#!/usr/bin/env python3
"""Research-only Mode 00 source-input branch of the fixed timing experiment.

The documented 36..96 receive range selects the filter before any new score.
This never limits the instrument engine's musical range. Original local research
media and immutable prior snapshots are required; no files are downloaded.
"""
from pathlib import Path
import argparse
import collections
import csv
import datetime
import importlib.util
import json
import shutil
import subprocess
import time

import numpy as np
from scipy.io import wavfile

import envelope_timing_sensitivity as historical

ROOT, SR = historical.ROOT, historical.SR
MODELS, METRICS = historical.MODELS, historical.METRICS
sha, read, write, record = historical.sha, historical.read, historical.write, historical.file_record


def pressure(path):
    with Path(path).open() as handle:
        rows = list(csv.DictReader(handle))
    by_program = []
    for program in range(100):
        subset = [row for row in rows if int(row["program"]) == program]
        by_program.append({"patch": program, "note_ons": len(subset),
                           "oldest_replacements": sum(int(row["oldest_replacement"]) for row in subset),
                           "max_active_before": max((int(row["active_before"]) for row in subset), default=0),
                           "max_active_after": max((int(row["active_after"]) for row in subset), default=0)})
    return {"csv": record(path), "note_ons": len(rows),
            "oldest_replacements": sum(int(row["oldest_replacement"]) for row in rows),
            "max_active": max(int(row["active_after"]) for row in rows), "by_program": by_program}


def freeze(args):
    out, prior, audit = args.output.resolve(), args.prior_timing.resolve(), args.effect_audit.resolve()
    if out.exists():
        raise RuntimeError("Preserve existing artifacts; choose a new output directory")
    old = read(prior / "result.json")
    old_protocol = old["protocol"]
    classification = read(audit / "result.json")
    assert len(classification["samples"]) == 300 and len(classification["patches"]) == 100
    inputs = {**old_protocol["inputs"],
              "prior_timing_result": record(prior / "result.json"),
              "prior_timing_protocol": record(prior / "protocol-frozen.json"),
              "effect_classification": record(audit / "result.json"),
              "effect_protocol": record(audit / "protocol-frozen.json"),
              "manual_pdf": record(args.manual_pdf),
              "manual_printed31": record(audit / "owner-printed31.png"),
              "manual_printed34": record(audit / "owner-printed34.png"),
              "manual_printed45": record(args.manual_page45),
              "historical_tool": record(Path(historical.__file__))}
    for value in inputs.values():
        assert sha(value["path"]) == value["sha256"], value["path"]
    notes = read(inputs["notes"]["path"])["notes"]
    intervals = read(inputs["timeline"]["path"])["intervals"]
    bank = read(inputs["bank"]["path"])
    rejected = [{"source_note_index": index, **note} for index, note in enumerate(notes)
                if not 36 <= note["midi"] <= 96]
    accepted = [note for note in notes if 36 <= note["midi"] <= 96]
    assert len(notes) == 1779 and len(rejected) == 18 and len(accepted) == 1761
    assert collections.Counter(note["midi"] for note in rejected) == {29: 2, 34: 13, 35: 3}
    assert all(note["velocity"] == 127 for note in notes)
    assert all(note["channel"] == 1 for note in rejected)
    out.mkdir(parents=True)
    snapshots = out / "snapshots"
    snapshots.mkdir()
    for name, source in (("runner.py", Path(__file__)),
                         ("historical_tool.py", Path(historical.__file__)),
                         ("previous-result.json", prior / "result.json"),
                         ("v4-protocol.json", prior / "snapshots/v4-protocol.json"),
                         ("stereo_metrics.py", prior / "snapshots/stereo_metrics.py"),
                         ("HardwareSequencePressure.cpp", args.prior_law / "HardwareSequencePressure.cpp"),
                         ("HardwareSequencePressureReverb.cpp", args.prior_reverb / "HardwareSequencePressureReverb.cpp")):
        shutil.copy2(source, snapshots / name)
    models = {}
    for key in MODELS:
        source = prior / "models" / key / "source"
        expected = old_protocol["models"][key]["source_sha256"]
        assert {p.name: sha(p) for p in source.iterdir() if p.is_file()} == expected
        destination = out / "models" / key / "source"
        shutil.copytree(source, destination)
        models[key] = {**old_protocol["models"][key], "pressure_fixture":
                       "HardwareSequencePressureReverb.cpp" if key == "rr3_carrier" else "HardwareSequencePressure.cpp"}
    map_records = []
    exclusions = []
    for mapping in old_protocol["maps"]:
        assert historical.events(notes, intervals, bank, mapping).encode() == Path(mapping["events"]["path"]).read_bytes()
        folder = out / "maps" / mapping["id"]
        folder.mkdir(parents=True)
        target = folder / "events.txt"
        target.write_text(historical.events(accepted, intervals, bank, mapping))
        assert len(target.read_text().splitlines()) == 3622
        assert sum(" patch " in row for row in target.read_text().splitlines()) == 100
        map_records.append({**mapping, "historical_events": mapping["events"], "filtered_events": record(target)})
        for note in rejected:
            frame = round(SR * (mapping["offset_seconds"] + mapping["scale"] * note["start"]))
            gate = round(SR * mapping["scale"] * note["gate"])
            exclusions.append({"map": mapping["id"], **note, "excluded_on_frame": frame,
                               "excluded_off_frame": frame + gate})
    observed_frames = [sample["frame"] for sample in classification["samples"]]
    for frame in observed_frames:
        assert sha(frame["path"]) == frame["sha256"]
    protocol = {
        "schema": "source-mode00-timing-by-envelope-v1",
        "status": "Frozen before any filtered render or score",
        "frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "selection": {"policy": "Exclude both on/off of source notes outside inclusive36..96; selected from manual and sampled c.00 display before scores, not from spectral comparison.",
                      "evidence": "Exact manual printed31 identifies c.00 as Keyboard Assign mode; printed34 describes five-octave receive range and ignored velocity; printed45 lists received note range36..96. Root and independent source-frame review observed c.00 on all300 sampled frames, with later Sine99 snapshots consistent.",
                      "conditional_assumptions": ["The published source MIDI file is the sequence sent to this recording.",
                                                  "Source note numbers reached the hardware without upstream transpose or remap.",
                                                  "Sampled c.00 state applies during the scored performance; no continuous mode/wire log was recovered."],
                      "not_applied": "No engine-wide key limit, patch change, velocity-response law, transpose fit, note-off retiming or effect-state fit.",
                      "original_notes": 1779, "accepted_notes": 1761, "excluded_notes": 18,
                      "original_events": 3658, "filtered_events": 3622,
                      "excluded_pitch_counts": {"29": 2, "34": 13, "35": 3},
                      "all_source_velocities": 127, "excluded_zero_based_source_channel": 1},
        "inputs": inputs, "sampled_source_frames": observed_frames,
        "snapshots": {p.name: sha(p) for p in snapshots.iterdir()},
        "models": models, "maps": map_records, "exclusions": exclusions,
        "render": old_protocol["render"],
        "timing_and_metric": {key: old_protocol[key] for key in
                              ("note_mapping", "program_mapping", "event_order", "score_windows", "metric")},
        "pressure": "Existing read-only pressure fixtures log activeVoices before/after onsets and exact current-model oldest replacement condition. Re-render all12 historical scenarios and require full WAV hashes to match preserved prior audio before interpreting logs. Delete each temporary historical WAV after hashing. New12 scored WAVs come from the same audited pressure fixtures. Pressure counts describe the model, not hardware allocation.",
        "analysis": "Retain all12 filtered outcomes, same100 absolute v4 windows, every old/new per-preset metric and regression, within-map model contrasts, focus65/93/97 and all100/targets/neighbors means, old/new pressure. No candidate parameter fit or mapping/model adoption.",
        "storage": "Keep12 filtered full WAVs; at most one71.5MB diagnostic WAV exists temporarily; retained+temporary WAV bytes must remain below1,000,000,000. No historical artifacts are edited.",
        "limitations": old_protocol["limitations"] + ["Source MIDI identity/transposition and continuous mode delivery remain conditional. Lower filtered spectral error would not independently prove the source policy.",
                                                        "All velocity values already127, so this experiment cannot identify the hardware's fixed amplitude for ignored velocity."]}
    write(out / "protocol-frozen.json", protocol)
    print(json.dumps({"protocol": str(out / "protocol-frozen.json"), "sha256": sha(out / "protocol-frozen.json"),
                      "scenarios": 12, "accepted_notes": len(accepted), "filtered_events": 3622}, indent=2))


def run(args):
    out = args.output.resolve()
    if (out / "run-started.json").exists():
        raise RuntimeError("Experiment already started; preserve it and use a new frozen directory")
    protocol = read(out / "protocol-frozen.json")
    for value in protocol["inputs"].values():
        assert sha(value["path"]) == value["sha256"], value["path"]
    for name, value in protocol["snapshots"].items():
        assert sha(out / "snapshots" / name) == value
    assert sha(Path(__file__)) == protocol["snapshots"]["runner.py"]
    old = read(out / "snapshots/previous-result.json")
    write(out / "run-started.json", {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                   "protocol_sha256": sha(out / "protocol-frozen.json")})
    compiled = {}
    for key, model in protocol["models"].items():
        source = out / "models" / key / "source"
        assert {p.name: sha(p) for p in source.iterdir() if p.is_file()} == model["source_sha256"]
        executable = source.parent / "pressure_sequence"
        command = ["c++", "-std=c++17", "-O2", "-I", str(source),
                   str(out / "snapshots" / model["pressure_fixture"]), str(source / "Press78Engine.cpp"),
                   "-o", str(executable)]
        subprocess.run(command, check=True, capture_output=True, text=True)
        compiled[key] = {"compile_command": command, "executable": str(executable),
                         "executable_sha256": sha(executable)}
    sr, original = wavfile.read(protocol["inputs"]["recording"]["path"], mmap=True)
    assert sr == SR
    outcomes, data = {}, {}
    max_wav_bytes = 0
    def wav_budget():
        nonlocal max_wav_bytes
        total = sum(p.stat().st_size for p in out.rglob("*.wav"))
        max_wav_bytes = max(max_wav_bytes, total)
        assert total < 1_000_000_000, total
    for mapping in protocol["maps"]:
        mid = mapping["id"]
        data[mid] = {}
        assert sha(mapping["filtered_events"]["path"]) == mapping["filtered_events"]["sha256"]
        assert sha(mapping["historical_events"]["path"]) == mapping["historical_events"]["sha256"]
        for key in MODELS:
            folder = out / "maps" / mid / key
            folder.mkdir()
            renders = {}
            for branch in ("historical", "mode00"):
                audio = folder / ("historical-diagnostic-temporary.wav" if branch == "historical" else "mode00.wav")
                csv_path = folder / (branch + "-voice-pressure.csv")
                events = mapping["historical_events" if branch == "historical" else "filtered_events"]["path"]
                command = [compiled[key]["executable"], events, str(audio), str(protocol["render"]["frames"]),
                           str(SR), "recorded", str(csv_path)]
                start = time.perf_counter()
                run = subprocess.run(command, check=True, capture_output=True, text=True)
                detail = json.loads(run.stdout)
                detail["wall_seconds"] = time.perf_counter() - start
                rate, samples = wavfile.read(audio, mmap=True)
                assert rate == SR and detail["latency_samples"] == 32 and np.isfinite(samples).all()
                assert len(samples) == protocol["render"]["frames"]
                assert detail["events"] == (3658 if branch == "historical" else 3622)
                wav_budget()
                renders[branch] = {"render_command": command, "render": detail,
                                   "audio": record(audio), "pressure": pressure(csv_path)}
                assert renders[branch]["pressure"]["note_ons"] == (1779 if branch == "historical" else 1761)
                if branch == "historical":
                    expected = old["models_and_renders"][f"{mid}/{key}"]["audio"]["sha256"]
                    assert renders[branch]["audio"]["sha256"] == expected
                    del samples
                    audio.unlink()
                    renders[branch]["temporary_audio_deleted_after_exact_old_hash_match"] = True
                else:
                    data[mid][key] = samples[32:32 + len(original)]
                    assert data[mid][key].shape == original.shape
            before, after = renders["historical"]["pressure"], renders["mode00"]["pressure"]
            pd = [{"patch": a["patch"], "oldest_replacements_delta": a["oldest_replacements"] - b["oldest_replacements"],
                   "note_ons_delta": a["note_ons"] - b["note_ons"]}
                  for a, b in zip(after["by_program"], before["by_program"])]
            outcomes[f"{mid}/{key}"] = {**compiled[key], "branches": renders,
                                        "pressure_delta": {"oldest_replacements": after["oldest_replacements"] - before["oldest_replacements"],
                                                           "note_ons": after["note_ons"] - before["note_ons"], "by_program": pd}}
            print("Rendered + old-hash verified", mid, key, flush=True)
    spec = importlib.util.spec_from_file_location("frozen_metric", out / "snapshots/stereo_metrics.py")
    metric = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metric)
    windows = read(out / "snapshots/v4-protocol.json")["windows"]
    rows = []
    for window in windows:
        a, z = round(window["start_seconds"] * SR), round(window["end_seconds"] * SR)
        reference = original[a:z].astype(float) / 32768
        old_row = next(row for row in old["rows"] if row["patch"] == window["patch"])
        scores = {m["id"]: {key: metric.stereo_compare(reference, data[m["id"]][key][a:z], SR)
                             for key in MODELS} for m in protocol["maps"]}
        delta = {m["id"]: {key: {name: scores[m["id"]][key][name] - old_row["scores"][m["id"]][key][name]
                                 for name in METRICS} for key in MODELS} for m in protocol["maps"]}
        rows.append({**window, "scores": scores, "historical_scores": old_row["scores"],
                     "source_filter_delta": delta})
        if len(rows) % 10 == 0:
            print("Scored all12 scenarios for", len(rows), "windows", flush=True)
    groups = {"all100": list(range(100)), "targets": [65, 93, 97], "neighbors": [64, 66, 92, 94, 96, 98]}
    aggregate = {group: {m["id"]: {key: {name: float(np.mean([row["scores"][m["id"]][key][name]
        for row in rows if row["patch"] in patches])) for name in METRICS} for key in MODELS}
        for m in protocol["maps"]} for group, patches in groups.items()}
    filter_comparisons = {m["id"]: {key: {name: historical.delta_summary([
        {"patch": row["patch"], "name": row["name"], "delta": row["source_filter_delta"][m["id"]][key][name]}
        for row in rows]) for name in METRICS} for key in MODELS} for m in protocol["maps"]}
    pairs = [("release_only_x3", "baseline"), ("rr3_carrier", "baseline"), ("rr3_carrier", "release_only_x3")]
    model_comparisons = {m["id"]: {f"{candidate}_minus_{comparator}": {name: historical.delta_summary([
        {"patch": row["patch"], "name": row["name"], "delta": row["scores"][m["id"]][candidate][name] -
         row["scores"][m["id"]][comparator][name]} for row in rows]) for name in METRICS}
        for candidate, comparator in pairs} for m in protocol["maps"]}
    rankings = {group: {m["id"]: {name: sorted(MODELS, key=lambda key: aggregate[group][m["id"]][key][name])
        for name in METRICS} for m in protocol["maps"]} for group in groups}
    production_unchanged = all(sha(protocol["inputs"][name]["path"]) == protocol["inputs"][name]["sha256"]
                               for name in ("production_cpp", "production_header", "bank"))
    write(out / "result.json", {
        "schema": protocol["schema"], "status": "Research source-policy comparison; no model/map or engine-range change",
        "protocol": protocol, "protocol_file": record(out / "protocol-frozen.json"), "artifact_directory": str(out),
        "models_and_renders": outcomes, "rows": rows, "aggregate": aggregate,
        "historical_aggregate": old["aggregate"], "source_filter_comparisons": filter_comparisons,
        "model_contrasts_within_map": model_comparisons, "aggregate_model_orderings": rankings,
        "historical_model_orderings": old["aggregate_model_orderings"],
        "validation": {"all12_historical_diagnostic_whole_wavs_match_old_audio_hashes": True,
                       "historical_diagnostic_wavs_deleted_after_verification": True,
                       "all24_diagnostic_renders_finite_with32_frame_latency": True,
                       "all12_mode00_scenarios_1761_note_ons_3622_events": True,
                       "same100_absolute_windows": True, "production_and_factory_unchanged": production_unchanged,
                       "no_artificial_noise": True, "maximum_new_wav_bytes_including_temporary": max_wav_bytes},
        "decision": "No DSP, timing-map, transposition or engine-range adoption. This documents a source-mode-aware benchmark branch conditional on MIDI identity, unchanged note numbering and sampled Mode00 continuity. Every historical comparison remains preserved."})
    print(json.dumps({"aggregate": aggregate, "rankings": rankings}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    freeze_parser = commands.add_parser("freeze")
    freeze_parser.add_argument("--output", type=Path, required=True)
    freeze_parser.add_argument("--prior-timing", type=Path, default=ROOT / "build/timing-sensitivity-20261019")
    freeze_parser.add_argument("--prior-law", type=Path, default=ROOT / "build/envelope-law-20261018")
    freeze_parser.add_argument("--prior-reverb", type=Path, default=ROOT / "build/envelope-reverb-benchmark-20261018")
    freeze_parser.add_argument("--effect-audit", type=Path, default=ROOT / "build/effect-state-audit-20261019-v2")
    freeze_parser.add_argument("--manual-pdf", type=Path, default=ROOT / "build/fm-fidelity-audit-20261018/PSS780E.PDF")
    freeze_parser.add_argument("--manual-page45", type=Path, required=True)
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    (freeze if args.command == "freeze" else run)(args)


if __name__ == "__main__":
    main()
