#!/usr/bin/env python3
"""Export new, metadata-only research fixtures from audited SMF event records.

This does not decode audio, send MIDI, run a synthesizer, or edit old fixtures.
The local decoded-events research artifact is required; no original recording or
MIDI file is copied into the output. Freeze source/input hashes before exporting:

  python3 Tools/export_midi_reference_events.py freeze --out build/midi-reference-new
  python3 Tools/export_midi_reference_events.py run --out build/midi-reference-new

The event text retains raw MIDI channel IDs, not independent MIDI/CV owners. A
future renderer must separately declare how enabled MIDI channels reach Mode00.
Mapping endpoints once removes the known separate-gate-rounding artifact; it
does not recover actual wire timing or establish a hardware-fidelity improvement.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
SR = 48000
RAW_SHA = "7ab6f4551b8116590d52dd0566c3f5a7fad89097eb1b64ddf97b60fba47167cf"
MAP_IDS = ("unchanged", "old_scale_median_offset",
           "nominal_scale_median_intercept", "equal_patch_robust_affine")
SCHEMA = "raw-midi-reference-event-export-v1"


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def record(path):
    path = Path(path).resolve()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}


def verify(item):
    path = Path(item["path"])
    if not path.is_file() or sha(path) != item["sha256"]:
        raise ValueError("Input hash mismatch: " + str(path))
    if "bytes" in item and path.stat().st_size != item["bytes"]:
        raise ValueError("Input size mismatch: " + str(path))


def write_new(path, value):
    path = Path(path)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def output_path(path):
    path = Path(path).resolve()
    build = (ROOT / "build").resolve()
    if path == build or not path.is_relative_to(build):
        raise ValueError("Research output must be a new directory under this repo's build/")
    return path


def canonical(event):
    return event["tick"], event["track"], event["ordinal"]


def accepted_messages(events, ppq):
    """Verify the bound decoder's exact times and retain original note events."""
    if events != sorted(events, key=canonical):
        raise ValueError("Decoded events are not in tick/track/ordinal order")
    if len({e["id"] for e in events}) != len(events):
        raise ValueError("Duplicate decoded event ID")
    previous_tick, tempo, seconds = 0, 500000, Fraction(0)
    ordinal = defaultdict(int)
    selected, excluded = [], []
    for e in events:
        track = e["track"]
        if e["ordinal"] != ordinal[track] or e["id"] != f"t{track}e{ordinal[track]}":
            raise ValueError("Invalid within-track ordinal")
        ordinal[track] += 1
        seconds += Fraction((e["tick"] - previous_tick) * tempo, ppq * 1_000_000)
        previous_tick = e["tick"]
        if seconds != Fraction(e["seconds_exact"]):
            raise ValueError("Decoded exact tempo time disagrees with event tick")
        if "tempo" in e:
            tempo = e["tempo"]
        if e["kind"] == "meta":
            continue
        if e["kind"] != "channel" or e["command"] not in (8, 9):
            raise ValueError("Unexpected non-note source message")
        pitch, velocity = e["data"]
        if not (0 <= pitch <= 127 and 0 <= velocity <= 127 and e["channel"] in (0, 1)):
            raise ValueError("Invalid source note payload")
        kind = "on" if e["command"] == 9 and velocity else "off"
        row = {"id": e["id"], "tick": e["tick"], "track": track,
               "ordinal": e["ordinal"], "kind": kind, "midi": pitch,
               "velocity": velocity, "channel": e["channel"],
               "seconds_exact": str(seconds)}
        (selected if 36 <= pitch <= 96 else excluded).append(row)
    return selected, excluded


def pair_messages(messages):
    pending = defaultdict(deque)
    notes = []
    for index, e in enumerate(messages):
        key = e["channel"], e["midi"]
        if e["kind"] == "on":
            if pending[key]:
                raise ValueError("Raw same-channel held duplicate is not the audited input")
            pending[key].append((index, e))
        else:
            if not pending[key]:
                raise ValueError("Raw unpaired off")
            on_index, on = pending[key].popleft()
            if e["tick"] <= on["tick"]:
                raise ValueError("Raw zero/negative note gate")
            notes.append({"on": on, "off": e, "on_index": on_index, "off_index": index})
    if any(pending.values()):
        raise ValueError("Raw unreleased key")
    return notes


def edge_check(messages, global_midi):
    held = set()
    duplicates, unheld_offs = [], []
    for e in messages:
        key = e["midi"] if global_midi else (e["channel"], e["midi"])
        if e["kind"] == "on":
            if key in held:
                duplicates.append(e["id"])
            held.add(key)
        else:
            if key not in held:
                unheld_offs.append(e["id"])
            held.discard(key)
    return {"duplicate_on_ids": duplicates, "unheld_off_ids": unheld_offs,
            "held_at_end": sorted(held)}


def contiguous_boundaries(notes):
    groups = defaultdict(list)
    for note in notes:
        groups[note["on"]["channel"], note["on"]["midi"]].append(note)
    boundaries = []
    for group in groups.values():
        group.sort(key=lambda n: canonical(n["on"]))
        for previous, following in zip(group, group[1:]):
            if following["on"]["tick"] == previous["off"]["tick"]:
                if (previous["off"]["track"] != following["on"]["track"] or
                        previous["off_index"] >= following["on_index"]):
                    raise ValueError("Audited contiguous source order changed")
                boundaries.append({"off_id": previous["off"]["id"],
                                   "on_id": following["on"]["id"],
                                   "tick": previous["off"]["tick"]})
    return boundaries


def parse_old_events(path):
    patches, ons = [], Counter()
    previous_frame = -1
    for index, line in enumerate(Path(path).read_text().splitlines()):
        fields = line.split()
        frame, kind = int(fields[0]), fields[1]
        if frame < previous_frame:
            raise ValueError("Old fixture is not frame sorted")
        previous_frame = frame
        if kind == "patch" and len(fields) == 3:
            if len(bytes.fromhex(fields[2])) != 33:
                raise ValueError("Invalid old patch row")
            patches.append({"frame": frame, "payload": fields[2], "old_line_index": index})
        elif kind == "on" and len(fields) == 5:
            ons[(frame, *map(int, fields[2:]))] += 1
        elif kind == "off" and len(fields) == 4:
            pass
        else:
            raise ValueError("Invalid old fixture row")
    if len(patches) != 100 or sum(ons.values()) != 1761:
        raise ValueError("Unexpected old fixture note/program count")
    return patches, ons


def mapped_rows(messages, patches, mapping):
    # Each source tick has exactly one frame. No note gate is rounded separately.
    exact_times = {e["tick"]: Fraction(e["seconds_exact"]) for e in messages}
    frames = {tick: round(SR * (mapping["offset_seconds"] +
                               mapping["scale"] * float(seconds)))
              for tick, seconds in exact_times.items()}
    rows = []
    for sequence, patch in enumerate(patches):
        rows.append({"frame": patch["frame"], "class": 0, "sequence": sequence,
                     "kind": "patch", "payload": patch["payload"],
                     "old_line_index": patch["old_line_index"]})
    for sequence, e in enumerate(messages):
        rows.append({"frame": frames[e["tick"]], "class": 1,
                     "sequence": sequence, **e})
    rows.sort(key=lambda row: (row["frame"], row["class"], row["sequence"]))
    return rows, frames


def serialize(rows):
    text = []
    for row in rows:
        if row["kind"] == "patch":
            message = "patch " + row["payload"]
        elif row["kind"] == "on":
            message = f"on {row['midi']} {row['velocity']} {row['channel']}"
        else:
            message = f"off {row['midi']} {row['channel']}"
        text.append(f"{row['frame']} {message}\n")
    return "".join(text)


def freeze(args):
    out = output_path(args.out)
    if out.exists():
        raise ValueError("Refusing to reuse an existing research directory")
    ledger_path = args.ledger.resolve()
    ledger = read(ledger_path)
    if ledger["schema"] != "midi-event-order-audit-public-v1":
        raise ValueError("Wrong source provenance ledger")
    if ledger["source"]["raw_midi"]["sha256"] != RAW_SHA:
        raise ValueError("Wrong raw MIDI ancestry")
    inputs = {"source_ledger": record(ledger_path)}
    for key, source_key in (("decoded_events", "audit_decoded-events.json"),
                            ("decoder", "audit_audit.py")):
        inputs[key] = ledger["provenance"][source_key]
        verify(inputs[key])
    for mapping in ledger["protocol"]["maps"]:
        item = mapping["filtered_events"]
        verify(item)
        inputs["old_events_" + mapping["id"]] = record(item["path"])
    if tuple(m["id"] for m in ledger["protocol"]["maps"]) != MAP_IDS:
        raise ValueError("Wrong fixed timing-map set")
    snapshots = out / "snapshots"
    snapshots.mkdir(parents=True)
    shutil.copyfile(__file__, snapshots / "exporter.py")
    shutil.copyfile(inputs["decoder"]["path"], snapshots / "decoder.py")
    protocol = {"schema": SCHEMA, "status": "Frozen before new event exports",
                "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
                "tool": record(__file__), "snapshots": [record(p) for p in sorted(snapshots.iterdir())],
                "inputs": inputs, "raw_midi_ancestry": ledger["source"]["raw_midi"],
                "ppq": ledger["raw_header"]["ppq"], "sample_rate": SR,
                "maps": [{k: m[k] for k in ("id", "offset_seconds", "scale")}
                         for m in ledger["protocol"]["maps"]],
                "rules": {
                    "authority": "Audited raw decoded SMF events, not paired start-plus-gate notes.",
                    "canonical_merge": "tick, track index, within-track ordinal; intertrack wire order unmeasured.",
                    "time": "Reintegrate exact Fraction tempo times; one frame per tick: round(48000*(offset+scale*float(exact_seconds))). Python nearest/ties-to-even rounding.",
                    "filter": "Retain both on/off only for inclusive36..96, exactly existing Mode00 research source policy.",
                    "within_frame": "All inferred patch rows first, old patch order retained; then all note messages in raw canonical order, including mixed OFF/ON. No off-first category.",
                    "programs": "Copy100 inferred patch payloads and frame positions exactly from each old filtered fixture; program-first is an explicit unmeasured convention.",
                    "channel_field": "Raw MIDI channel ID, not a MIDI/CV ownership claim.",
                    "required": "1761on/1761off, identical old onset multiset+frames,193contiguous same-channel OFF-before-ON at one frame, no manufactured same-channel duplicate, raw canonical note order, genuine cross-channel62 overlap retained.",
                    "scope": "Metadata-only new research fixtures. No audio, fitting, runtime/default changes, original MIDI redistribution or proof of actual2017sender timing."}}
    write_new(out / "protocol-frozen.json", protocol)
    print(json.dumps({"status": "SOURCE FROZEN; no fresh events generated", "protocol": record(out / "protocol-frozen.json")}, indent=2))


def run(args):
    out = output_path(args.out)
    protocol = read(out / "protocol-frozen.json")
    if protocol["schema"] != SCHEMA or protocol["sample_rate"] != SR:
        raise ValueError("Wrong export protocol")
    verify(protocol["tool"])
    if sha(__file__) != protocol["tool"]["sha256"]:
        raise ValueError("Executing another exporter version")
    for item in list(protocol["inputs"].values()) + protocol["snapshots"]:
        verify(item)
    write_new(out / "started.json", {"started_at_utc": datetime.now(timezone.utc).isoformat(),
                                     "protocol": record(out / "protocol-frozen.json")})
    try:
        events = read(protocol["inputs"]["decoded_events"]["path"])
        messages, excluded = accepted_messages(events, protocol["ppq"])
        notes = pair_messages(messages)
        boundaries = contiguous_boundaries(notes)
        if Counter(e["kind"] for e in messages) != {"on": 1761, "off": 1761} or len(excluded) != 36 or len(boundaries) != 193:
            raise ValueError("Audited source counts changed")
        raw_global = edge_check(messages, True)
        if raw_global["duplicate_on_ids"] != ["t2e1029"] or raw_global["held_at_end"]:
            raise ValueError("Genuine cross-channel overlap changed")
        if any(edge_check(messages, False).values()):
            raise ValueError("Raw same-channel edge state is not clean")
        generated = []
        for mapping in protocol["maps"]:
            previous = protocol["inputs"]["old_events_" + mapping["id"]]
            patches, old_ons = parse_old_events(previous["path"])
            rows, frames = mapped_rows(messages, patches, mapping)
            note_rows = [row for row in rows if row["kind"] != "patch"]
            if [e["id"] for e in note_rows] != [e["id"] for e in messages]:
                raise ValueError("Canonical raw note order not preserved")
            ons = Counter((e["frame"], e["midi"], e["velocity"], e["channel"])
                          for e in note_rows if e["kind"] == "on")
            if ons != old_ons:
                raise ValueError("Old note-on times/multiset changed")
            positions = {e["id"]: index for index, e in enumerate(note_rows)}
            by_id = {e["id"]: e for e in note_rows}
            for boundary in boundaries:
                a, b = boundary["off_id"], boundary["on_id"]
                if by_id[a]["frame"] != by_id[b]["frame"] or positions[a] >= positions[b]:
                    raise ValueError("Contiguous OFF-before-ON boundary was manufactured into overlap")
            channel_state, global_state = edge_check(note_rows, False), edge_check(note_rows, True)
            if any(channel_state.values()) or global_state != raw_global:
                raise ValueError("Export changed raw received-key edge semantics")
            if [(row["frame"], row["payload"]) for row in rows if row["kind"] == "patch"] != [(p["frame"], p["payload"]) for p in patches]:
                raise ValueError("Inferred patch rows changed")
            generated.append((mapping, rows, frames, channel_state, global_state))
        # All invariants above pass before any event file is emitted.
        results = []
        for mapping, rows, frames, channel_state, global_state in generated:
            folder = out / "maps" / mapping["id"]
            folder.mkdir(parents=True)
            with (folder / "events.txt").open("x") as stream:
                stream.write(serialize(rows))
            write_new(folder / "event-index.json", rows)
            results.append({"id": mapping["id"], "events": record(folder / "events.txt"),
                            "event_index": record(folder / "event-index.json"),
                            "event_count": len(rows), "note_ons": 1761, "note_offs": 1761,
                            "patch_rows": 100, "tick_frame_count": len(frames),
                            "old_onset_multiset_and_times_identical": True,
                            "all193_contiguous_off_before_on_preserved": True,
                            "raw_note_order_preserved": True,
                            "inferred_patch_frames_and_payloads_identical": True,
                            "per_channel_state": channel_state, "global_midi_state": global_state})
        for item in protocol["inputs"].values():
            verify(item)
        result = {"schema": SCHEMA, "status": "Metadata export invariants passed; no audio benchmark",
                  "protocol": record(out / "protocol-frozen.json"), "maps": results,
                  "source_counts": {"accepted_notes": len(notes), "accepted_messages": len(messages),
                                    "excluded_messages": len(excluded), "same_channel_contiguous": len(boundaries)},
                  "all_existing_inputs_unchanged": True, "audio_rendered": False,
                  "benchmark_started": False, "production_changed": False}
        write_new(out / "result.json", result)
        print(json.dumps(result, indent=2))
    except Exception as error:
        write_new(out / "failure.json", {"error": str(error), "type": type(error).__name__,
                                        "partial_files_preserved": True})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=("freeze", "run"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, default=ROOT / "Reference/Research/midi-event-order-audit-20261019.json")
    args = parser.parse_args()
    (freeze if args.action == "freeze" else run)(args)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
