#!/usr/bin/env python3
"""Gated conditional retained-recording benchmark. Never freeze/fit DSP here.

No source replay, model processing, PCM scoring or WAV export without a root
review receipt binding design + implementation + pure prechecks. Old recordings,
fixtures, results and failed gates are read-only. One own scratch at a time.
"""
from __future__ import annotations
import argparse
from collections import Counter
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BUILD = ROOT / "build/command-recording-benchmark-20261019"
DESIGN = HERE / "design-frozen.json"
CODE = ("BenchmarkSequence.h", "BenchmarkRenderer.cpp", "ContractTests.cpp", "run.py")
METRICS = ("joint_lr_band_rmse_db", "mid_band_rmse_db", "stereo_stft_convergence", "stereo_stft_log_error_db")
FOCUS = (65, 93, 97, 99, 199, 200)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def record(path):
    path = Path(path).resolve()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}


def read(path):
    return json.loads(Path(path).read_text())


def write_new(path, value):
    path = Path(path)
    payload = (json.dumps(value, indent=2, allow_nan=False) + "\n").encode("utf-8")
    cap = 1024 * 1024 if path.name.endswith("-scores.json") else 8 * 1024 * 1024
    if len(payload) > cap:
        raise RuntimeError("JSON byte cap exceeded before write")
    if BUILD in path.resolve().parents:
        budget(read(DESIGN), len(payload))
    with path.open("xb") as stream:
        stream.write(payload)


def verify(item):
    actual = record(item["path"])
    if actual["sha256"] != item["sha256"] or actual["bytes"] != item["bytes"]:
        raise ValueError("Changed frozen input: " + item["path"])


def implementation():
    return {name: sha(HERE / name) for name in CODE}


def bytes_below(folder):
    return sum(p.stat().st_size for p in folder.rglob("*") if p.is_file())


def budget(design, incoming=0):
    # Count the WHOLE own experiment subtree, including earlier prechecks and
    # failures, not merely this run. Never remove prior evidence for headroom.
    size = bytes_below(BUILD)
    if size + incoming > design["storage"]["maximum_new_bytes"]:
        raise RuntimeError("Own subtree would exceed frozen200MiB cap")
    free = shutil.disk_usage(BUILD).free
    if free < incoming + 64 * 1024 * 1024:
        raise RuntimeError("Insufficient scratch plus64MiB free headroom")
    return {"subtree_bytes": size, "incoming_bytes": incoming, "free_bytes": free}


def check_review(path):
    review = read(path)
    if review.get("schema") != "press78.command-recording-root-execution-review.v1" or review.get("approved") is not True:
        raise ValueError("Explicit bound root execution approval required")
    if review.get("design_sha256") != sha(DESIGN) or review.get("implementation_sha256") != implementation():
        raise ValueError("Review does not bind the current protocol/implementation")
    prechecks = review.get("prechecks")
    if not isinstance(prechecks, dict):
        raise ValueError("Review must bind pure prechecks")
    verify(prechecks)
    pre = read(prechecks["path"])
    if pre.get("passed") is not True or pre.get("audio_processed") is not False:
        raise ValueError("Required prechecks must be pure, passing and audio-free")
    return review


def verify_all(design):
    for item in design["inputs"].values():
        verify(item)
    for fixture in design["fixtures"]:
        verify(fixture["events"])
        verify(fixture["ledger"])


def validate_fixtures(design):
    """Only called after root gate. No sound/media decoding in this function."""
    bank = read(design["inputs"]["bank"]["path"])["voices"]
    if [v["number"] for v in bank] != list(range(100)):
        raise ValueError("Expected exact100-program bank order")
    payloads = {}
    flags = Counter()
    for voice in bank:
        raw = voice["raw_data"]
        if len(raw) != 33 or any(type(b) is not int or not 0 <= b <= 255 for b in raw) or not 0 <= raw[0] <= 4 or raw[32] != 0:
            raise ValueError("Unexpected raw factory format")
        # Independent4824-check original-table proof binds this exact bank.
        # Do not reconstruct from a masked shipping Patch.
        working = [0] * 32
        working[:31] = raw[1:32]
        working[23] = raw[24]
        working[31] = 0
        if working != raw[1:]:
            raise ValueError("Current explicit padding differs from public source")
        flags[working[23]] += 1
        payloads[voice["number"]] = bytes(raw).hex()
    if dict(flags) != {0: 59, 64: 4, 128: 35, 192: 2}:
        raise ValueError("Factory effect distribution changed")
    checks = []
    for fixture in design["fixtures"]:
        ledger = read(fixture["ledger"]["path"])
        rows = ledger["events"]
        if ledger["sample_rate"] != 48000 or ledger["scenario"] != fixture["order"] or ledger["map_id"] != fixture["map"]["id"]:
            raise ValueError("Fixture identity mismatch")
        actual = Path(fixture["events"]["path"]).read_text().splitlines()
        expected, channels, programs, ids = [], Counter(), [], []
        last = -1
        for row in rows:
            frame = row["frame"]
            if type(frame) is not int or not last <= frame < design["render_controls"]["frames"]:
                raise ValueError("Unsupported fixture frame domain")
            last = frame
            if row["kind"] == "patch":
                program = row["patch"]
                if row.get("inferred") is not True or row["timeline_ordinal"] != len(programs):
                    raise ValueError("Inferred program provenance mismatch")
                programs.append(program)
                expected.append(f"{frame} patch {payloads[program]}")
            else:
                channel, note, velocity = row["channel"], row["midi"], row["velocity"]
                if channel not in (0, 1) or not 36 <= note <= 96 or not 0 <= velocity <= 127:
                    raise ValueError("Unsupported conditional MIDI domain")
                if row["kind"] == "on":
                    if velocity == 0:
                        raise ValueError("Zero velocity ON must already be OFF")
                    expected.append(f"{frame} on {note} {velocity} {channel}")
                elif row["kind"] == "off":
                    expected.append(f"{frame} off {note} {channel}")
                else:
                    raise ValueError("Unknown source event")
                # These provenance keys remain in the bound original ledger.
                for field in ("source_id", "tick", "track", "ordinal", "raw_status", "seconds_exact"):
                    if field not in row:
                        raise ValueError("Missing source identity " + field)
                channels[channel] += 1
                ids.append(row["source_id"])
        counts = Counter(row["kind"] for row in rows)
        if actual != expected or len(rows) != 3622 or counts != {"patch": 100, "on": 1761, "off": 1761} or programs != list(range(100)) or len(ids) != len(set(ids)):
            raise ValueError("Whole source JSON/text/payload/count mismatch")
        if set(channels) != {0, 1}:
            raise ValueError("Both conditional source channels required")
        checks.append({"id": fixture["id"], "events": len(rows), "counts": dict(counts), "channels": dict(channels),
                       "source_identity": "input index joins bound original JSON source_id/tick/track/ordinal/status/channel", "equal_frame_groups": len({r["frame"] for r in rows}), "all_json_text_payloads_exact": True})
    return {"passed": True, "factory_rows": 100, "flags": dict(flags), "fixtures": checks,
            "clock_volume_scope": "Both clock offset/drift0; volumeIndex9 is neutral assumption, not captured calibration."}


def compile_one(source, output, log):
    command = ["clang++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-pedantic", str(HERE / source), "-o", str(output)]
    with Path(log).open("xb") as stream:
        subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)
    return {"command": command, "binary": record(output), "log": record(log)}


def run(args):
    # Approval and hash checks precede retained event replay, source PCM access
    # through wavfile, compilation of executable paths and all audio processing.
    review = check_review(args.review)
    design = read(DESIGN)
    verify_all(design)
    output = args.output.resolve()
    if BUILD not in output.parents or output.exists():
        raise ValueError("Use a fresh descendant of this ignored experiment directory")
    budget(design, design["storage"]["scratch_maximum"] + 16 * 1024 * 1024)
    output.mkdir(parents=True)
    write_new(output / "run-started.json", {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "design": record(DESIGN), "root_review": record(args.review), "implementation_sha256": implementation()})
    scratch = output / "scratch.wav"
    try:
        conformance = validate_fixtures(design)
        write_new(output / "fixture-conformance.json", conformance)
        renderer = compile_one("BenchmarkRenderer.cpp", output / "renderer", output / "compile-renderer.log")
        contracts = compile_one("ContractTests.cpp", output / "contracts", output / "compile-contracts.log")
        with (output / "audio-contract.json").open("xb") as stdout, (output / "audio-contract.stderr").open("xb") as stderr:
            subprocess.run([contracts["binary"]["path"], "--audio-contract", "REVIEW_AUTHORIZED"], stdout=stdout, stderr=stderr, cwd=ROOT, check=True)
        if read(output / "audio-contract.json").get("audio_processed") is not True:
            raise ValueError("Audio contracts not executed")
        # Local retained PCM only. No ffmpeg/download/extra full recording copy.
        import numpy as np
        from scipy.io import wavfile
        rate, reference = wavfile.read(design["inputs"]["recording"]["path"], mmap=True)
        frames = design["render_controls"]["frames"]
        if rate != 48000 or reference.dtype != np.int16 or reference.shape != (design["reference_pcm"]["frames"], 2) or len(reference) > frames - 32:
            raise ValueError("Unexpected original retained PCM")
        spec = importlib.util.spec_from_file_location("exact_frozen_command_recording_metric", design["inputs"]["metric"]["path"])
        metric = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(metric)
        supports = design["windows"] + design["diagnostic_windows"]
        if len(supports) != 102 or [w["patch"] for w in supports[:100]] != list(range(100)) or [w["patch"] for w in supports[100:]] != [199, 200]:
            raise ValueError("Changed original fixed supports")
        cells, focus_files, max_size = [], {}, bytes_below(BUILD)
        for fixture in design["fixtures"]:
            for path in ("A", "B"):
                # Exact source invariants, actual subtree usage and free space
                # are checked BEFORE each new full scratch is constructed.
                check_review(args.review)
                verify_all(design)
                space = budget(design, design["storage"]["scratch_maximum"] + 16 * 1024 * 1024)
                if scratch.exists():
                    raise RuntimeError("Prior scratch retained; refusing replacement")
                cell_id = fixture["id"] + "/" + path
                stem = cell_id.replace("/", "--")
                pressure, journal = output / (stem + "-events.csv"), output / (stem + "-commands.csv")
                command = [renderer["binary"]["path"], path, fixture["events"]["path"], str(scratch), str(pressure), str(journal), str(frames), "128", "REVIEW_AUTHORIZED"]
                with (output / (stem + "-render.json")).open("xb") as stdout, (output / (stem + "-render.stderr")).open("xb") as stderr:
                    subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr, check=True)
                detail = read(output / (stem + "-render.json"))
                sr, data = wavfile.read(scratch, mmap=True)
                if sr != 48000 or data.dtype != np.float32 or data.shape != (frames, 2) or not np.isfinite(data).all():
                    raise ValueError("Invalid complete model output; keep scratch")
                if detail["events"] != 3622 or detail["latency_frames"] != 32 or detail["source_groups"] != next(c["equal_frame_groups"] for c in conformance["fixtures"] if c["id"] == fixture["id"]) or detail["vibrato_invocations"] != (frames - 1) // 240:
                    raise ValueError("Render schedule/count mismatch; keep scratch")
                whole = record(scratch)
                aligned = data[32:32 + len(reference)]
                rows = []
                for window in supports:
                    first, last = round(window["start_seconds"] * 48000), round(window["end_seconds"] * 48000)
                    observed = reference[first:last].astype(float) / 32768
                    candidate = aligned[first:last]
                    score = metric.stereo_compare(observed, candidate, 48000)
                    if any(key not in score for key in METRICS) or any(value is not None and not math.isfinite(value) for value in score.values()):
                        raise ValueError("Invalid metric object; keep scratch")
                    row = {**window, "first_frame": first, "last_frame_exclusive": last, "scores": score,
                           "candidate_float32_support_sha256": hashlib.sha256(candidate.tobytes(order="C")).hexdigest(),
                           "reference_pcm16_support_sha256": hashlib.sha256(reference[first:last].tobytes(order="C")).hexdigest(),
                           "raw_model_pair_rms": float(np.sqrt(np.mean(candidate.astype(float) ** 2))),
                           "raw_reference_pair_rms": float(np.sqrt(np.mean(observed ** 2))), "raw_model_peak": float(np.max(np.abs(candidate)))}
                    if fixture["id"] == "unchanged/ascending_track" and window["patch"] in FOCUS:
                        dest = output / "focus" / str(window["patch"])
                        dest.mkdir(parents=True, exist_ok=True)
                        clip = dest / (path + ".wav")
                        if clip.exists():
                            raise ValueError("Refusing prior focused PCM")
                        wavfile.write(clip, 48000, np.array(candidate, dtype=np.float32))
                        cr, cx = wavfile.read(clip, mmap=True)
                        if cr != 48000 or cx.dtype != np.float32 or not np.array_equal(candidate, cx) or hashlib.sha256(cx.tobytes(order="C")).hexdigest() != row["candidate_float32_support_sha256"]:
                            raise ValueError("Focused exact PCM export mismatch; keep scratch")
                        focus_files.setdefault(str(window["patch"]), {})[path] = {"audio": record(clip), "scores": score, "model_support_sha256": row["candidate_float32_support_sha256"], "raw_model_pair_rms": row["raw_model_pair_rms"], "raw_reference_pair_rms": row["raw_reference_pair_rms"], "raw_model_peak": row["raw_model_peak"], "listening_pair_RMS_gain": row["raw_reference_pair_rms"] / row["raw_model_pair_rms"] if row["raw_model_pair_rms"] > 0 else None}
                        del cx
                    rows.append(row)
                if len(rows) != 102:
                    raise ValueError("Incomplete scores; keep scratch")
                verify_all(design)
                check_review(args.review)
                max_size = max(max_size, bytes_below(BUILD))
                budget(design)
                cell = {"id": cell_id, "fixture": fixture, "path": path, "render": detail, "command": command, "whole_float32_wav": whole,
                        "retention": "Ephemeral own scratch; delete only after this successful full scoring/checkpoint. Hash retained; full PCM not retained for independent full recalculation.",
                        "event_ledger": record(pressure), "command_ledger": record(journal), "space_before_render": space, "rows": rows}
                checkpoint = output / (stem + "-scores.json")
                write_new(checkpoint, cell)
                # Do not delete before every score/export/hash/frozen-source/
                # budget/checkpoint succeeds. Delete only this own fresh file.
                del candidate, aligned, data
                if scratch.parent != output or scratch.name != "scratch.wav" or scratch.is_symlink() or sha(scratch) != whole["sha256"]:
                    raise ValueError("Scratch identity changed; preserve")
                scratch.unlink()
                write_new(output / (stem + "-scratch-deleted.json"), {"removed_only_own_successful_scratch": True, "whole_wav_sha256": whole["sha256"], "complete_checkpoint": record(checkpoint)})
                cells.append(cell)
                print("Scored", cell_id, "102fixed supports; scratch removed after checkpoint", flush=True)
        contrasts, regressions, aggregate = {}, {}, {}
        groups = {"all100": list(range(100)), "focus": [65, 93, 97, 99], "neighbors": [64, 66, 92, 94, 96, 98]}
        for fixture in design["fixtures"]:
            fid = fixture["id"]
            a, b = [next(c for c in cells if c["id"] == fid + "/" + path) for path in ("A", "B")]
            differences = [{"patch": x["patch"], "name": x["name"], "B_minus_A": {key: y["scores"][key] - x["scores"][key] for key in METRICS}} for x, y in zip(a["rows"], b["rows"])]
            contrasts[fid] = differences
            regressions[fid] = {key: [r for r in differences if r["B_minus_A"][key] > 0] for key in METRICS}
            aggregate[fid] = {group: {path: {key: float(np.mean([r["scores"][key] for r in cell["rows"] if r["patch"] in patches])) for key in METRICS} for path, cell in (("A", a), ("B", b))} for group, patches in groups.items()}
        # Raw focused files remain exact score supports. Report fixed listening
        # trims separately; no hidden PCM normalization or level calibration.
        for paths in focus_files.values():
            peaks = [item["raw_model_peak"] * item["listening_pair_RMS_gain"] for item in paths.values() if item["listening_pair_RMS_gain"] is not None]
            safety = min(1.0, .9 / max(max(peaks), 1e-12)) if peaks else None
            for item in paths.values():
                item["common_pair_listening_safety"] = safety
        write_new(output / "key.json", {"A": "Unchanged shipping Engine baseline", "B": "One-owner complete command consumer", "files": "Raw exact scoring PCM, no hidden file trims. Fixed pair-RMS gains and common per-support safety reported for level-matched playback; level itself is uncalibrated.", "focus": focus_files})
        (output / "key.md").write_text("# Conditional A/B key\n\nA is the unchanged shipping Engine baseline; B is the fixed-slot command consumer. The six supports are65/93/97/99/199/200, only unchanged/ascending_track. WAVs retain exact raw scoring PCM. key.json gives one pair-RMS listening gain per file and a common safety per support; no listening preference is selected. Reverb is visibly ON but its audio law is unsupported/store-only here. This compares bundled command policy, not isolated envelope calibration.\n")
        verify_all(design)
        budget(design)
        result = {"schema": design["schema"], "status": "completed descriptive comparison; no promotion", "design": record(DESIGN), "root_review": record(args.review), "implementation_sha256": implementation(),
                  "conformance": conformance, "compilations": {"renderer": renderer, "contracts": contracts}, "audio_contract": record(output / "audio-contract.json"),
                  "cells": cells, "score_objects": sum(len(c["rows"]) for c in cells), "contrasts": contrasts, "positive_regressions": regressions, "aggregate": aggregate,
                  "focused_pcm": focus_files, "maximum_observed_subtree_bytes": max(max_size, bytes_below(BUILD)), "storage_limit_bytes": design["storage"]["maximum_new_bytes"],
                  "independent_metric_recheck": "Pending separate review of retained focused PCM only; no independent full discardedPCM claim.", "historical_results": "Unchanged, separately bound; earlier failed gates not overturned.", "new_fit": False, "artificial_noise": False, "production_changes": False}
        if result["score_objects"] != 1632:
            raise ValueError("Incomplete full result")
        write_new(output / "result.json", result)
        budget(design)
    except BaseException as error:
        failure = output / "failure.json"
        if not failure.exists():
            write_new(failure, {"error": repr(error), "traceback": traceback.format_exc(), "scratch_exists": scratch.exists(), "scratch_retained": record(scratch) if scratch.exists() else None, "historical_files_untouched": True})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
