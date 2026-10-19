#!/usr/bin/env python3
"""Fixed original-allocation experiment; requires retained local research inputs.

Freeze the design, then bind the candidate and runner before recording renders.
Neither stage edits production DSP or fits model parameters. Three lanes separate
historical MIDI-channel owner tags from one hardware Mode00 MIDI domain.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import shutil
import subprocess
import time

import numpy as np
from scipy.io import wavfile
import benchmark_pitch_model as common

ROOT = Path(__file__).resolve().parents[1]
SR = 48000
MAPS = common.MAPS
METRICS = common.METRICS
FOCUS = common.FOCUS
LAWS = {"HistoricalLegacy": 0, "Legacy": 1, "Original": 2}
sha, read, write, record, verify = common.sha, common.read, common.write, common.record, common.verify


def validate_scores(values):
    optional = {"reference_side_mid_db", "model_side_mid_db", "side_mid_error_db"}
    expected = set(METRICS) | optional | {"reference_right_left_db", "model_right_left_db", "one_pair_gain_db"}
    assert set(values) == expected
    assert all((value is None and key in optional) or (value is not None and np.isfinite(value))
               for key, value in values.items())


def freeze(args):
    out = args.output.resolve()
    assert not out.exists(), "Use a fresh directory; keep superseded protocols"
    previous = ROOT / "build/key-level-b13-20261019/design-frozen-v2.json"
    prior = read(previous)
    assert sha(prior["baseline"]["prior_b12_result"]) == prior["baseline"]["prior_result_sha256"]
    policy_path = ROOT / "build/opu-allocation-mode00-channels-20261019/review.json"
    policy = read(policy_path)
    assert policy["schema"] == "press78.independent-mode00-channel-review.v1" and policy["passed"]
    for artifact in policy["evidence"]:
        verify(artifact)
    for model in ("PSS780", "PSS680"):
        shared = next(r["observed"] for r in policy["rows"] if r["model"] == model and r["mask"] == 3 and r["scenario"] == "shared-same-pitch")
        cached = next(r["observed"] for r in policy["rows"] if r["model"] == model and r["mask"] == 3 and r["scenario"] == "cross-channel-cache")
        assert shared["shared_byte_24c5_after_wire"] == [1,1,0,0]
        assert shared["pitch_slots"] == [[0],[],[],[]]
        assert cached["pitch_slots"] == [[0],[],[1],[],[0]]
    counts = {}
    for m in prior["maps"]:
        verify(m["events"])
        verify(m["expected_legacy_audio"])
        counts[m["id"]] = {"on": {0: 0, 1: 0}, "off": {0: 0, 1: 0}, "patch": 0}
        for line in Path(m["events"]["path"]).read_text().splitlines():
            x = line.split()
            if x[1] == "patch": counts[m["id"]]["patch"] += 1
            else:
                assert int(x[-1]) in (0,1)
                counts[m["id"]][x[1]][int(x[-1])] += 1
        assert counts[m["id"]] == {"on": {0:842,1:919}, "off": {0:842,1:919}, "patch":100}
    verify(prior["recording"])
    verify(prior["bank"])
    out.mkdir(parents=True)
    baseline = out / "baseline-source"
    shutil.copytree(ROOT / "Source/DSP", baseline)
    manifest = out / "baseline-source-frozen.json"
    write(manifest, {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                     "source_sha256": {p.name: sha(p) for p in baseline.iterdir() if p.is_file()},
                     "scope": "Current b15 shipping DSP before allocator candidate audio"})
    design = {"schema": "press78.original-allocation-recording-protocol.v3",
              "frozen_at_utc": common.now(), "status": "Before candidate recording renders, scores or fitting",
              "frozen_runner": record(Path(__file__)), "frozen_common": record(ROOT / "Tools/benchmark_pitch_model.py"),
              "superseded": record(ROOT / "build/allocator-recording-comparison-v2-20261019/superseded-before-render.json"),
              "prior_source_policy_correction": record(ROOT / "build/allocator-recording-comparison-20261019/superseded-before-render.json"),
              "v3_amendment": "Before binding/audio: allow only the existing three optional width diagnostics to be null; all primary metrics and remaining diagnostics must be finite. Correct deletion receipt identity wording. No source/timing/window/metric/gate changes.",
              "baseline": {**prior["baseline"], "source_manifest": str(manifest), "sha256": sha(manifest)},
              "prior_design": record(previous), "maps": prior["maps"], "windows": prior["windows"],
              "recording": prior["recording"], "bank": prior["bank"], "render": prior["render"],
              "timing_and_metric": prior["timing_and_metric"],
              "source_policy": {"evidence": record(policy_path), "counts": counts,
                  "HistoricalLegacy": "Original file MIDI-channel IDs0/1 remain engine source IDs0/1; historical reproduction only, not a CV capture.",
                  "Legacy": "All accepted raw MIDI channels enter one engine source0 domain; allocationModel0. Independently compiled unchanged b15 source must reproduce each complete merged Legacy WAV.",
                  "Original": "Exactly the same global MIDI domain/source0, allocationModel1. Original-minus-Legacy isolates allocation from source mapping.",
                  "unchanged": "No input event is deleted, reordered, retimed, repitched or re-velocitized. Raw channel metadata stays in the event file/pressure log; the fixture changes only the API owner argument for merged lanes.",
                  "scope": "Original Mode00 CPU witnesses support one received-key bitmap across enabled MIDI channels. Actual sender delivery/filtering remains conditional. Plugin MIDI/CV owners remain separate in normal host use."},
              "diagnostic_windows": [
                  {"patch":199,"name":"Sine99 full ending","start_seconds":176.1,"end_seconds":184.2},
                  {"patch":200,"name":"Sine99 prior primary repeated75","start_seconds":181.55,"end_seconds":182.20}],
              "diagnostic_selection": "Fixed before candidate audio, from prior Sine99 retrigger evidence. These reused-source supports do not establish actual gate arrival, phase or an independent holdout.",
              "changed_path": "Optional Original normalMode00 allocator with disclosed host extensions. No EG, phase reset, CPU-service period, pitch, level, waveform, Reverb, analog, DAC, clock or noise fit. The historical channel-owner mapping is separated as a third lane; CV is not simulated as MIDI-channel1.",
              "required_gates": {"historical_legacy_all4_fullWAV_hash_equality": True,
                  "merged_legacy_all4_independent_baseline_fullWAV_equality": True,
                  "unchanged_map_all100_joint_band_delta_max_db": -0.01,
                  "other_maps_all100_joint_band_delta_max_db": 0.03,
                  "each_focus_each_map_joint_band_delta_max_db": 0.10,
                  "all_maps_all100_STFTlog_delta_max_db": 0.05,
                  "each_sine_diagnostic_each_map_band_delta_max_db": 0.10},
              "decision_scope": "Regression gates for default promotion, not a definition of physical truth. Preserve every failed outcome and the candidate; no moving gates or fitting source/map/gain/time/phase to force a pass. Command evidence remains valid if its audio embedding fails.",
              "analysis": "All100 patches x4maps x3lanes plus both Sine supports. Report Original-minus-mergedLegacy and mergedLegacy-minus-historical separately. Retain all metrics/regressions/focus/neighbors and20 four-part auditions. Native/CPU/SDK/host and independent acoustic evidence remain separate.",
              "auditions": "Hardware/HistoricalLegacy/mergedLegacy/Original, fixed windows. Established one RMS gain per stereo model pair plus common safety across maps/lanes; no EQ/time/phase/pitch/channel-gain fitting.",
              "maximum_new_wav_bytes":800000000,
              "storage": "At most four merged b15 baseline WAVs plus four Original WAVs and auditions; delete candidate Legacy copies only after exact independent hash identity and historical copies only after their exact retained hashes. Preserve mismatches. Limit raised prospectively from superseded v1 because the independent merged baseline is now retained.",
              "limits": ["Reused exact-device tour; sender timing, capture dynamics and chip behavior remain unidentified.",
                  "All velocities127/noCC64; not a velocity or pedal measurement.",
                  "Passing reused-recording gates cannot establish market-leading accuracy or complete chip emulation."]}
    write(out / "design-frozen.json", design)
    print(json.dumps(record(out / "design-frozen.json"), indent=2))


def bind(args):
    out = args.output.resolve()
    design_path = out / "design-frozen.json"
    design = read(design_path)
    assert not (out / "candidate-bound.json").exists(), "Candidate already bound"
    assert design["schema"] == "press78.original-allocation-recording-protocol.v3", "Superseded protocol"
    verify(design["frozen_runner"])
    verify(design["frozen_common"])
    verify(design["source_policy"]["evidence"])
    prior_path = Path(design["baseline"]["prior_b12_result"])
    assert sha(prior_path) == design["baseline"]["prior_result_sha256"]
    assert sha(design["baseline"]["source_manifest"]) == design["baseline"]["sha256"]
    prior = read(prior_path)
    assert len(design["windows"]) == 100 and tuple(m["id"] for m in design["maps"]) == MAPS
    for m in design["maps"]:
        verify(m["events"])
        verify(m["expected_legacy_audio"])
        assert m["expected_legacy_audio"]["sha256"] == prior["renders"][m["id"] + "/Original"]["audio"]["sha256"]
    verify(design["recording"])
    verify(design["bank"])
    evidence = read(args.command_validation)
    assert evidence["schema"] == "press78.allocator-candidate-review.v1"
    assert evidence["passed"], "Independent allocation review required"
    required = ("mode00_command_reference", "legacy_audio_compatibility", "host_source_ownership",
                "polyphony_reset_mode_handover", "render_event_no_allocations")
    assert set(evidence["requirements"]) == set(required)
    assert all(evidence["requirements"].values())
    for artifact in evidence["artifacts"]:
        verify(artifact)
    source = out / "candidate-source"
    shutil.copytree(args.source.resolve(), source)
    assert {p.name: sha(p) for p in source.iterdir() if p.is_file()} == evidence["source_sha256"], "Review belongs to another candidate"
    snapshots = out / "snapshots"
    snapshots.mkdir()
    old = prior_path.parent
    for name in ("stereo_metrics.py", "HardwareSequencePressure.cpp"):
        p = old / "snapshots" / name
        assert sha(p) == prior["protocol"]["snapshots"][name]
        shutil.copyfile(p, snapshots / name)
    original_fixture = (snapshots / "HardwareSequencePressure.cpp").read_text()
    def mapped_fixture(candidate):
        fixture = original_fixture
        needle = "press78::Controls c;c.masterGain=1.;"
        assert fixture.count(needle) == 1
        controls = "press78::Controls c;c.pitchModel=1;c.sustainMode=1;c.midiPitchBend=-1;"
        if candidate:
            controls += "c.allocationModel=std::stoi(argv[7])==2?1:0;"
            assert fixture.count("if(argc!=7)") == 1
            fixture = fixture.replace("if(argc!=7)","if(argc!=8)")
        controls += "c.masterGain=1.;"
        fixture = fixture.replace(needle,controls)
        point = "const int rate=std::stoi(argv[4]);const std::string mode=argv[5];"
        assert fixture.count(point) == 1
        declaration = "const bool historicalSources=std::stoi(argv[7])==0;" if candidate else "const bool historicalSources=false;"
        fixture = fixture.replace(point,point+declaration)
        for old,new in (("engine->noteOn(x.note,x.velocity,x.source)","engine->noteOn(x.note,x.velocity,historicalSources?x.source:0)"),
                        ("engine->noteOff(x.note,x.source)","engine->noteOff(x.note,historicalSources?x.source:0)"),
                        ("source,active_before","input_midi_channel,engine_source,active_before"),
                        ('<<x.source<<","<<before','<<x.source<<","<<(historicalSources?x.source:0)<<","<<before'),
                        ("eligible,oldest_replacement","legacy_TL_AR_gate,legacy_oldest_condition")):
            assert fixture.count(old)==1,old
            fixture=fixture.replace(old,new)
        return fixture
    (out / "AllocationSequence.cpp").write_text(mapped_fixture(True))
    (out / "BaselineMergedSequence.cpp").write_text(mapped_fixture(False))
    baseline = out / "baseline-source"
    baseline_manifest = read(design["baseline"]["source_manifest"])
    assert {p.name:sha(p) for p in baseline.iterdir() if p.is_file()} == baseline_manifest["source_sha256"]
    shutil.copyfile(Path(__file__), snapshots / "runner-bound.py")
    shutil.copyfile(ROOT / "Tools/benchmark_pitch_model.py", snapshots / "common-bound.py")
    bound = {
        "design": record(design_path), "bound_at_utc": common.now(),
        "source": {p.name: sha(p) for p in source.iterdir() if p.is_file()},
        "source_directory": str(source), "fixture": record(out / "AllocationSequence.cpp"),
        "baseline_fixture": record(out / "BaselineMergedSequence.cpp"), "baseline_source": baseline_manifest,
        "runner": record(Path(__file__)), "common_module": record(ROOT / "Tools/benchmark_pitch_model.py"),
        "command_validation": record(args.command_validation),
        "snapshots": {p.name: sha(p) for p in snapshots.iterdir()},
        "status": "Candidate and runner bound before compilation/rendering; no measurements",
    }
    write(out / "candidate-bound.json", bound)
    print(json.dumps({"bound": str(out / "candidate-bound.json"), "sha256": sha(out / "candidate-bound.json")}, indent=2))


def auditions(out, design, reference, models):
    destination = out / "auditions"
    destination.mkdir()
    rows = []
    html = ['<!doctype html><meta charset="utf-8"><title>Allocation comparison</title>',
            '<h1>Hardware → Historical → Merged Legacy → Original allocation</h1>',
            '<p>Fixed windows/maps. One RMS gain per model stereo pair; common safety gain per voice. No EQ, timing or pitch fit.</p>']
    for patch in list(FOCUS) + [w["patch"] for w in design["diagnostic_windows"]]:
        w = next(w for w in design["windows"] + design["diagnostic_windows"] if w["patch"] == patch)
        a, z = round(w["start_seconds"] * SR), round(w["end_seconds"] * SR)
        hardware = reference[a:z].astype(float) / 32768
        rms = float(np.sqrt(np.mean(hardware * hardware)))
        normalized, gains = {}, {}
        for mid in MAPS:
            normalized[mid], gains[mid] = {}, {}
            for name in LAWS:
                x = models[mid][name][a:z].astype(float)
                power = float(np.sqrt(np.mean(x * x)))
                assert power > 0
                gain = rms / power
                normalized[mid][name], gains[mid][name] = x * gain, gain
        peak = max(float(np.max(np.abs(hardware))), *(float(np.max(np.abs(x))) for group in normalized.values() for x in group.values()))
        safety = min(1., .9 / max(peak, 1e-12))
        for mid in MAPS:
            gap = np.zeros((SR // 4, 2))
            audio = np.concatenate((hardware, gap, normalized[mid]["HistoricalLegacy"], gap, normalized[mid]["Legacy"], gap, normalized[mid]["Original"])) * safety
            assert np.isfinite(audio).all() and np.max(np.abs(audio)) <= .900001
            p = destination / f"{patch:02d}-{mid}-hardware-legacy-original.wav"
            wavfile.write(p, SR, audio.astype(np.float32))
            rows.append({"patch": patch, "map": mid, "audio": record(p), "pair_gains": gains[mid],
                         "common_focus_safety_gain": safety, "peak": float(np.max(np.abs(audio)))})
            html.append(f'<h2>{w["name"]} — {mid}</h2><audio controls src="auditions/{p.name}"></audio>')
    (out / "audition.html").write_text("\n".join(html))
    return rows


def run(args):
    out = args.output.resolve()
    bound = read(out / "candidate-bound.json")
    assert not (out / "run-started.json").exists(), "Keep completed/failed runs; use a fresh experiment"
    for key in ("design", "fixture", "baseline_fixture", "runner", "common_module", "command_validation"):
        verify(bound[key])
    for name, h in bound["snapshots"].items():
        assert sha(out / "snapshots" / name) == h
    design = read(bound["design"]["path"])
    source = Path(bound["source_directory"])
    assert {p.name: sha(p) for p in source.iterdir() if p.is_file()} == bound["source"]
    assert sha(design["baseline"]["prior_b12_result"]) == design["baseline"]["prior_result_sha256"]
    verify(design["recording"])
    verify(design["bank"])
    verify(design["frozen_runner"])
    verify(design["frozen_common"])
    verify(design["source_policy"]["evidence"])
    baseline = out / "baseline-source"
    assert {p.name:sha(p) for p in baseline.iterdir() if p.is_file()} == bound["baseline_source"]["source_sha256"]
    write(out / "run-started.json", {"utc": common.now(), "candidate_binding_sha256": sha(out / "candidate-bound.json")})
    exe = out / "allocation_sequence"
    command = ["c++", "-std=c++17", "-O2", "-I", str(source), str(out / "AllocationSequence.cpp"),
               str(source / "Press78Engine.cpp"), "-o", str(exe)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    baseline_exe = out / "baseline_merged_sequence"
    baseline_command = ["c++","-std=c++17","-O2","-I",str(baseline),str(out / "BaselineMergedSequence.cpp"),str(baseline / "Press78Engine.cpp"),"-o",str(baseline_exe)]
    subprocess.run(baseline_command,check=True,capture_output=True,text=True)
    rate, reference = wavfile.read(design["recording"]["path"], mmap=True)
    assert rate == SR and reference.dtype == np.int16 and reference.shape[1] == 2
    models, renders, maximum_bytes = {}, {}, 0
    for m in design["maps"]:
        verify(m["events"])
        verify(m["expected_legacy_audio"])
        folder = out / "maps" / m["id"]
        folder.mkdir(parents=True)
        models[m["id"]] = {}
        baseline_audio, baseline_pressure = folder / "BaselineMerged.wav", folder / "BaselineMerged-pressure.csv"
        baseline_cmd = [str(baseline_exe),m["events"]["path"],str(baseline_audio),str(design["render"]["frames"]),str(SR),"recorded",str(baseline_pressure)]
        baseline_run = subprocess.run(baseline_cmd,check=True,capture_output=True,text=True)
        baseline_detail=json.loads(baseline_run.stdout)
        baseline_sr,baseline_data=wavfile.read(baseline_audio,mmap=True)
        assert baseline_sr==SR and baseline_data.shape==(design["render"]["frames"],2) and np.isfinite(baseline_data).all()
        assert baseline_detail["events"]==3622 and baseline_detail["latency_samples"]==32
        baseline_record=record(baseline_audio)
        renders[m["id"]+"/IndependentMergedBaseline"]={"command":baseline_cmd,"render":baseline_detail,"audio":baseline_record,"pressure":record(baseline_pressure)}
        for name, law in LAWS.items():
            audio, pressure = folder / (name + ".wav"), folder / (name + "-pressure.csv")
            cmd = [str(exe), m["events"]["path"], str(audio), str(design["render"]["frames"]),
                   str(SR), "recorded", str(pressure), str(law)]
            started = time.perf_counter()
            p = subprocess.run(cmd, check=True, capture_output=True, text=True)
            detail = json.loads(p.stdout)
            detail["wall_seconds"] = time.perf_counter() - started
            sr, data = wavfile.read(audio, mmap=True)
            assert sr == SR and data.shape == (design["render"]["frames"], 2) and np.isfinite(data).all()
            assert detail["events"] == 3622 and detail["latency_samples"] == 32
            artifact = {**record(audio), "frames": len(data), "peak": float(np.max(np.abs(data)))}
            size = sum(p.stat().st_size for p in out.rglob("*.wav"))
            maximum_bytes = max(maximum_bytes, size)
            assert size < design["maximum_new_wav_bytes"]
            result = {"command": cmd, "render": detail, "audio": artifact, "pressure": record(pressure)}
            if name in ("HistoricalLegacy", "Legacy"):
                target = m["expected_legacy_audio"] if name == "HistoricalLegacy" else baseline_record
                assert artifact["sha256"] == target["sha256"], f"Keep mismatch WAV; {name} whole-WAV identity failed"
                del data
                audio.unlink()
                result["deleted_only_after_exact_target_hash_match"] = record(Path(target["path"]))
                result["identity_target"] = "retained_historical_WAV" if name == "HistoricalLegacy" else "independently_compiled_merged_b15_WAV"
                _, data = wavfile.read(target["path"], mmap=True)
            models[m["id"]][name] = data[32:32 + len(reference)]
            assert models[m["id"]][name].shape == reference.shape
            renders[m["id"] + "/" + name] = result
            write(out / "render-progress.json", renders)
            print("Rendered", m["id"], name, flush=True)
    spec = importlib.util.spec_from_file_location("fixed_allocation_metrics", out / "snapshots/stereo_metrics.py")
    metric = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metric)
    rows = []
    for w in design["windows"] + design["diagnostic_windows"]:
        a, z = round(w["start_seconds"] * SR), round(w["end_seconds"] * SR)
        observed = reference[a:z].astype(float) / 32768
        scores = {mid: {name: metric.stereo_compare(observed, models[mid][name][a:z], SR) for name in LAWS} for mid in MAPS}
        delta = {mid: {key: scores[mid]["Original"][key] - scores[mid]["Legacy"][key] for key in METRICS} for mid in MAPS}
        policy_delta = {mid:{key:scores[mid]["Legacy"][key]-scores[mid]["HistoricalLegacy"][key] for key in METRICS} for mid in MAPS}
        for group in scores.values():
            for values in group.values():
                validate_scores(values)
        rows.append({**w, "scores": scores, "original_minus_legacy": delta, "merged_legacy_minus_historical": policy_delta})
        if len(rows) % 10 == 0:
            print("Scored", len(rows), "windows", flush=True)
    groups = {"all100": list(range(100)), "focus": list(FOCUS), "neighbors": [64, 66, 92, 94, 96, 98]}
    aggregate = {group: {mid: {name: {key: float(np.mean([r["scores"][mid][name][key] for r in rows if r["patch"] in patches]))
                                     for key in METRICS} for name in LAWS} for mid in MAPS} for group, patches in groups.items()}
    regressions = {mid: {key: [{"patch": r["patch"], "delta": r["original_minus_legacy"][mid][key]}
                              for r in rows if r["original_minus_legacy"][mid][key] > 0] for key in METRICS} for mid in MAPS}
    diagnostic_rows = [r for r in rows if r["patch"] not in range(100)]
    limits = design["required_gates"]
    def mean_delta(mid, key):
        return aggregate["all100"][mid]["Original"][key] - aggregate["all100"][mid]["Legacy"][key]
    gates = {
        "historical_legacy_all4_retained_WAVs_identical": True,
        "merged_legacy_all4_independent_baselines_identical": True,
        "unchanged_map_band_improvement": mean_delta("unchanged", "joint_lr_band_rmse_db") <= limits["unchanged_map_all100_joint_band_delta_max_db"],
        "other_maps_band_bounds": all(mean_delta(mid, "joint_lr_band_rmse_db") <= limits["other_maps_all100_joint_band_delta_max_db"] for mid in MAPS[1:]),
        "each_focus_each_map_band_bounds": all(r["original_minus_legacy"][mid]["joint_lr_band_rmse_db"] <= limits["each_focus_each_map_joint_band_delta_max_db"] for r in rows if r["patch"] in FOCUS for mid in MAPS),
        "all_maps_STFT_log_bounds": all(mean_delta(mid, "stereo_stft_log_error_db") <= limits["all_maps_all100_STFTlog_delta_max_db"] for mid in MAPS),
        "all_sine_diagnostics_each_map_band_bounds": all(r["original_minus_legacy"][mid]["joint_lr_band_rmse_db"] <= limits["each_sine_diagnostic_each_map_band_delta_max_db"] for r in diagnostic_rows for mid in MAPS),
    }
    clips = auditions(out, design, reference, models)
    maximum_bytes = max(maximum_bytes, sum(p.stat().st_size for p in out.rglob("*.wav")))
    assert maximum_bytes < design["maximum_new_wav_bytes"]
    result = {"schema": design["schema"], "protocol": design, "design": bound["design"],
              "candidate_binding": record(out / "candidate-bound.json"), "candidate_source_sha256": bound["source"],
              "compile_command": command, "executable": record(exe),
              "baseline_compile_command": baseline_command,"baseline_executable":record(baseline_exe), "renders": renders, "rows": rows,
              "aggregate": aggregate, "regressions": regressions, "audio_gates": gates,
              "audio_gates_passed": all(gates.values()), "auditions": clips, "maximum_new_wav_bytes": maximum_bytes,
              "external_gates": "Independent command equivalence/core/wrapper/CPU/SDK/host checks remain separate; no automatic adoption",
              "no_new_fit": True, "no_artificial_noise": True}
    write(out / "result.json", result)
    print(json.dumps({"result": str(out / "result.json"), "audio_gates": gates, "audio_gates_passed": all(gates.values())}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "bind", "run"))
    parser.add_argument("--output", type=Path, default=ROOT / "build/allocator-recording-comparison-v3-20261019")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--command-validation", type=Path)
    args = parser.parse_args()
    if args.action == "bind" and (args.source is None or args.command_validation is None):
        parser.error("bind requires --source and --command-validation")
    globals()[args.action](args)


if __name__ == "__main__":
    main()
