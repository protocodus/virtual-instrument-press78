"""Public synthetic fixtures only: no retained musical work or factory payload."""
from fractions import Fraction
import struct
import tempfile
from pathlib import Path
import unittest

import compiler as c


def vlq(value):
    result = [value & 127]
    while value >> 7:
        value >>= 7
        result.insert(0, (value & 127) | 128)
    return bytes(result)


def track(*messages):
    return b"".join(vlq(delta) + message for delta, message in messages) + b"\0\xff\x2f\0"


def smf(*tracks, ppq=384, fmt=None):
    fmt = (0 if len(tracks) == 1 else 1) if fmt is None else fmt
    return b"MThd" + struct.pack(">IHHH", 6, fmt, len(tracks), ppq) + b"".join(
        b"MTrk" + struct.pack(">I", len(t)) + t for t in tracks)


IDENTITY = {"id": "synthetic", "offset_seconds": 0.0, "scale": 1.0}


class CompilerContracts(unittest.TestCase):
    def test_running_status_and_velocity_zero_keep_original_bytes(self):
        data = smf(track((0, b"\x90\x48\x7f"), (128, b"\x48\0")))
        parsed = c.parse_smf(data)
        a, b = parsed["events"][:2]
        self.assertEqual((a["ordinal"], b["ordinal"], b["tick"]), (0, 1, 128))
        self.assertFalse(b["explicit_status"])
        self.assertEqual(data[b["file_byte_start"]:b["file_byte_end_exclusive"]], b"\x81\0\x48\0")
        rows = c.compile_events(parsed, IDENTITY, [], "ascending_track")["events"]
        self.assertEqual([e["kind"] for e in rows], ["on", "off"])
        self.assertEqual(rows[1]["raw_status"], 0x90)

    def test_tick_end_not_onset_plus_rounded_gate(self):
        parsed = c.parse_smf(smf(track((1, b"\x90\x48\x7f"), (1, b"\x80\x48\0"),
                                             (0, b"\x90\x48\x7f"), (1, b"\x80\x48\0")), ppq=3))
        result = c.compile_events(parsed, IDENTITY, [], "ascending_track", rate=3)
        self.assertEqual([e["frame"] for e in result["events"]], [0, 1, 1, 2])
        self.assertEqual([e["kind"] for e in result["events"]], ["on", "off", "on", "off"])
        self.assertEqual(round(Fraction(1, 2)) + round(Fraction(1, 2)), 0)  # historical gate pitfall

    def test_chords_keep_ordinal_not_pitch_order(self):
        parsed = c.parse_smf(smf(track((0, b"\x90\x54\x7f"), (0, b"\x90\x3c\x7f"),
                                             (0, b"\x90\x48\x7f"))))
        for scenario in c.SCENARIOS:
            result = c.compile_events(parsed, IDENTITY, [], scenario)
            self.assertEqual([e["midi"] for e in result["events"]], [84, 60, 72])

    def test_same_track_on_before_off_is_not_globally_rewritten(self):
        parsed = c.parse_smf(smf(track((0, b"\x90\x48\x7f"), (0, b"\x80\x48\0"))))
        self.assertEqual([e["kind"] for e in c.compile_events(parsed, IDENTITY, [], "descending_track")["events"]], ["on", "off"])

    def test_track_merge_is_an_explicit_scenario(self):
        parsed = c.parse_smf(smf(track((0, b"\x90\x48\x7f")), track((0, b"\x91\x3c\x7f"))))
        asc = c.compile_events(parsed, IDENTITY, [], "ascending_track")["events"]
        desc = c.compile_events(parsed, IDENTITY, [], "descending_track")["events"]
        self.assertEqual([e["track"] for e in asc], [0, 1])
        self.assertEqual([e["track"] for e in desc], [1, 0])
        with self.assertRaises(ValueError):
            c.compile_events(parsed, IDENTITY, [], "wire_order")

    def test_distinct_ticks_collapsed_to_one_frame_keep_tick_order(self):
        parsed = c.parse_smf(smf(track((2, b"\x90\x48\x7f")), track((1, b"\x91\x3c\x7f")), ppq=10))
        for scenario in c.SCENARIOS:
            rows = c.compile_events(parsed, IDENTITY, [], scenario, rate=1)["events"]
            self.assertEqual([(e["frame"], e["tick"]) for e in rows], [(0, 1), (0, 2)])

    def test_exact_tempo_changes_with_duplicate_tempo(self):
        tempo = b"\xff\x51\x03\x0f\x42\x40"  # 1,000,000 us
        a = track((1, b"\x90\x48\x7f"), (2, tempo), (3, b"\x80\x48\0"))
        b = track((3, tempo))
        times = c.exact_tick_times(c.parse_smf(smf(a, b, ppq=3)))
        self.assertEqual(times[1], Fraction(1, 6))
        self.assertEqual(times[3], Fraction(1, 2))
        self.assertEqual(times[6], Fraction(3, 2))

    def test_conflicting_tempos_fail_instead_of_choosing_track(self):
        a = track((0, b"\xff\x51\3\x07\xa1\x20"))
        b = track((0, b"\xff\x51\3\x0f\x42\x40"))
        with self.assertRaisesRegex(c.InvalidMidi, "Conflicting"):
            c.exact_tick_times(c.parse_smf(smf(a, b)))

    def test_binary64_coefficients_are_preserved(self):
        parsed = c.parse_smf(smf(track((1, b"\x90\x48\x7f")), ppq=7))
        m = {"offset_seconds": 0.1, "scale": 0.9998070138348876}
        result = c.compile_events(parsed, m, [], "ascending_track", rate=48000)
        expected = round(48000 * (Fraction(0.1) + Fraction(m["scale"]) / 14))
        self.assertEqual(result["tick_frames"]["1"], expected)
        self.assertNotEqual(Fraction(0.1), Fraction("0.1"))

    def test_ties_to_even_positive_and_negative(self):
        values = [Fraction(n, 2) for n in range(-11, 12)]
        self.assertEqual([c.nearest_even(x) for x in values], [round(x) for x in values])

    def test_patch_first_is_explicit_and_timeline_order_survives(self):
        parsed = c.parse_smf(smf(track((0, b"\x90\x48\x7f"))))
        timeline = [{"patch": 9, "midi_start_seconds": 0.0}, {"patch": 2, "midi_start_seconds": 0.0}]
        rows = c.compile_events(parsed, IDENTITY, timeline, "ascending_track")["events"]
        self.assertEqual([e["kind"] for e in rows], ["patch", "patch", "on"])
        self.assertEqual([e["patch"] for e in rows[:2]], [9, 2])

    def test_range_filter_removes_both_edges_and_keeps_boundaries(self):
        notes = (35, 36, 96, 97)
        messages = [(0, bytes((0x90, n, 127))) for n in notes] + [(1, bytes((0x80, n, 0))) for n in notes]
        result = c.compile_events(c.parse_smf(smf(track(*messages))), IDENTITY, [], "ascending_track")
        self.assertEqual([e["midi"] for e in result["events"]], [36, 96, 36, 96])
        self.assertEqual(len(result["excluded_source_ids"]), 4)

    def test_cross_channel_same_pitch_is_retained(self):
        parsed = c.parse_smf(smf(track((0, b"\x90\x3e\x7f"), (2, b"\x80\x3e\0")),
                                track((0, b"\x91\x3e\x7f"), (1, b"\x81\x3e\0"))))
        rows = c.compile_events(parsed, IDENTITY, [], "ascending_track")["events"]
        self.assertEqual([(e["kind"], e["channel"]) for e in rows], [("on", 0), ("on", 1), ("off", 1), ("off", 0)])

    def test_malformed_inputs_fail_closed(self):
        valid = smf(track((0, b"\x90\x48\x7f")))
        invalid = [valid[:-1], valid + b"extra", smf(b"\0\x90\x48\x7f"),
                   smf(track((0, b"\x48\x7f"))), smf(track((0, b"\x90\x80\x7f"))),
                   smf(track((0, b"\xff\x51\3\0\0\0"))),
                   smf(track((0, b"\xff\x2f\0"))),
                   smf(b"\x81\x81\x81\x81\0\x90\x48\x7f\0\xff\x2f\0"),
                   smf(track(), ppq=0), smf(track(), ppq=0xE728), smf(track(), fmt=2)]
        for data in invalid:
            with self.subTest(data=data.hex()), self.assertRaises(c.InvalidMidi):
                c.parse_smf(data)

    def test_nonnote_midi_is_not_silently_discarded(self):
        for message in (b"\xb0\x40\x7f", b"\xc0\x01", b"\xf0\x01\xf7"):
            with self.subTest(message=message), self.assertRaisesRegex(c.InvalidMidi, "Non-note"):
                c.compile_events(c.parse_smf(smf(track((0, message)))), IDENTITY, [], "ascending_track")

    def test_high_bit_meta_types_are_invalid(self):
        for meta_type in range(128, 256):
            with self.subTest(meta_type=meta_type), self.assertRaisesRegex(c.InvalidMidi, "Meta event type"):
                c.parse_smf(smf(track((0, bytes((0xFF, meta_type, 0))))))

    def test_opaque_meta_payloads_retain_eight_bit_bytes(self):
        for meta_type in (0x7E, 0x7F):
            parsed = c.parse_smf(smf(track((0, bytes((0xFF, meta_type, 3, 1, 0xFF, 0x80))),
                                           (0, b"\x90\x48\x7f"))))
            self.assertEqual(parsed["events"][0]["data"], [1, 255, 128])
            rows = c.compile_events(parsed, IDENTITY, [], "ascending_track")["events"]
            self.assertEqual([(e["kind"], e["midi"]) for e in rows], [("on", 72)])

    def test_negative_frame_and_nonpositive_scale_are_rejected(self):
        parsed = c.parse_smf(smf(track((0, b"\x90\x48\x7f"))))
        for timing in ({"offset_seconds": -1, "scale": 1}, {"offset_seconds": 1, "scale": 0}):
            with self.assertRaises(ValueError):
                c.compile_events(parsed, timing, [], "ascending_track")

    def test_no_overwrite_or_outside_build_export(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "receipt.json"
            c.write_json(file, {"first": True})
            with self.assertRaises(FileExistsError):
                c.write_json(file, {"second": True})
            with self.assertRaisesRegex(ValueError, "ignored build"):
                c.export(HERE / "freeze.json", Path(temp) / "fixtures")


HERE = Path(__file__).resolve().parent
if __name__ == "__main__":
    unittest.main(verbosity=2)
