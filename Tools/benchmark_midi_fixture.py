#!/usr/bin/env python3
"""Research-only old/corrected MIDI fixture x Legacy/Original allocation study.

Requires retained local evidence. Freeze before independent source review, then
run once. Does not fit audio, change DSP, or implement the original program loader.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import shutil
import subprocess
import traceback

import numpy as np
from scipy.io import wavfile
import benchmark_pitch_model as common

ROOT = Path(__file__).resolve().parents[1]
SR, MAPS, METRICS, FOCUS = common.SR, common.MAPS, common.METRICS, common.FOCUS
NAMES = ("OldLegacy", "OldOriginal", "CorrectedLegacy", "CorrectedOriginal")
sha, read, write, record, verify = common.sha, common.read, common.write, common.record, common.verify


def fresh_output(path):
    out = path.resolve()
    assert out.is_relative_to(ROOT / "build") and out != ROOT / "build", "Research output must be below build/"
    return out


def file_manifest(folder):
    return {p.name: sha(p) for p in folder.iterdir() if p.is_file()}


def freeze(args):
    out = fresh_output(args.output)
    assert not out.exists(), "Keep every prior run; choose a fresh directory"
    old_dir = ROOT / "build/allocator-recording-comparison-v3-20261019"
    old = read(old_dir / "result.json")
    prior, bound = old["protocol"], read(old_dir / "candidate-bound.json")
    assert not old["audio_gates_passed"], "Retain the original failed decision"
    verify(old["design"])
    verify(old["candidate_binding"])
    for key in ("fixture", "baseline_fixture", "command_validation", "runner", "common_module"):
        verify(bound[key])
    for key in ("executable", "baseline_executable"):
        verify(old[key])
    validation = read(bound["command_validation"]["path"])
    assert validation["passed"] and all(validation["requirements"].values())
    export_path = ROOT / "Docs/research/midi-reference-export-2026-10-19.json"
    export = read(export_path)
    assert export["independent_review"]["checks"] == 41553
    for item in export["artifacts"]:
        verify(item)
    verify(export["independent_review"]["receipt"])
    assert export["result"]["all_existing_inputs_unchanged"]
    verify(prior["recording"])
    verify(prior["bank"])
    maps = []
    assert tuple(m["id"] for m in prior["maps"]) == MAPS
    for m in prior["maps"]:
        mid = m["id"]
        new = next(v for v in export["result"]["maps"] if v["id"] == mid)
        timing = next(v for v in export["protocol"]["maps"] if v["id"] == mid)
        assert (m["offset_seconds"], m["scale"]) == (timing["offset_seconds"], timing["scale"])
        assert new["event_count"] == 3622 and new["note_ons"] == new["note_offs"] == 1761 and new["patch_rows"] == 100
        assert new["all193_contiguous_off_before_on_preserved"] and new["raw_note_order_preserved"]
        assert new["old_onset_multiset_and_times_identical"] and new["inferred_patch_frames_and_payloads_identical"]
        old_audio = {"OldLegacy": old["renders"][mid + "/IndependentMergedBaseline"]["audio"],
                     "OldOriginal": old["renders"][mid + "/Original"]["audio"]}
        for item in [m["events"], new["events"], new["event_index"], *old_audio.values()]:
            verify(item)
        maps.append({"id": mid, "offset_seconds": m["offset_seconds"], "scale": m["scale"],
                     "old_events": m["events"], "corrected_events": new["events"],
                     "corrected_index": new["event_index"], "old_audio": old_audio})
    sources = {"candidate": (Path(bound["source_directory"]), bound["source"]),
               "baseline": (old_dir / "baseline-source", bound["baseline_source"]["source_sha256"])}
    for folder, expected in sources.values():
        assert file_manifest(folder) == expected
    out.mkdir(parents=True)
    for name, (folder, _) in sources.items():
        shutil.copytree(folder, out / (name + "-source"))
    snapshots = out / "snapshots"
    snapshots.mkdir()
    for key, name in (("fixture", "AllocationSequence.cpp"), ("baseline_fixture", "BaselineMergedSequence.cpp")):
        shutil.copyfile(bound[key]["path"], snapshots / name)
    metrics = old_dir / "snapshots/stereo_metrics.py"
    assert sha(metrics) == bound["snapshots"]["stereo_metrics.py"]
    shutil.copyfile(metrics, snapshots / "stereo_metrics.py")
    shutil.copyfile(__file__, snapshots / "runner.py")
    shutil.copyfile(ROOT / "Tools/benchmark_pitch_model.py", snapshots / "common.py")
    design = {
        "schema": "press78.corrected-midi-allocation-comparison.v2", "frozen_at_utc": common.now(),
        "status": "Frozen before new compilation, rendering or scoring; independent source review required",
        "superseded_before_audio": record(ROOT / "build/midi-fixture-comparison-20261019/superseded-before-audio.json"),
        "v2_amendment": "Scope inherited timing metadata to Old cells and specify Corrected separately. Add complete final frozen-source/dependency revalidation. No changes to events, maps, controls, DSP, gates, metrics, windows or comparisons.",
        "runner": record(__file__), "common": record(ROOT / "Tools/benchmark_pitch_model.py"),
        "old_result": record(old_dir / "result.json"), "old_binding": record(old_dir / "candidate-bound.json"),
        "old_executables": [old["executable"], old["baseline_executable"]],
        "export_ledger": record(export_path), "export_review": export["independent_review"]["receipt"],
        "allocation_validation": bound["command_validation"],
        "program_loader_evidence": record(ROOT / "Docs/research/opu-mode00-program-load-validation-2026-10-19.json"),
        "known_recording_effect_state": record(ROOT / "Docs/research/recording-mode-effects-audit-2026-10-19.json"),
        "sources": {name: {"directory": str(out / (name + "-source")), "sha256": expected}
                    for name, (_, expected) in sources.items()},
        "snapshots": file_manifest(snapshots), "maps": maps, "windows": prior["windows"],
        "diagnostic_windows": prior["diagnostic_windows"], "render": prior["render"],
        "recording": prior["recording"], "bank": prior["bank"],
        "timing_and_metric": {
            "Old": prior["timing_and_metric"],
            "Corrected": {**prior["timing_and_metric"],
                          "note_mapping": "One frame for each raw MIDI tick using exact tempo-integrated source seconds: round(48000*(offset+scale*float(exact_seconds))). Both ON and actual OFF use that tick frame; no separately rounded gate.",
                          "event_order": "Patch rows first at a shared frame; notes retain canonical raw tick/track/within-track order, including mixed OFF/ON. No off-first category or pitch sort. Future-only patch snapshots are retained solely to isolate metadata."}},
        "required_gates": prior["required_gates"],
        "cells": list(NAMES),
        "contrasts": ["Original-Legacy separately under old and corrected fixtures",
                      "Corrected-old separately under each allocator",
                      "Interaction=(CorrectedOriginal-CorrectedLegacy)-(OldOriginal-OldLegacy)"],
        "analysis": "Every contrast for all4 primary metrics, all100 windows and both fixed Sine supports; retain absolute scores, means, per-voice deltas and every positive regression without epsilon. Old scores copied exactly from frozen result; new scores use its unchanged metric source.",
        "identity": "Corrected candidate-Legacy whole WAV must equal separately compiled unchanged b15 corrected baseline for all4 maps. Keep all original files; delete only the new candidate-Legacy duplicate after exact hash match.",
        "event_policy": "Read input lines in file order at equal frames, no sort. Raw channels0/1 both enter engine source0. Exactly1761ons/1761offs/100patches. Corrected source uses one frame per raw tick; original onset times and inferred program rows unchanged. Canonical track-index merge and program-first remain explicit unmeasured conventions, not recovered sender timing.",
        "program_policy": "setPatch(...,false) future-only snapshots retained in ALL four cells solely to isolate MIDI metadata. This omits verified780 serial-keyclear/pendingcancel and bothmodels all12slot rewrite. Neither chip live-parameter response nor panel-source association is assumed recovered.",
        "effects_limit": "Reverb+Chorus are visiblyON in sampled exact-tour frames. Recorded chorus is unchanged; chip-Reverb envelope law remains missing. No original key-service/phase/retrigger response is recovered here.",
        "decision_scope": "Apply the old numerical audio bounds unchanged to CorrectedOriginal-CorrectedLegacy, but no automatic promotion even if they pass. Metadata conformance is required independently of score direction. Past failed gates remain failed; no physical law or best-on-market claim follows.",
        "auditions": "Exactly20 five-part clips: Hardware/OldLegacy/OldOriginal/CorrectedLegacy/CorrectedOriginal for focus65/93/97 and Sine199/200 across4maps. Fixed250ms gaps. One RMS scalar per model stereo pair; common safety perwindow across allmaps/cells, ceiling0.9. No EQ/pitch/phase/time/channelgain/peak normalization fit.",
        "maximum_new_wav_bytes": 800000000,
        "storage": "Retain4 corrected baseline and4 corrected Original WAVs plus20auditions. Candidate-Legacy deleted only after complete independent baseline hash equality; preserve every mismatch and all old data.",
        "no_production_changes": True, "no_new_fit": True, "no_artificial_noise": True,
    }
    assert len(design["windows"]) == 100 and [w["patch"] for w in design["windows"]] == list(range(100))
    assert [w["patch"] for w in design["diagnostic_windows"]] == [199, 200]
    write(out / "design-frozen.json", design)
    print(json.dumps(record(out / "design-frozen.json"), indent=2))


def validate_scores(values):
    optional = {"reference_side_mid_db", "model_side_mid_db", "side_mid_error_db"}
    expected = set(METRICS) | optional | {"reference_right_left_db", "model_right_left_db", "one_pair_gain_db"}
    assert set(values) == expected
    assert all((v is None and k in optional) or (v is not None and np.isfinite(v)) for k, v in values.items())


def make_auditions(out, design, reference, models):
    folder = out / "auditions"
    folder.mkdir()
    rows, html = [], ['<!doctype html><meta charset="utf-8"><title>MIDI fixture comparison</title>',
                     '<h1>Hardware / Old Legacy / Old Original / Corrected Legacy / Corrected Original</h1>',
                     '<p>Fixed supports/maps, shared listening safety. Original program loading and chip-Reverb response remain unmodeled.</p>']
    for patch in (*FOCUS, 199, 200):
        w = next(w for w in design["windows"] + design["diagnostic_windows"] if w["patch"] == patch)
        a, z = round(w["start_seconds"] * SR), round(w["end_seconds"] * SR)
        hardware = reference[a:z].astype(float) / 32768
        rms, normalized, gains = float(np.sqrt(np.mean(hardware * hardware))), {}, {}
        for mid in MAPS:
            normalized[mid], gains[mid] = {}, {}
            for name in NAMES:
                x = models[mid][name][a:z].astype(float)
                power = float(np.sqrt(np.mean(x * x)))
                assert power > 0
                gain = rms / power
                normalized[mid][name], gains[mid][name] = x * gain, gain
        peak = max(float(np.max(np.abs(hardware))), *(float(np.max(np.abs(x))) for group in normalized.values() for x in group.values()))
        safety = min(1., .9 / max(peak, 1e-12))
        for mid in MAPS:
            parts = [hardware]
            for name in NAMES:
                parts.extend((np.zeros((SR // 4, 2)), normalized[mid][name]))
            audio = np.concatenate(parts) * safety
            assert np.isfinite(audio).all() and np.max(np.abs(audio)) <= .900001
            path = folder / f"{patch:02d}-{mid}.wav"
            wavfile.write(path, SR, audio.astype(np.float32))
            rows.append({"patch": patch, "map": mid, "audio": record(path), "pair_gains": gains[mid],
                         "common_window_safety_gain": safety, "peak": float(np.max(np.abs(audio)))})
            html.append(f'<h2>{w["name"]} — {mid}</h2><audio controls src="auditions/{path.name}"></audio>')
    (out / "audition.html").write_text("\n".join(html))
    return rows


def run(args):
    out = fresh_output(args.output)
    assert not (out / "run-started.json").exists(), "Do not rerun failed/completed experiments"
    design = read(out / "design-frozen.json")
    assert design["schema"] == "press78.corrected-midi-allocation-comparison.v2"
    review = read(args.review)
    assert review["schema"] == "press78.corrected-midi-audio-source-review.v1" and review["passed"]
    assert review["design_sha256"] == sha(out / "design-frozen.json")
    assert review["runner_sha256"] == sha(__file__)
    for item in review["artifacts"]:
        verify(item)
    for key in ("runner", "common", "old_result", "old_binding", "export_ledger", "export_review",
                "allocation_validation", "program_loader_evidence", "known_recording_effect_state", "recording", "bank", "superseded_before_audio"):
        verify(design[key])
    for item in design["old_executables"]:
        verify(item)
    for name, digest in design["snapshots"].items():
        assert sha(out / "snapshots" / name) == digest
    for item in design["sources"].values():
        assert file_manifest(Path(item["directory"])) == item["sha256"]
    for m in design["maps"]:
        for item in [m["old_events"], m["corrected_events"], m["corrected_index"], *m["old_audio"].values()]:
            verify(item)
    write(out / "run-started.json", {"utc": common.now(), "design": record(out / "design-frozen.json"), "source_review": record(args.review)})
    compilations = {}
    for name, fixture in (("candidate", "AllocationSequence.cpp"), ("baseline", "BaselineMergedSequence.cpp")):
        source, exe = Path(design["sources"][name]["directory"]), out / (name + "_sequence")
        command = ["c++", "-std=c++17", "-O2", "-I", str(source), str(out / "snapshots" / fixture), str(source / "Press78Engine.cpp"), "-o", str(exe)]
        p = subprocess.run(command, check=True, capture_output=True, text=True)
        compilations[name] = {"command": command, "stdout": p.stdout, "stderr": p.stderr, "executable": record(exe)}
    rate, reference = wavfile.read(design["recording"]["path"], mmap=True)
    assert rate == SR and reference.dtype == np.int16 and reference.shape[1] == 2
    old, models, renders, max_bytes = read(design["old_result"]["path"]), {}, {}, 0
    def load_model(path):
        rate, data = wavfile.read(path, mmap=True)
        assert rate == SR and data.shape == (design["render"]["frames"], 2) and np.isfinite(data).all()
        aligned = data[32:32 + len(reference)]
        assert aligned.shape == reference.shape
        return aligned
    for m in design["maps"]:
        mid = m["id"]
        folder = out / "maps" / mid
        folder.mkdir(parents=True)
        models[mid] = {name: load_model(item["path"]) for name, item in m["old_audio"].items()}
        baseline_record = None
        for name, binary, law in (("IndependentCorrectedBaseline", "baseline", None),
                                  ("CorrectedLegacy", "candidate", 1), ("CorrectedOriginal", "candidate", 2)):
            audio, pressure = folder / (name + ".wav"), folder / (name + "-pressure.csv")
            command = [compilations[binary]["executable"]["path"], m["corrected_events"]["path"], str(audio), str(design["render"]["frames"]), str(SR), "recorded", str(pressure)]
            if law is not None:
                command.append(str(law))
            p = subprocess.run(command, check=True, capture_output=True, text=True)
            detail = json.loads(p.stdout)
            assert detail["events"] == 3622 and detail["latency_samples"] == 32 and detail["frames"] == design["render"]["frames"]
            data = load_model(audio)
            artifact = record(audio)
            row = {"command": command, "render": detail, "audio": artifact, "pressure": record(pressure)}
            max_bytes = max(max_bytes, sum(p.stat().st_size for p in out.rglob("*.wav")))
            assert max_bytes < design["maximum_new_wav_bytes"]
            if name == "IndependentCorrectedBaseline":
                baseline_record = artifact
            elif name == "CorrectedLegacy":
                assert artifact["sha256"] == baseline_record["sha256"], "Keep mismatch WAV"
                del data
                audio.unlink()
                row["deleted_after_whole_wav_equality"] = baseline_record
                models[mid][name] = load_model(baseline_record["path"])
            else:
                models[mid][name] = data
            renders[mid + "/" + name] = row
            write(out / "render-progress.json", renders)
            print("Rendered", mid, name, flush=True)
    spec = importlib.util.spec_from_file_location("frozen_midi_fixture_metrics", out / "snapshots/stereo_metrics.py")
    metric = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metric)
    rows = []
    for index, w in enumerate(design["windows"] + design["diagnostic_windows"]):
        a, z = round(w["start_seconds"] * SR), round(w["end_seconds"] * SR)
        observed = reference[a:z].astype(float) / 32768
        prior = old["rows"][index]
        assert all(prior[k] == v for k, v in w.items())
        scores, alloc, fixture, interaction = {}, {}, {}, {}
        for mid in MAPS:
            scores[mid] = {"OldLegacy": prior["scores"][mid]["Legacy"], "OldOriginal": prior["scores"][mid]["Original"]}
            for name in NAMES[2:]:
                scores[mid][name] = metric.stereo_compare(observed, models[mid][name][a:z], SR)
            for values in scores[mid].values():
                validate_scores(values)
            alloc[mid] = {epoch: {k: scores[mid][epoch + "Original"][k] - scores[mid][epoch + "Legacy"][k] for k in METRICS} for epoch in ("Old", "Corrected")}
            fixture[mid] = {law: {k: scores[mid]["Corrected" + law][k] - scores[mid]["Old" + law][k] for k in METRICS} for law in ("Legacy", "Original")}
            interaction[mid] = {k: alloc[mid]["Corrected"][k] - alloc[mid]["Old"][k] for k in METRICS}
            assert alloc[mid]["Old"] == prior["original_minus_legacy"][mid]
        rows.append({**w, "scores": scores, "original_minus_legacy": alloc, "corrected_minus_old": fixture, "allocation_effect_change": interaction})
        if len(rows) % 10 == 0:
            print("Scored", len(rows), "windows", flush=True)
    groups = {"all100": list(range(100)), "focus": list(FOCUS), "neighbors": [64, 66, 92, 94, 96, 98]}
    aggregate = {group: {mid: {name: {k: float(np.mean([r["scores"][mid][name][k] for r in rows if r["patch"] in patches])) for k in METRICS} for name in NAMES} for mid in MAPS} for group, patches in groups.items()}
    regressions = {mid: {k: [{"patch": r["patch"], "delta": r["original_minus_legacy"][mid]["Corrected"][k]} for r in rows if r["original_minus_legacy"][mid]["Corrected"][k] > 0] for k in METRICS} for mid in MAPS}
    limits = design["required_gates"]
    def delta(mid, key):
        return aggregate["all100"][mid]["CorrectedOriginal"][key] - aggregate["all100"][mid]["CorrectedLegacy"][key]
    gates = {
        "corrected_legacy_all4_independent_baselines_identical": True,
        "unchanged_map_band_improvement": delta("unchanged", "joint_lr_band_rmse_db") <= limits["unchanged_map_all100_joint_band_delta_max_db"],
        "other_maps_band_bounds": all(delta(mid, "joint_lr_band_rmse_db") <= limits["other_maps_all100_joint_band_delta_max_db"] for mid in MAPS[1:]),
        "each_focus_each_map_band_bounds": all(r["original_minus_legacy"][mid]["Corrected"]["joint_lr_band_rmse_db"] <= limits["each_focus_each_map_joint_band_delta_max_db"] for r in rows if r["patch"] in FOCUS for mid in MAPS),
        "all_maps_STFT_log_bounds": all(delta(mid, "stereo_stft_log_error_db") <= limits["all_maps_all100_STFTlog_delta_max_db"] for mid in MAPS),
        "all_sine_diagnostics_each_map_band_bounds": all(r["original_minus_legacy"][mid]["Corrected"]["joint_lr_band_rmse_db"] <= limits["each_sine_diagnostic_each_map_band_delta_max_db"] for r in rows if r["patch"] in (199, 200) for mid in MAPS),
    }
    auditions = make_auditions(out, design, reference, models)
    max_bytes = max(max_bytes, sum(p.stat().st_size for p in out.rglob("*.wav")))
    assert max_bytes < design["maximum_new_wav_bytes"]
    for key in ("runner", "common", "old_result", "old_binding", "export_ledger", "export_review",
                "allocation_validation", "program_loader_evidence", "known_recording_effect_state", "recording", "bank", "superseded_before_audio"):
        verify(design[key])
    for item in [*design["old_executables"], *review["artifacts"]]:
        verify(item)
    for name, digest in design["snapshots"].items():
        assert sha(out / "snapshots" / name) == digest
    for item in design["sources"].values():
        assert file_manifest(Path(item["directory"])) == item["sha256"]
    for m in design["maps"]:
        for item in [m["old_events"], m["corrected_events"], m["corrected_index"], *m["old_audio"].values()]:
            verify(item)
    result = {"schema": design["schema"], "design": record(out / "design-frozen.json"), "protocol": design,
              "source_review": record(args.review), "compilations": compilations, "renders": renders, "rows": rows,
              "aggregate": aggregate, "regressions": regressions, "audio_gates": gates, "audio_gates_passed": all(gates.values()),
              "old_audio_gates_preserved": old["audio_gates"], "old_audio_gates_passed": old["audio_gates_passed"],
              "auditions": auditions, "maximum_new_wav_bytes": max_bytes,
              "no_new_fit": True, "no_production_changes": True, "no_artificial_noise": True,
              "decision_scope": design["decision_scope"]}
    write(out / "result.json", result)
    print(json.dumps({"result": str(out / "result.json"), "audio_gates": gates, "passed": all(gates.values())}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "run"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review", type=Path)
    args = parser.parse_args()
    if args.action == "run" and args.review is None:
        parser.error("run requires --review")
    try:
        globals()[args.action](args)
    except Exception:
        out = fresh_output(args.output)
        if out.exists():
            failure = out / "failure.json"
            if not failure.exists():
                write(failure, {"utc": common.now(), "action": args.action, "error": traceback.format_exc()})
        raise


if __name__ == "__main__":
    main()
