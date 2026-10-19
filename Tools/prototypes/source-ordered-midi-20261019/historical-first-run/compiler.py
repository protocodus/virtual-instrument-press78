#!/usr/bin/env python3
"""Conditional SMF-source-order research fixture compiler; never a wire capture."""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCENARIOS = ("ascending_track", "descending_track")


class InvalidMidi(ValueError):
    pass


class Reader:
    def __init__(self, data, start=0, end=None):
        self.data, self.pos = data, start
        self.end = len(data) if end is None else end

    def take(self, length):
        if length < 0 or self.pos + length > self.end:
            raise InvalidMidi("Truncated SMF field or chunk")
        result = self.data[self.pos:self.pos + length]
        self.pos += length
        return result

    def vlq(self):
        result = 0
        for _ in range(4):
            byte = self.take(1)[0]
            result = result * 128 + (byte & 127)
            if byte < 128:
                return result
        raise InvalidMidi("VLQ exceeds four bytes")


def parse_smf(data):
    """Retain byte provenance and ordinal of every message, including meta."""
    r = Reader(data)
    if r.take(4) != b"MThd":
        raise InvalidMidi("Missing MThd")
    size = int.from_bytes(r.take(4), "big")
    if size < 6:
        raise InvalidMidi("Short MThd")
    fmt, count, ppq = struct.unpack(">HHH", r.take(6))
    r.take(size - 6)
    if fmt not in (0, 1) or count == 0 or (fmt == 0 and count != 1):
        raise InvalidMidi("Only format 0/1 with valid track count is supported")
    if ppq == 0 or ppq & 0x8000:
        raise InvalidMidi("Only nonzero PPQN division is supported")
    events = []
    for track in range(count):
        if r.take(4) != b"MTrk":
            raise InvalidMidi("Missing MTrk")
        size = int.from_bytes(r.take(4), "big")
        if r.pos + size > r.end:
            raise InvalidMidi("Truncated track")
        t = Reader(data, r.pos, r.pos + size)
        r.pos += size
        tick, ordinal, running, ended = 0, 0, None, False
        while t.pos < t.end:
            start = t.pos
            delta = t.vlq()
            tick += delta
            status_offset = t.pos
            first = t.take(1)[0]
            explicit = first >= 128
            if explicit:
                status = first
            else:
                if running is None:
                    raise InvalidMidi("Running status without channel status")
                status = running
                t.pos -= 1
            e = dict(id=f"t{track}e{ordinal}", track=track, ordinal=ordinal,
                     tick=tick, delta=delta, status=status,
                     file_byte_start=start, status_byte_offset=status_offset,
                     explicit_status=explicit)
            if 0x80 <= status <= 0xEF:
                running = status
                command = status >> 4
                payload = t.take(1 if command in (12, 13) else 2)
                if any(byte >= 128 for byte in payload):
                    raise InvalidMidi("Status byte in channel payload")
                e.update(kind="channel", channel=status & 15,
                         command=command, data=list(payload))
            elif status == 0xFF:
                running = None
                meta = t.take(1)[0]
                payload = t.take(t.vlq())
                e.update(kind="meta", meta=meta, data=list(payload))
                if meta == 0x51:
                    if len(payload) != 3 or int.from_bytes(payload, "big") == 0:
                        raise InvalidMidi("Invalid tempo")
                    e["tempo"] = int.from_bytes(payload, "big")
                if meta == 0x2F:
                    if payload or t.pos != t.end:
                        raise InvalidMidi("EOT must be empty and terminate its track")
                    ended = True
            elif status in (0xF0, 0xF7):
                running = None
                e.update(kind="sysex", data=list(t.take(t.vlq())))
            else:
                raise InvalidMidi("Unsupported system status in SMF")
            e["file_byte_end_exclusive"] = t.pos
            events.append(e)
            ordinal += 1
        if not ended:
            raise InvalidMidi("Track lacks final EOT")
    if r.pos != r.end:
        raise InvalidMidi("Trailing bytes after declared tracks")
    return {"format": fmt, "ppq": ppq, "track_count": count, "events": events}


def exact_tick_times(parsed):
    """One rational timestamp per unique tick; conflicting tempo ties fail closed."""
    tempos = {}
    for e in parsed["events"]:
        if "tempo" in e:
            if e["tick"] in tempos and tempos[e["tick"]] != e["tempo"]:
                raise InvalidMidi("Conflicting simultaneous tempos have no declared authority")
            tempos[e["tick"]] = e["tempo"]
    result, previous, tempo, seconds = {}, 0, 500000, Fraction(0)
    for tick in sorted({e["tick"] for e in parsed["events"]}):
        seconds += Fraction((tick - previous) * tempo, parsed["ppq"] * 1000000)
        result[tick] = seconds
        previous, tempo = tick, tempos.get(tick, tempo)
    return result


def nearest_even(value):
    """Integer-only rounding, including negative ties."""
    quotient, remainder = divmod(value.numerator, value.denominator)
    twice = 2 * remainder
    return quotient + int(twice > value.denominator or
                          (twice == value.denominator and quotient % 2 != 0))


def compile_events(parsed, timing_map, timeline, scenario, rate=48000, low=36, high=96):
    if scenario not in SCENARIOS:
        raise ValueError("An explicit supported intertrack scenario is required")
    if rate <= 0 or not 0 <= low <= high <= 127:
        raise ValueError("Invalid sample rate or note range")
    offset = Fraction(timing_map["offset_seconds"])
    scale = Fraction(timing_map["scale"])
    if scale <= 0:
        raise ValueError("Timing scale must be positive")
    times = exact_tick_times(parsed)
    tick_frames = {tick: nearest_even(rate * (offset + scale * seconds))
                   for tick, seconds in times.items()}
    rows, excluded = [], []
    for e in parsed["events"]:
        if e["kind"] == "meta":
            continue
        if e["kind"] != "channel" or e["command"] not in (8, 9):
            raise InvalidMidi("Non-note MIDI would require an additional event contract")
        note, velocity = e["data"]
        if not low <= note <= high:
            excluded.append(e["id"])
            continue
        rows.append(dict(frame=tick_frames[e["tick"]],
                         kind="on" if e["command"] == 9 and velocity else "off",
                         source_id=e["id"], tick=e["tick"], track=e["track"],
                         ordinal=e["ordinal"], channel=e["channel"], midi=note,
                         velocity=velocity, raw_status=e["status"],
                         seconds_exact=str(times[e["tick"]])))
    for ordinal, entry in enumerate(timeline):
        # Intentionally preserve historical inferred-program timing. These are
        # not raw SMF messages and do not claim recovered tick or wire times.
        frame = round((timing_map["offset_seconds"] + timing_map["scale"] *
                       entry["midi_start_seconds"]) * rate)
        rows.append(dict(frame=frame, kind="patch", timeline_ordinal=ordinal,
                         patch=entry["patch"], inferred=True))
    if any(e["frame"] < 0 for e in rows):
        raise ValueError("Negative frames require an explicitly different protocol")
    direction = 1 if scenario == "ascending_track" else -1
    rows.sort(key=lambda e: (e["frame"], 0, e["timeline_ordinal"]) if e["kind"] == "patch"
              else (e["frame"], 1, e["tick"], direction * e["track"], e["ordinal"]))
    return {"scenario": scenario, "map_id": timing_map.get("id", "synthetic"),
            "sample_rate": rate, "events": rows, "excluded_source_ids": excluded,
            "tick_frames": {str(k): v for k, v in tick_frames.items()},
            "tick_seconds_exact": {str(k): str(v) for k, v in times.items()}}


def record(path):
    path = Path(path)
    return dict(path=str(path.resolve()), bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def verify_inputs(protocol):
    for name, expected in protocol["inputs"].items():
        actual = record(expected["path"])
        if actual["sha256"] != expected["sha256"] or actual["bytes"] != expected["bytes"]:
            raise ValueError("Frozen input changed: " + name)
    for m in protocol["maps"]:
        if str(Fraction(m["offset_seconds"])) != m["offset_exact_binary64"] or str(Fraction(m["scale"])) != m["scale_exact_binary64"]:
            raise ValueError("Frozen coefficient representation changed")


def write_json(path, value):
    with Path(path).open("x") as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write("\n")


def export(protocol_path, output):
    protocol_path, output = Path(protocol_path), Path(output).resolve()
    allowed = (ROOT / "build/source-ordered-midi-20261019").resolve()
    if allowed not in output.parents:
        raise ValueError("Full fixtures must stay under ignored build/source-ordered-midi-20261019/<new-run>")
    protocol = json.loads(protocol_path.read_text())
    verify_inputs(protocol)
    output.mkdir(parents=True, exist_ok=False)
    # This receipt exists before any source decoding or full-fixture export.
    receipt = {"protocol": record(protocol_path), "implementation": [record(p) for p in sorted(HERE.glob("*.py"))],
               "stage": "Code and protocol bound before export", "outputs": []}
    write_json(output / "implementation-before-export.json", receipt)
    try:
        parsed = parse_smf(Path(protocol["inputs"]["raw_midi"]["path"]).read_bytes())
        timeline = json.loads(Path(protocol["inputs"]["timeline"]["path"]).read_text())["intervals"]
        bank = json.loads(Path(protocol["inputs"]["bank"]["path"]).read_text())
        payloads = {v["number"]: bytes(v["raw_data"]).hex() for v in bank["voices"]}
        write_json(output / "source-events.json", parsed)
        for m in protocol["maps"]:
            for scenario in protocol["scenarios"]:
                directory = output / m["id"] / scenario
                directory.mkdir(parents=True)
                compiled = compile_events(parsed, m, timeline, scenario, protocol["sample_rate"], *protocol["mode00_pitch_range"])
                write_json(directory / "events.json", compiled)
                with (directory / "events.txt").open("x") as handle:
                    for e in compiled["events"]:
                        if e["kind"] == "patch":
                            command = "patch " + payloads[e["patch"]]
                        elif e["kind"] == "on":
                            command = f"on {e['midi']} {e['velocity']} {e['channel']}"
                        else:
                            command = f"off {e['midi']} {e['channel']}"
                        handle.write(f"{e['frame']} {command}\n")
                receipt["outputs"].extend(record(directory / name) for name in ("events.json", "events.txt"))
        verify_inputs(protocol)
        write_json(output / "export-receipt.json", receipt | {"passed": True, "frozen_inputs_unchanged": True})
    except Exception as exc:
        write_json(output / "failure.json", {"passed": False, "type": type(exc).__name__, "message": str(exc)})
        raise
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=HERE / "freeze.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = export(args.protocol, args.output)
    print(json.dumps({"output": str(args.output), "fixture_files": len(result["outputs"])}))
