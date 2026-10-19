#!/usr/bin/env python3
"""Fixed key-level-command experiment; requires retained local research inputs.

The design precedes candidate implementation. Bind the candidate and this runner
before rendering. Neither stage edits production DSP or fits model parameters.
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
LAWS = {"Legacy": 0, "Firmware": 1}
sha, read, write, record, verify = common.sha, common.read, common.write, common.record, common.verify


def bind(args):
    out = args.output.resolve()
    design_path = out / "design-frozen-v2.json"
    design = read(design_path)
    assert not (out / "candidate-bound.json").exists(), "Candidate already bound"
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
    assert evidence["schema"] == "press78.keylevel-native-independent-command-audit.v1"
    assert evidence["passed"], "Independent command check required"
    assert evidence["native_coverage"]["table_entries"] == 640
    assert evidence["native_coverage"]["all_lks_note_offsets"] == 32768
    assert evidence["native_coverage"]["all_valid_tl_lks_note_commands"] == 4194304
    assert evidence["original_execution"]["fresh_primitive_cases"] == 131072
    for name, h in evidence["artifacts"].items():
        assert sha(ROOT / name) == h, name
    for kind in ("header", "generator"):
        assert sha(ROOT / evidence["candidate"][kind]) == evidence["candidate"][kind + "_sha256"]
    source = out / "candidate-source"
    shutil.copytree(args.source.resolve(), source)
    assert sha(source / "FirmwareLevel.h") == evidence["candidate"]["header_sha256"], "Command audit belongs to another candidate"
    snapshots = out / "snapshots"
    snapshots.mkdir()
    old = prior_path.parent
    for name in ("stereo_metrics.py", "HardwareSequencePressure.cpp"):
        p = old / "snapshots" / name
        assert sha(p) == prior["protocol"]["snapshots"][name]
        shutil.copyfile(p, snapshots / name)
    fixture = (snapshots / "HardwareSequencePressure.cpp").read_text()
    assert fixture.count("if(argc!=7)") == 1
    fixture = fixture.replace("if(argc!=7)", "if(argc!=8)")
    needle = "press78::Controls c;c.masterGain=1.;"
    assert fixture.count(needle) == 1
    fixture = fixture.replace(needle, "press78::Controls c;c.pitchModel=1;c.keyLevelModel=std::stoi(argv[7]);c.midiPitchBend=-1;c.masterGain=1.;")
    (out / "KeyLevelSequence.cpp").write_text(fixture)
    shutil.copyfile(Path(__file__), snapshots / "runner-bound.py")
    shutil.copyfile(ROOT / "Tools/benchmark_pitch_model.py", snapshots / "common-bound.py")
    bound = {
        "design": record(design_path), "bound_at_utc": common.now(),
        "source": {p.name: sha(p) for p in source.iterdir() if p.is_file()},
        "source_directory": str(source), "fixture": record(out / "KeyLevelSequence.cpp"),
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
    html = ['<!doctype html><meta charset="utf-8"><title>Key-level comparison</title>',
            '<h1>Hardware → Legacy → Firmware key level</h1>',
            '<p>Fixed windows/maps. One RMS gain per model stereo pair; common safety gain per voice. No EQ, timing or pitch fit.</p>']
    for patch in FOCUS:
        w = next(w for w in design["windows"] if w["patch"] == patch)
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
            audio = np.concatenate((hardware, gap, normalized[mid]["Legacy"], gap, normalized[mid]["Firmware"])) * safety
            assert np.isfinite(audio).all() and np.max(np.abs(audio)) <= .900001
            p = destination / f"{patch:02d}-{mid}-hardware-legacy-firmware.wav"
            wavfile.write(p, SR, audio.astype(np.float32))
            rows.append({"patch": patch, "map": mid, "audio": record(p), "pair_gains": gains[mid],
                         "common_focus_safety_gain": safety, "peak": float(np.max(np.abs(audio)))})
            html.append(f'<h2>{patch} {mid}</h2><audio controls src="auditions/{p.name}"></audio>')
    (out / "audition.html").write_text("\n".join(html))
    return rows


def run(args):
    out = args.output.resolve()
    bound = read(out / "candidate-bound.json")
    assert not (out / "run-started.json").exists(), "Keep completed/failed runs; use a fresh experiment"
    for key in ("design", "fixture", "runner", "common_module", "command_validation"):
        verify(bound[key])
    for name, h in bound["snapshots"].items():
        assert sha(out / "snapshots" / name) == h
    design = read(bound["design"]["path"])
    source = Path(bound["source_directory"])
    assert {p.name: sha(p) for p in source.iterdir() if p.is_file()} == bound["source"]
    assert sha(design["baseline"]["prior_b12_result"]) == design["baseline"]["prior_result_sha256"]
    verify(design["recording"])
    verify(design["bank"])
    write(out / "run-started.json", {"utc": common.now(), "candidate_binding_sha256": sha(out / "candidate-bound.json")})
    exe = out / "key_level_sequence"
    command = ["c++", "-std=c++17", "-O2", "-I", str(source), str(out / "KeyLevelSequence.cpp"),
               str(source / "Press78Engine.cpp"), "-o", str(exe)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    rate, reference = wavfile.read(design["recording"]["path"], mmap=True)
    assert rate == SR and reference.dtype == np.int16 and reference.shape[1] == 2
    models, renders, maximum_bytes = {}, {}, 0
    for m in design["maps"]:
        verify(m["events"])
        verify(m["expected_legacy_audio"])
        folder = out / "maps" / m["id"]
        folder.mkdir(parents=True)
        models[m["id"]] = {}
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
            assert size < 500000000
            result = {"command": cmd, "render": detail, "audio": artifact, "pressure": record(pressure)}
            if name == "Legacy":
                assert artifact["sha256"] == m["expected_legacy_audio"]["sha256"], "Keep mismatch WAV; Legacy identity failed"
                del data
                audio.unlink()
                result["deleted_only_after_exact_historical_hash_match"] = True
                _, data = wavfile.read(m["expected_legacy_audio"]["path"], mmap=True)
            models[m["id"]][name] = data[32:32 + len(reference)]
            assert models[m["id"]][name].shape == reference.shape
            renders[m["id"] + "/" + name] = result
            write(out / "render-progress.json", renders)
            print("Rendered", m["id"], name, flush=True)
    spec = importlib.util.spec_from_file_location("fixed_key_level_metrics", out / "snapshots/stereo_metrics.py")
    metric = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metric)
    rows = []
    for w in design["windows"]:
        a, z = round(w["start_seconds"] * SR), round(w["end_seconds"] * SR)
        observed = reference[a:z].astype(float) / 32768
        scores = {mid: {name: metric.stereo_compare(observed, models[mid][name][a:z], SR) for name in LAWS} for mid in MAPS}
        delta = {mid: {key: scores[mid]["Firmware"][key] - scores[mid]["Legacy"][key] for key in METRICS} for mid in MAPS}
        rows.append({**w, "scores": scores, "firmware_minus_legacy": delta})
        if len(rows) % 10 == 0:
            print("Scored", len(rows), "windows", flush=True)
    groups = {"all100": list(range(100)), "focus": list(FOCUS), "neighbors": [64, 66, 92, 94, 96, 98]}
    aggregate = {group: {mid: {name: {key: float(np.mean([r["scores"][mid][name][key] for r in rows if r["patch"] in patches]))
                                     for key in METRICS} for name in LAWS} for mid in MAPS} for group, patches in groups.items()}
    regressions = {mid: {key: [{"patch": r["patch"], "delta": r["firmware_minus_legacy"][mid][key]}
                              for r in rows if r["firmware_minus_legacy"][mid][key] > 0] for key in METRICS} for mid in MAPS}
    limits = design["required_gates"]
    def mean_delta(mid, key):
        return aggregate["all100"][mid]["Firmware"][key] - aggregate["all100"][mid]["Legacy"][key]
    gates = {
        "legacy_all4_whole_WAVs_identical": True,
        "unchanged_map_band_improvement": mean_delta("unchanged", "joint_lr_band_rmse_db") <= limits["unchanged_map_all100_joint_band_delta_max_db"],
        "other_maps_band_bounds": all(mean_delta(mid, "joint_lr_band_rmse_db") <= limits["other_maps_all100_joint_band_delta_max_db"] for mid in MAPS[1:]),
        "each_focus_each_map_band_bounds": all(r["firmware_minus_legacy"][mid]["joint_lr_band_rmse_db"] <= limits["each_focus_each_map_joint_band_delta_max_db"] for r in rows if r["patch"] in FOCUS for mid in MAPS),
        "all_maps_STFT_log_bounds": all(mean_delta(mid, "stereo_stft_log_error_db") <= limits["all_maps_all100_STFTlog_delta_max_db"] for mid in MAPS),
    }
    clips = auditions(out, design, reference, models)
    maximum_bytes = max(maximum_bytes, sum(p.stat().st_size for p in out.rglob("*.wav")))
    assert maximum_bytes < 500000000
    result = {"schema": design["schema"], "protocol": design, "design": bound["design"],
              "candidate_binding": record(out / "candidate-bound.json"), "candidate_source_sha256": bound["source"],
              "compile_command": command, "executable": record(exe), "renders": renders, "rows": rows,
              "aggregate": aggregate, "regressions": regressions, "audio_gates": gates,
              "audio_gates_passed": all(gates.values()), "auditions": clips, "maximum_new_wav_bytes": maximum_bytes,
              "external_gates": "Independent command equivalence/core/wrapper/CPU/SDK/host checks remain separate; no automatic adoption",
              "no_new_fit": True, "no_artificial_noise": True}
    write(out / "result.json", result)
    print(json.dumps({"result": str(out / "result.json"), "audio_gates": gates, "audio_gates_passed": all(gates.values())}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("bind", "run"))
    parser.add_argument("--output", type=Path, default=ROOT / "build/key-level-b13-20261019")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--command-validation", type=Path)
    args = parser.parse_args()
    if args.action == "bind" and (args.source is None or args.command_validation is None):
        parser.error("bind requires --source and --command-validation")
    globals()[args.action](args)


if __name__ == "__main__":
    main()
