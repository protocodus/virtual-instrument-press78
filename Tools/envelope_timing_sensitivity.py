#!/usr/bin/env python3
"""Freeze and score four event maps x three existing research DSP snapshots.

No production source is edited. Existing recordings and research snapshots are
required; none is downloaded. The corrected maps are failed-adoption sensitivity
scenarios, never selected by the synthesis score. Run freeze before run.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import importlib.util
import itertools
import json
import shutil
import subprocess
import time

import numpy as np
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[1]
SR = 48000
METRICS = ("joint_lr_band_rmse_db", "mid_band_rmse_db",
           "stereo_stft_convergence", "stereo_stft_log_error_db")
MODELS = ("baseline", "release_only_x3", "rr3_carrier")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def file_record(path):
    return {"path": str(Path(path).resolve()), "sha256": sha(path)}


def events(notes, intervals, bank, mapping):
    """Preserve the original sequence's separately rounded gate convention."""
    offset, scale = mapping["offset_seconds"], mapping["scale"]
    raw = {v["number"]: bytes(v["raw_data"]).hex() for v in bank["voices"]}
    rows = []
    for patch in intervals:
        frame = round((offset + scale * patch["midi_start_seconds"]) * SR)
        rows.append((frame, 0, len(rows), f'patch {raw[patch["patch"]]}'))
    for note in notes:
        onset = round((offset + scale * note["start"]) * SR)
        duration = round(scale * note["gate"] * SR)
        if duration <= 0 or note["velocity"] <= 0:
            continue
        rows.append((onset, 2, len(rows),
                     f'on {note["midi"]} {note["velocity"]} {note["channel"]}'))
        rows.append((onset + duration, 1, len(rows),
                     f'off {note["midi"]} {note["channel"]}'))
    return "".join(f"{frame} {line}\n" for frame, _, _, line in sorted(rows))


def freeze(args):
    out = args.output.resolve()
    if out.exists():
        raise RuntimeError("Refusing to overwrite any existing experiment directory")
    law, reverb = args.prior_law.resolve(), args.prior_reverb.resolve()
    old_law, old_reverb = read(law / "result.json"), read(reverb / "result.json")
    mapping_path = ROOT / "Docs/research/global-event-mapping-2026-10-19.json"
    mapping_report = read(mapping_path)
    maps = mapping_report["protocol"]["candidate_maps"]
    assert len(maps) == 4 and maps[0]["id"] == "unchanged"
    reference = args.reference_root.resolve() / "references"
    inputs = {"mapping_report": mapping_path, "prior_law_report": law / "result.json",
              "prior_reverb_report": reverb / "result.json",
              "recording": reference / "v2/user-ONfIvtDOog0.wav",
              "notes": reference / "v2/eugenia-events.json",
              "timeline": reference / "v3_program_timeline.json",
              "alignment": reference / "v2/alignment.json",
              "bank": ROOT / "Assets/FactoryBank/press78-factory.json",
              "production_cpp": ROOT / "Source/DSP/Press78Engine.cpp",
              "production_header": ROOT / "Source/DSP/Press78Engine.h"}
    for name in ("recording", "notes", "timeline", "alignment", "bank"):
        mapping_name = "events" if name == "notes" else name
        assert sha(inputs[name]) == mapping_report["protocol"]["source_files"][mapping_name]["sha256"]
    assert sha(inputs["recording"]) == old_law["source_recording"]["sha256"]
    assert inputs["production_cpp"].read_bytes() == (law / "baseline/source/Press78Engine.cpp").read_bytes()
    assert inputs["production_header"].read_bytes() == (law / "baseline/source/Press78Engine.h").read_bytes()
    out.mkdir(parents=True)
    snapshots = out / "snapshots"
    snapshots.mkdir()
    for name, source in (("HardwareSequence.cpp", law / "HardwareSequence.cpp"),
                         ("HardwareSequenceReverb.cpp", reverb / "HardwareSequenceReverb.cpp"),
                         ("stereo_metrics.py", reverb / "stereo_metrics.py"),
                         ("v4-protocol.json", reverb / "v4-protocol.json"),
                         ("mapping-report.json", mapping_path),
                         ("prior-law-report.json", law / "result.json"),
                         ("prior-reverb-report.json", reverb / "result.json"),
                         ("runner.py", Path(__file__))):
        shutil.copy2(source, snapshots / name)
    models = {}
    for key in MODELS:
        prior = old_reverb["models"][key]
        source = reverb / key / "source" if key == "rr3_carrier" else law / key / "source"
        expected = prior["definition"]["source_sha256"]
        assert {p.name: sha(p) for p in source.iterdir() if p.is_file()} == expected
        assert sha(prior["audio_file"]) == prior["audio_sha256"]
        dest = out / "models" / key / "source"
        shutil.copytree(source, dest)
        models[key] = {"source_sha256": expected, "prior_audio": file_record(prior["audio_file"]),
                       "definition": prior["definition"], "fixture":
                       "HardwareSequenceReverb.cpp" if key == "rr3_carrier" else "HardwareSequence.cpp"}
    notes = read(inputs["notes"])["notes"]
    intervals = read(inputs["timeline"])["intervals"]
    bank = read(inputs["bank"])
    map_records = []
    for mapping in maps:
        target = out / "maps" / mapping["id"]
        target.mkdir(parents=True)
        event_file = target / "events.txt"
        event_file.write_text(events(notes, intervals, bank, mapping))
        lines = event_file.read_text().splitlines()
        assert len(lines) == 3658
        assert sum(" patch " in line for line in lines) == 100
        assert sum(" on " in line for line in lines) == 1779
        if mapping["id"] == "unchanged":
            assert event_file.read_bytes() == (law / "events.txt").read_bytes()
            assert event_file.read_bytes() == (reverb / "events.txt").read_bytes()
        map_records.append({**mapping, "events": file_record(event_file), "event_count": len(lines)})
    protocol = {
        "version": "timing-by-release-reverb-four-by-three-v1",
        "frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "Frozen before any new scenario audio render or spectral score",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "scope": "Exactly four fixed event mappings x three prior fixed DSP states; descriptive sensitivity only",
        "mapping_adoption": "All corrected mappings failed the prior held-out adoption criteria. None is truth; no mapping or model is selected from these spectral scores.",
        "inputs": {name: file_record(path) for name, path in inputs.items()},
        "snapshots": {p.name: sha(p) for p in snapshots.iterdir()},
        "models": models, "maps": map_records,
        "scenario_order": [f'{mapping["id"]}/{key}' for mapping in maps for key in MODELS],
        "note_mapping": "on=round(48000*(offset+scale*source_start)); gate=round(48000*scale*source_gate); off=on+gate. This separate gate rounding exactly preserves the established baseline; it can differ by one sample from rounding mapped source end.",
        "program_mapping": "All100 inferred program changes use round(48000*(offset+scale*timeline.midi_start_seconds)). The old timeline audio_start_seconds is not reused for corrected maps. Bar-based program inference remains an assumption, not measured MIDI command time.",
        "event_order": "Sort by frame, then patch, old off, new on; preserve source-file order within each category. Patch changes preserve existing held/release voices.",
        "score_windows": "Exactly the100 prior v4 absolute recording-time windows, unchanged for every map/model. No moved or reselected windows.",
        "render": {"rate": SR, "polyphony": 12, "latency_samples": 32,
                   "chorus": "Frozen Recorded mode; epoch=-32/48000 seconds for every scenario, not remapped or fitted",
                   "master_gain": 1, "drive": 0, "tone_cutoff": 0, "dc_block": False,
                   "limiter": False, "artificial_noise": False,
                   "frames": old_law["models"]["baseline"]["render"]["frames"]},
        "metric": "Unchanged frozen stereo_metrics.py: one stereo-pair RMS normalization;64 bands80-14000Hz;STFT512/2048/8192. No local or per-model timing, phase, pitch, frequency or gain optimization beyond established pair RMS normalization.",
        "analysis": "All12 outcomes; every100-row metric; model contrasts within each map; difference-in-differences vs old mapping; per-patch ranking reversals and all100/target ranking stability. No adoption threshold or score-based winner selection.",
        "limitations": ["Reused recording/windows and prior calibrated DSP candidates, not a fresh holdout.",
                        "Changing maps jointly moves notes, gates and inferred program commands; it does not isolate physical MIDI latency from program inference or allocation history.",
                        "Recorded chorus remains an audio-time capture model; internal global LFO starts at time0. Event shifts therefore also change their phase at note arrival without any phase fitting.",
                        "The research Reverb candidate retains96dB retirement,12voice oldest replacement and48tick stolen fade; hardware allocator remains unverified."]}
    write(out / "protocol-frozen.json", protocol)
    print(json.dumps({"protocol": str(out / "protocol-frozen.json"),
                      "sha256": sha(out / "protocol-frozen.json"), "scenarios": 12}, indent=2))


def delta_summary(values):
    return {"mean_delta": float(np.mean([v["delta"] for v in values])),
            "improve_count": sum(v["delta"] < -1e-6 for v in values),
            "worsen_count": sum(v["delta"] > 1e-6 for v in values),
            "unchanged_within_1e_6": sum(abs(v["delta"]) <= 1e-6 for v in values),
            "all_patch_deltas": values,
            "largest_regressions": sorted(values, key=lambda x: x["delta"], reverse=True)[:10],
            "largest_improvements": sorted(values, key=lambda x: x["delta"])[:10]}


def run(args):
    out = args.output.resolve()
    if (out / "result.json").exists() or (out / "run-started.json").exists():
        raise RuntimeError("Experiment already started; preserve it and use a new frozen directory")
    protocol = read(out / "protocol-frozen.json")
    for record in protocol["inputs"].values():
        assert sha(record["path"]) == record["sha256"], record["path"]
    for name, digest in protocol["snapshots"].items():
        assert sha(out / "snapshots" / name) == digest
    assert sha(Path(__file__)) == protocol["snapshots"]["runner.py"]
    for mapping in protocol["maps"]:
        assert sha(mapping["events"]["path"]) == mapping["events"]["sha256"]
    write(out / "run-started.json", {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                   "protocol_sha256": sha(out / "protocol-frozen.json")})
    spec = importlib.util.spec_from_file_location("frozen_stereo_metric", out / "snapshots/stereo_metrics.py")
    metric = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metric)
    prior = read(out / "snapshots/prior-reverb-report.json")
    windows = read(out / "snapshots/v4-protocol.json")["windows"]
    sr, original = wavfile.read(protocol["inputs"]["recording"]["path"], mmap=True)
    assert sr == SR
    compiled = {}
    for key, definition in protocol["models"].items():
        source = out / "models" / key / "source"
        assert {p.name: sha(p) for p in source.iterdir() if p.is_file()} == definition["source_sha256"]
        executable = source.parent / "hardware_sequence"
        command = ["c++", "-std=c++17", "-O2", "-I", str(source),
                   str(out / "snapshots" / definition["fixture"]), str(source / "Press78Engine.cpp"),
                   "-o", str(executable)]
        subprocess.run(command, check=True, capture_output=True, text=True)
        compiled[key] = {"compile_command": command, "executable": str(executable),
                         "executable_sha256": sha(executable)}
    outcomes, data = {}, {}
    for mapping in protocol["maps"]:
        map_id = mapping["id"]
        data[map_id] = {}
        for key in MODELS:
            folder = out / "maps" / map_id / key
            folder.mkdir()
            audio = folder / "recorded-continuous.wav"
            command = [compiled[key]["executable"], mapping["events"]["path"], str(audio),
                       str(protocol["render"]["frames"]), str(SR), "recorded"]
            start = time.perf_counter()
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            detail = json.loads(result.stdout)
            detail["wall_seconds"] = time.perf_counter() - start
            rate, samples = wavfile.read(audio, mmap=True)
            assert rate == SR and detail["latency_samples"] == 32 and np.isfinite(samples).all()
            assert detail["events"] == 3658 and len(samples) == protocol["render"]["frames"]
            if map_id == "unchanged":
                assert sha(audio) == protocol["models"][key]["prior_audio"]["sha256"]
            data[map_id][key] = samples[32:32 + len(original)]
            assert data[map_id][key].shape == original.shape
            outcomes[f"{map_id}/{key}"] = {**compiled[key], "render_command": command,
                                          "render": detail, "audio": file_record(audio),
                                          "old_map_byte_identical_to_prior": map_id == "unchanged"}
            print("Rendered", map_id, key, flush=True)
    rows = []
    for window in windows:
        first, last = round(window["start_seconds"] * SR), round(window["end_seconds"] * SR)
        reference = original[first:last].astype(float) / 32768
        scores = {mapping["id"]: {key: metric.stereo_compare(reference, data[mapping["id"]][key][first:last], SR)
                                   for key in MODELS} for mapping in protocol["maps"]}
        old = next(row for row in prior["rows"] if row["patch"] == window["patch"])
        for key in MODELS:
            for name, value in scores["unchanged"][key].items():
                previous = old["scores"][key][name]
                assert (value is None and previous is None) or abs(value - previous) < 1e-12
        rows.append({**window, "scores": scores})
        if len(rows) % 10 == 0:
            print("Scored all12 scenarios for", len(rows), "windows", flush=True)
    groups = {"all100": list(range(100)), "targets": [65, 93, 97], "neighbors": [64, 66, 92, 94, 96, 98]}
    aggregate = {group: {mapping["id"]: {key: {name: float(np.mean([
        row["scores"][mapping["id"]][key][name] for row in rows if row["patch"] in patches]))
        for name in METRICS} for key in MODELS} for mapping in protocol["maps"]}
                 for group, patches in groups.items()}
    pairs = [("release_only_x3", "baseline"), ("rr3_carrier", "baseline"),
             ("rr3_carrier", "release_only_x3")]
    comparisons, map_effects, interactions = {}, {}, {}
    for mapping in protocol["maps"]:
        map_id = mapping["id"]
        comparisons[map_id] = {}
        for candidate, comparator in pairs:
            contrast = f"{candidate}_minus_{comparator}"
            comparisons[map_id][contrast] = {name: delta_summary([
                {"patch": row["patch"], "name": row["name"], "delta":
                 row["scores"][map_id][candidate][name] - row["scores"][map_id][comparator][name]}
                for row in rows]) for name in METRICS}
        if map_id == "unchanged":
            continue
        map_effects[map_id] = {key: {name: delta_summary([
            {"patch": row["patch"], "name": row["name"], "delta":
             row["scores"][map_id][key][name] - row["scores"]["unchanged"][key][name]}
            for row in rows]) for name in METRICS} for key in MODELS}
        interactions[map_id] = {}
        for candidate, comparator in pairs:
            contrast = f"{candidate}_minus_{comparator}"
            interactions[map_id][contrast] = {}
            for name in METRICS:
                values = []
                for row in rows:
                    def difference(m):
                        return row["scores"][m][candidate][name] - row["scores"][m][comparator][name]
                    old_delta, new_delta = difference("unchanged"), difference(map_id)
                    values.append({"patch": row["patch"], "name": row["name"],
                                   "old_map_model_delta": old_delta, "scenario_model_delta": new_delta,
                                   "delta": new_delta - old_delta,
                                   "strict_rank_reversal": old_delta * new_delta < 0 and
                                   min(abs(old_delta), abs(new_delta)) > 1e-6})
                interactions[map_id][contrast][name] = {
                    **delta_summary(values),
                    "strict_rank_reversal_count": sum(v["strict_rank_reversal"] for v in values)}
    rankings = {group: {mapping["id"]: {name: sorted(MODELS, key=lambda key:
        aggregate[group][mapping["id"]][key][name]) for name in METRICS}
        for mapping in protocol["maps"]} for group in groups}
    report = {"version": protocol["version"], "status": "Research-only complete12-scenario comparison; no mapping/DSP adopted",
              "artifact_directory": str(out), "protocol": protocol,
              "protocol_file": file_record(out / "protocol-frozen.json"),
              "models_and_renders": outcomes, "rows": rows, "aggregate": aggregate,
              "model_contrasts_within_map": comparisons, "map_effects_within_model": map_effects,
              "timing_by_model_interaction": interactions, "aggregate_model_orderings": rankings,
              "validation": {"all12_renders_finite": True, "all12_latency32": True,
                             "three_unchanged_map_whole_wavs_exactly_match_prior": True,
                             "three_unchanged_map_all100_all_metrics_match_prior_within1e_12": True,
                             "unchanged_map_all3658_events_byte_identical": True,
                             "all_maps_transform100_program_bars_and1779_note_on_gate_pairs": True,
                             "same100_absolute_v4_windows": True, "production_noise_absent": True,
                             "no_production_source_changes": all(sha(protocol["inputs"][name]["path"]) ==
                                protocol["inputs"][name]["sha256"] for name in ("production_cpp", "production_header"))},
              "decision": "No map or DSP adoption. Evaluate ranking stability and interaction across failed-adoption timing scenarios; spectral agreement does not identify event delivery or hardware constants."}
    write(out / "result.json", report)
    print(json.dumps({"aggregate": aggregate, "rankings": rankings}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    f = commands.add_parser("freeze")
    f.add_argument("--reference-root", type=Path, required=True)
    f.add_argument("--prior-law", type=Path, default=ROOT / "build/envelope-law-20261018")
    f.add_argument("--prior-reverb", type=Path, default=ROOT / "build/envelope-reverb-benchmark-20261018")
    f.add_argument("--output", type=Path, required=True)
    r = commands.add_parser("run")
    r.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    (freeze if args.command == "freeze" else run)(args)


if __name__ == "__main__":
    main()
