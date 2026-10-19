#!/usr/bin/env python3
"""Freeze and read sampled effect LEDs in the retained PSS-780 tour.

This reads video pixels only. It does not infer an effect algorithm, edit the
recording alignment, render audio, change presets, or operate an instrument.
Third-party frames remain in the requested local artifact directory.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import math
import subprocess

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CENTERS = {"vibrato": [421, 196], "sustain": [421, 222],
           "reverb": [421, 247], "portamento": [421, 272],
           "chorus": [421, 298], "duet": [456, 196]}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def record(path):
    path = Path(path).resolve()
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}


def extract(video, frames, folder):
    folder.mkdir()
    # A long left-associative addition exceeds libavutil's expression parser
    # recursion limit. Balance the identical terms without changing selection.
    def balanced(terms):
        if len(terms) == 1:
            return terms[0]
        split = len(terms) // 2
        return f"({balanced(terms[:split])}+{balanced(terms[split:])})"
    expression = balanced([f"eq(n,{n})" for n in frames])
    command = ["ffmpeg", "-v", "error", "-i", str(video), "-vf",
               f"select='{expression}'", "-fps_mode", "vfr", "-frames:v",
               str(len(frames)), str(folder / "%03d.png")]
    subprocess.run(command, check=True)
    paths = sorted(folder.glob("*.png"))
    if len(paths) != len(frames):
        raise RuntimeError("Not every frozen frame was extracted")
    return command, dict(zip(frames, paths))


def features(path, centers):
    with Image.open(path) as image:
        if image.size != (1280, 720):
            raise RuntimeError("The frozen pixel geometry requires 1280x720")
        pixels = np.asarray(image.convert("RGB"), dtype=float)
    result = {}
    for key, (x, y) in centers.items():
        area = pixels[y-4:y+5, x-4:x+5]
        redness = area[:, :, 0] - np.maximum(area[:, :, 1], area[:, :, 2])
        result[key] = float(np.mean(np.sort(redness.ravel())[-5:]))
    return result


def freeze(args):
    out = args.output.resolve()
    if (out / "protocol-frozen.json").exists():
        raise RuntimeError("A protocol already exists; use a new output directory")
    ref = args.reference_root.resolve()
    inputs = {"video": ref / "references/v2/user-ONfIvtDOog0.mkv",
              "timeline": ref / "references/v3_program_timeline.json",
              "bank": ROOT / "Assets/FactoryBank/press78-factory.json",
              "manual_effect_page": ref / "research/v3-owner-effects-p9.png"}
    timeline = read(inputs["timeline"])["intervals"]
    if [x["patch"] for x in timeline] != list(range(100)):
        raise RuntimeError("Expected all100 existing program intervals")
    samples = [{"patch": p["patch"], "offset_from_observed_led_start": offset,
                "source_frame": math.ceil(30 * (p["led_start_seconds"] + offset) - 1e-9)}
               for p in timeline for offset in (.4, .8, 1.2)]
    if len({r["source_frame"] for r in samples}) != 300:
        raise RuntimeError("Expected300 distinct frozen video frames")
    out.mkdir(parents=True, exist_ok=True)
    calibration = [r for r in samples if r["patch"] in (69, 99)
                   and r["offset_from_observed_led_start"] == .8]
    command, images = extract(inputs["video"],
                              [r["source_frame"] for r in calibration], out / "calibration-frozen")
    values = {r["patch"]: features(images[r["source_frame"]], CENTERS) for r in calibration}
    on_cells = [(69, "sustain"), (69, "reverb"), (69, "chorus"),
                (99, "reverb"), (99, "chorus")]
    off_cells = [(p, key) for p in (69, 99) for key in CENTERS if (p, key) not in on_cells]
    on = [values[p][key] for p, key in on_cells]
    off = [values[p][key] for p, key in off_cells]
    threshold = (float(np.median(on)) + float(np.median(off))) / 2
    if min(on) <= threshold + 10 or max(off) >= threshold - 10:
        raise RuntimeError("Calibration separation fails the fixed10-unit margin")
    protocol = {"schema": 1,
                "frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "source_url": "https://www.youtube.com/watch?v=ONfIvtDOog0",
                "scope": "Three sampled visible LED states per preset in one reused video, not continuous state or effect-algorithm recovery",
                "inputs": {key: record(path) for key, path in inputs.items()},
                "tool": record(Path(__file__)),
                "video": {"width": 1280, "height": 720, "fps": 30, "start_seconds": 0},
                "centers": CENTERS,
                "samples": samples,
                "calibration": {"selection": "Only preset69/99 at observedLCDstart+.8s; these frames were visually inspected before freeze",
                                "on_cells": on_cells, "off_cells": off_cells,
                                "features": values, "threshold": threshold,
                                "files": [record(p) for p in images.values()], "command": command},
                "feature": "Mean of the five largest R-max(G,B) values in a fixed9x9ROI, no expected-preset-state input",
                "classification": "ON above threshold+10, OFF below threshold-10, otherwise UNKNOWN. No per-LED threshold or later adjustment.",
                "consensus": "All three samples must be the same known state; any disagreement or unknown is unresolved, with every sample retained.",
                "comparison": "Only after classification compare Vibrato/Sustain with raw byte24 bits7/6. Other four states have no field in the imported voice data.",
                "limits": ["Video/patches have already been used throughout development; not a fresh recording or unseen holdout.",
                           "The two calibration frames contribute to the300 samples and are not independent validation.",
                           "ObservedLCD timing selects snapshots only; no sample-accurate delivered program or MIDI timestamp is inferred.",
                           "Fixed pixels can fail under camera motion, scan flicker, obstruction or codec artifacts; unresolved cases are not filled from factory flags.",
                           "Visible LED state does not identify audio routing, external processing, actual parameter values or effect implementation."]}
    write(out / "protocol-frozen.json", protocol)
    print(json.dumps({"protocol_sha256": sha(out / "protocol-frozen.json"),
                      "threshold": threshold, "on_range": [min(on), max(on)],
                      "off_range": [min(off), max(off)], "samples": len(samples)}, indent=2))


def run(args):
    out = args.output.resolve()
    if (out / "run-started.json").exists():
        raise RuntimeError("Preserve the started experiment; use a new directory")
    protocol = read(out / "protocol-frozen.json")
    for item in [*protocol["inputs"].values(), protocol["tool"], *protocol["calibration"]["files"]]:
        if sha(item["path"]) != item["sha256"]:
            raise RuntimeError(f"Frozen input changed: {item['path']}")
    write(out / "run-started.json", {"protocol_sha256": sha(out / "protocol-frozen.json")})
    command, images = extract(protocol["inputs"]["video"]["path"],
                              [r["source_frame"] for r in protocol["samples"]], out / "frames")
    threshold = protocol["calibration"]["threshold"]
    rows = []
    for sample in protocol["samples"]:
        path = images[sample["source_frame"]]
        values = features(path, protocol["centers"])
        states = {key: "ON" if value > threshold + 10 else
                  "OFF" if value < threshold - 10 else "UNKNOWN"
                  for key, value in values.items()}
        rows.append({**sample, "source_seconds": sample["source_frame"] / 30,
                     "frame": record(path), "features": values, "states": states})
    bank = read(protocol["inputs"]["bank"]["path"])["voices"]
    patches = []
    for patch in range(100):
        members = [r for r in rows if r["patch"] == patch]
        consensus = {}
        for key in protocol["centers"]:
            seen = {r["states"][key] for r in members}
            consensus[key] = next(iter(seen)) if len(seen) == 1 and "UNKNOWN" not in seen else "UNRESOLVED"
        voice = next(v for v in bank if v["number"] == patch)
        expected = {key: "ON" if voice["raw_data"][24] & bit else "OFF"
                    for key, bit in (("vibrato", 128), ("sustain", 64))}
        patches.append({"patch": patch, "name": voice["name"], "consensus": consensus,
                        "expected_raw_flags": expected,
                        "raw_flag_agreement": {key: consensus[key] == value for key, value in expected.items()}})
    # Contact sheets preserve enough source context to check the effect column
    # against the visible LCD program number. No third-party image is published.
    sheets = []
    for start in range(0, 100, 10):
        sheet = Image.new("RGB", (1095, 1810), "#eeeeee")
        draw = ImageDraw.Draw(sheet)
        for row_index, patch in enumerate(range(start, start + 10)):
            for column, row in enumerate(r for r in rows if r["patch"] == patch):
                x, y = column * 365, row_index * 181
                draw.text((x+4, y+3), f"{patch:02d}; video{row['source_seconds']:.3f}s", fill="black")
                with Image.open(row["frame"]["path"]) as frame:
                    sheet.paste(frame.crop((350, 170, 715, 330)), (x, y+20))
        path = out / f"contact-{start:02d}-{start+9:02d}.png"
        sheet.save(path)
        sheets.append(record(path))
    result = {"protocol_sha256": sha(out / "protocol-frozen.json"), "command": command,
              "samples": rows, "patches": patches, "contact_sheets": sheets,
              "summary": {key: {state: sum(p["consensus"][key] == state for p in patches)
                                 for state in ("ON", "OFF", "UNRESOLVED")}
                          for key in protocol["centers"]},
              "raw_flag_mismatches": [p for p in patches if not all(p["raw_flag_agreement"].values())],
              "production_or_alignment_changed": False, "audio_measured": False}
    write(out / "result.json", result)
    print(json.dumps({"summary": result["summary"], "raw_flag_mismatches": result["raw_flag_mismatches"],
                      "result_sha256": sha(out / "result.json")}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "run"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference-root", type=Path)
    args = parser.parse_args()
    if args.command == "freeze" and args.reference_root is None:
        parser.error("freeze requires --reference-root")
    (freeze if args.command == "freeze" else run)(args)


if __name__ == "__main__":
    main()
