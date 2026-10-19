#!/usr/bin/env python3
"""Validate against a separately authored, frozen raw-SMF auditor, not compiler helpers.

Full decoded media and event streams are read only from ignored/local paths.
This script does not import compiler.py and never rewrites historical artifacts.
"""
import argparse
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


class Check:
    def __init__(self):
        self.count = 0

    def __call__(self, condition, message):
        self.count += 1
        if not condition:
            raise AssertionError(message)


def edge_counts(events, global_pitch=False):
    held = set()
    duplicate = unheld = 0
    for e in events:
        if e["kind"] == "patch":
            continue  # source MIDI edge diagnostic, not allocator/program-reset simulation
        key = e["midi"] if global_pitch else (e["channel"], e["midi"])
        if e["kind"] == "on":
            duplicate += key in held
            held.add(key)
        else:
            unheld += key not in held
            held.discard(key)
    return {"duplicate_on": duplicate, "unheld_off": unheld, "held_at_end": len(held)}


def validate(output, protocol_path, check):
    protocol = load(protocol_path)
    for name, rec in protocol["inputs"].items():
        check(digest(rec["path"]) == rec["sha256"], "Frozen input digest: " + name)
    before = load(output / "implementation-before-export.json")
    check(before["protocol"]["sha256"] == digest(protocol_path), "Export protocol binding")
    for rec in before["implementation"]:
        check(digest(rec["path"]) == rec["sha256"], "Code changed after export: " + rec["path"])
    export = load(output / "export-receipt.json")
    for rec in export["outputs"]:
        check(digest(rec["path"]) == rec["sha256"], "Export changed: " + rec["path"])
    audit_path = protocol["inputs"]["old_auditor"]["path"]
    spec = importlib.util.spec_from_file_location("frozen_independent_smf_auditor", audit_path)
    auditor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(auditor)
    raw_path = protocol["inputs"]["raw_midi"]["path"]
    raw_bytes = Path(raw_path).read_bytes()
    decoded = auditor.decode(raw_path)  # independent raw-byte parse, not retained JSON alone
    old_events = load(protocol["inputs"]["old_decoded_events"]["path"])
    check(decoded["events"] == old_events, "Independent reparse differs from frozen auditor output")
    check(decoded["notes"] == load(protocol["inputs"]["old_decoded_notes"]["path"]), "Old decoded note identity")
    public_audit = load(protocol["inputs"]["published_audit"]["path"])
    for m, old in zip(protocol["maps"], public_audit["protocol"]["maps"]):
        check(all(m[k] == old[k] for k in ("id", "offset_seconds", "scale")), "Historical map coefficient changed")
    check(len(protocol["maps"]) == len(public_audit["protocol"]["maps"]) == 4, "Four maps")
    check(protocol["scenarios"] == ["ascending_track", "descending_track"], "Both scenarios declared")
    source = load(output / "source-events.json")
    check((source["format"], source["ppq"], source["track_count"]) == (1, 384, 3), "SMF header")
    check(len(source["events"]) == len(old_events) == 3576, "Every raw event retained")
    by_id = {e["id"]: e for e in old_events}
    for e in source["events"]:
        expected = by_id[e["id"]]
        for key, value in e.items():
            check(expected[key] == value, "Raw identity mismatch " + e["id"] + " " + key)
        # Verify the raw byte span/status independently of the compiler ledger.
        start, end = e["file_byte_start"], e["file_byte_end_exclusive"]
        check(start < end <= len(raw_bytes), "Raw span bounds")
        check(raw_bytes[e["status_byte_offset"]] == e["status"] if e["explicit_status"]
              else raw_bytes[e["status_byte_offset"]] < 128, "Raw explicit/running status byte")
        if e["kind"] == "channel":
            check(list(raw_bytes[end - len(e["data"]):end]) == e["data"], "Raw channel payload")
    # Existing note parser agreement is checked independently of either new file.
    retained = load(protocol["inputs"]["notes"]["path"])["notes"]
    fields = ("start", "end", "gate", "midi", "channel", "velocity", "track", "tick")
    check(len(retained) == len(decoded["notes"]) == 1779, "Retained note count")
    for raw_note, prior_note in zip(decoded["notes"], retained):
        check(all(raw_note[k] == prior_note[k] for k in fields), "Original note parser agreement")
    accepted = [n for n in decoded["notes"] if 36 <= n["midi"] <= 96]
    excluded = [n for n in decoded["notes"] if not 36 <= n["midi"] <= 96]
    check(len(accepted) == 1761 and len(excluded) == 18, "Mode00 pitch range count")
    check(Counter(n["midi"] for n in excluded) == {29: 2, 34: 13, 35: 3}, "Low-note exclusion distribution")
    accepted_ids = {n[k] for n in accepted for k in ("on_event", "off_event")}
    excluded_ids = {n[k] for n in excluded for k in ("on_event", "off_event")}
    notes = [e for e in old_events if e["id"] in accepted_ids]
    adjacent = auditor.adjacent(accepted, False)
    contiguous = [a for a in adjacent if a["raw_gap_ticks"] == 0]
    check(len(contiguous) == 193, "193 same-channel contiguous retriggers")
    check(not any(a["raw_gap_ticks"] < 0 for a in adjacent), "No same-channel source overlap")
    for pair in contiguous:
        off, on = (by_id[pair[k]] for k in ("previous_off_event", "next_on_event"))
        check(off["track"] == on["track"] and off["ordinal"] < on["ordinal"], "Authoritative raw OFF-before-ON")
    genuine = [n for n in accepted if n["midi"] == 62 and n["tick"] == 40704]
    check(sorted((n["channel"], n["off_tick"]) for n in genuine) == [(0, 41184), (1, 40896)], "Genuine cross-channel MIDI62 overlap")
    bank = load(protocol["inputs"]["bank"]["path"])
    payloads = {v["number"]: bytes(v["raw_data"]).hex() for v in bank["voices"]}
    timeline = load(protocol["inputs"]["timeline"]["path"])["intervals"]
    check(len(timeline) == 100, "100 independently inferred program entries")
    exact_times = {e["tick"]: Fraction(e["seconds_exact"]) for e in old_events}
    results = []
    for m in protocol["maps"]:
        expected_frames = {tick: round(48000 * (Fraction(m["offset_seconds"]) + Fraction(m["scale"]) * sec))
                           for tick, sec in exact_times.items()}
        for scenario in protocol["scenarios"]:
            directory = output / m["id"] / scenario
            compiled = load(directory / "events.json")
            rows = compiled["events"]
            check(compiled["tick_frames"] == {str(k): v for k, v in expected_frames.items()}, "One independently computed frame per source tick")
            check(compiled["tick_seconds_exact"] == {str(k): str(v) for k, v in exact_times.items()}, "Exact rational tempos")
            check(set(compiled["excluded_source_ids"]) == excluded_ids, "Both edges of every excluded note")
            check(len(rows) == 3622, "3522 retained note edges plus100 inferred patches")
            direction = 1 if scenario == "ascending_track" else -1
            expected = []
            for e in notes:
                expected.append((expected_frames[e["tick"]], 1, e["tick"], direction * e["track"], e["ordinal"], e))
            for i, p in enumerate(timeline):
                expected.append((round((m["offset_seconds"] + m["scale"] * p["midi_start_seconds"]) * 48000), 0, i, 0, 0, p))
            expected.sort(key=lambda item: item[:5])
            commands, positions = [], {}
            for position, (row, reference) in enumerate(zip(rows, expected)):
                frame, category, _, _, _, source_event = reference
                check(row["frame"] == frame, "Independent expected frame")
                if category == 0:
                    check(row["kind"] == "patch" and row["patch"] == source_event["patch"] and row["inferred"], "Explicit patch-first timeline")
                    command = "patch " + payloads[source_event["patch"]]
                else:
                    e = source_event
                    kind = "on" if e["command"] == 9 and e["data"][1] else "off"
                    check(row["source_id"] == e["id"], "Exact ordered source identity (no chord sort)")
                    check((row["kind"], row["tick"], row["track"], row["ordinal"], row["channel"], row["midi"], row["velocity"], row["raw_status"])
                          == (kind, e["tick"], e["track"], e["ordinal"], e["channel"], e["data"][0], e["data"][1], e["status"]), "Raw source event properties")
                    positions[e["id"]] = (position, frame)
                    command = f"on {e['data'][0]} {e['data'][1]} {e['channel']}" if kind == "on" else f"off {e['data'][0]} {e['channel']}"
                commands.append(f"{frame} {command}\n")
            check((directory / "events.txt").read_bytes() == "".join(commands).encode(), "Text fixture bytes independently reconstructed")
            for pair in contiguous:
                off, on = (positions[pair[k]] for k in ("previous_off_event", "next_on_event"))
                check(off[1] == on[1] and off[0] < on[0], "Mapped contiguous OFF-before-ON retained")
            per_channel, global_pitch = edge_counts(rows), edge_counts(rows, True)
            check(per_channel == {"duplicate_on": 0, "unheld_off": 0, "held_at_end": 0}, "No artificial per-channel edge collision")
            check(global_pitch == {"duplicate_on": 1 if scenario == "ascending_track" else 2,
                                   "unheld_off": 1 if scenario == "ascending_track" else 2, "held_at_end": 0}, "Declared merge scenario global edges")
            boundary = [e for e in rows if e.get("tick") == 58368 and e.get("midi") == 51]
            check([e["kind"] for e in boundary] == (["off", "on"] if direction == 1 else ["on", "off"]), "Conditional cross-track MIDI51 boundary")
            results.append({"map": m["id"], "scenario": scenario, "event_count": len(rows),
                            "contiguous_retriggers_preserved": len(contiguous),
                            "within_track_order_inversions": 0, "per_channel_edges": per_channel,
                            "global_pitch_edges": global_pitch, "sha256": digest(directory / "events.txt")})
    for name, rec in protocol["inputs"].items():
        check(digest(rec["path"]) == rec["sha256"], "Historical input changed after validation: " + name)
    return {"source_messages": len(old_events), "source_notes": len(decoded["notes"]),
            "accepted_notes": len(accepted), "excluded_notes": len(excluded), "maps": results,
            "genuine_cross_channel_overlap": {"midi": 62, "on_tick": 40704, "channel0_off": 41184, "channel1_off": 40896},
            "source_duration_exact": decoded["duration_exact"], "source_duration_seconds": float(Fraction(decoded["duration_exact"])),
            "historical_inputs_unchanged": True, "audio_rendered": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, default=HERE / "freeze.json")
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    check = Check()
    # Refuse overwrite before doing work, retain even a failed validation attempt.
    with args.receipt.open("x") as receipt:
        try:
            result = validate(args.output, args.protocol, check)
            result.update(passed=True, checks=check.count, validator_sha256=digest(__file__), protocol_sha256=digest(args.protocol))
        except Exception as exc:
            result = dict(passed=False, checks=check.count, failure_type=type(exc).__name__, failure=str(exc), validator_sha256=digest(__file__))
            json.dump(result, receipt, indent=2)
            receipt.write("\n")
            raise
        json.dump(result, receipt, indent=2)
        receipt.write("\n")
    print(json.dumps({"passed": True, "checks": check.count, "scenarios": len(result["maps"])}))


if __name__ == "__main__":
    main()
