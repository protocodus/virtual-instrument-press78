#!/usr/bin/env python3
"""Local, descriptive PSS-780 recording comparison; no bundled source audio.

Example:
  python3 Tools/hardware_benchmark.py --reference-root /path/to/pss780-experiment \
    --artifact-dir build/hardware-benchmarks/baseline-unique \
    --report Tests/results/hardware-baseline.json

Every invocation preserves its source snapshot, native executable, protocol,
render and A/B files in a unique ignored/local artifact directory. Reusing an
already completed directory is refused. The external recording and research
dependencies are explicitly hashed. There is no parameter, timing or pitch fit.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import tempfile

import numpy as np
from scipy import signal
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[1]
SR = 48000
TARGETS = (65, 93, 97)
NEIGHBORS = (64, 66, 92, 94, 96, 98)
PRIOR_TRAIN = (0, 2, 22, 34, 59, 77)
PRIOR_REGRESSION = (1, 3, 23, 35, 60, 75)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write_json(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def rms(x):
    return float(np.sqrt(np.mean(np.asarray(x, dtype=float)**2)))


def events_file(reference, destination):
    alignment = read(reference / "references/v2/alignment.json")
    timeline = read(reference / "references/v3_program_timeline.json")["intervals"]
    notes = read(reference / "references/v2/eugenia-events.json")["notes"]
    bank = read(ROOT / "Resources/FactoryBank/press78-factory.json")["voices"]
    raw = {v["number"]: bytes(v["raw_data"]).hex() for v in bank}
    rows = []
    for p in timeline:
        rows.append((round(p["audio_start_seconds"] * SR), 0, len(rows), f'patch {raw[p["patch"]]}'))
    transformed = []
    for n in notes:
        start = alignment["offset_seconds"] + alignment["scale"] * n["start"]
        gate = alignment["scale"] * n["gate"]
        begin, duration = round(start * SR), round(gate * SR)
        if duration <= 0 or n["velocity"] <= 0:
            continue
        source = n["channel"]
        # Program, old note-offs, then note-ons, preserving MIDI file order.
        rows.append((begin, 2, len(rows), f'on {n["midi"]} {n["velocity"]} {source}'))
        rows.append((begin + duration, 1, len(rows), f'off {n["midi"]} {source}'))
        transformed.append({"start": start, "gate": gate, "midi": n["midi"],
                            "velocity": n["velocity"], "channel": source,
                            "on_frame": begin, "off_frame": begin + duration})
    destination.write_text("".join(f"{frame} {line}\n" for frame, _, _, line in sorted(rows)))
    return transformed, timeline, alignment


def snapshot_sources(source, out):
    out.mkdir(exist_ok=True)
    for path in sorted(source.iterdir()):
        if not path.is_file():
            continue
        destination = out / path.name
        if path.resolve() != destination.resolve():
            if destination.exists() and destination.read_bytes() != path.read_bytes():
                raise ValueError(f"Refusing to overwrite frozen source: {destination}")
            shutil.copy2(path, destination)
    return {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file()}


def legacy_side(mid, start_seconds=0.):
    """Analytic reproduction of the old native creative chorus, full mix.

    Fixed12ms delay,2ms depth,.65Hz sine, quarter-cycle second tap. This is
    explicitly a reproduction for the input-driven diagnostic, not recovered
    hardware. There is no smoothing transition because controls start fixed.
    """
    samples = np.arange(len(mid)); phase = 2 * np.pi * .65 * (start_seconds + samples / SR)
    a = np.interp(samples - SR * (.012 + .002 * np.sin(phase)), samples, mid, left=0., right=0.)
    b = np.interp(samples - SR * (.012 + .002 * np.sin(phase + np.pi / 2)), samples, mid, left=0., right=0.)
    return .5 * (a - b)


def side_metrics(prediction, expected):
    a, b = rms(prediction), rms(expected)
    if b <= 1e-12:
        raise ValueError("Silent side reference")
    return {"normalized_rmse": rms(prediction - expected) / b,
            "rms_level_error_db": 20 * np.log10(max(a, 1e-30) / b),
            "correlation": None if a <= 1e-12 else float(np.corrcoef(prediction, expected)[0, 1])}


def audition(out, patch, reference, candidates):
    equal = {"reference": reference}
    gains = {}
    for key, y in candidates.items():
        gains[key] = rms(reference) / rms(y)
        equal[key] = y * gains[key]
    safety = min(1., .85 / max(np.max(abs(y)) for y in equal.values()))
    paths = {}
    for key, y in equal.items():
        path = out / f"{patch:02d}-{key}.wav"
        wavfile.write(path, SR, np.asarray(y * safety, dtype=np.float32)); paths[key] = str(path)
    order = list(equal)
    combined = out / f"{patch:02d}-comparison.wav"
    wavfile.write(combined, SR, np.concatenate([part for key in order for part in
                  (equal[key] * safety, np.zeros((round(.4 * SR), 2)))]).astype(np.float32))
    return {"patch": patch, "files": paths, "combined": str(combined), "order": order,
            "one_stereo_pair_gains": gains, "common_safety_gain": safety,
            "capture_noise_added": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, default=ROOT / "Source/DSP")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--baseline-report", type=Path, help="Also load preserved native dry/legacy clips from this earlier report")
    parser.add_argument("--all-presets", action="store_true")
    parser.add_argument("--modes", default="raw,dry,legacy", help="Comma-separated fixture output modes")
    args = parser.parse_args()
    reference, out = args.reference_root.resolve(), args.artifact_dir.resolve()
    if (out / "report.json").exists():
        parser.error("Completed artifact directory already exists; choose a unique directory")
    if out.is_relative_to(ROOT):
        ignored = subprocess.run(["git", "check-ignore", "--quiet", str(out)], cwd=ROOT).returncode == 0
        if not ignored:
            parser.error("Audio artifact directory inside repository must be git-ignored")
    out.mkdir(parents=True, exist_ok=True); audio = out / "audio"; audio.mkdir(exist_ok=True)
    sources = snapshot_sources(args.source_dir.resolve(), out / "source")
    fixture = ROOT / "Tools/HardwareSequence.cpp"; shutil.copy2(fixture, out / fixture.name)
    shutil.copy2(Path(__file__), out / Path(__file__).name)
    metric_path = reference / "references/stereo_metrics.py"
    spec = importlib.util.spec_from_file_location("frozen_stereo_metrics", metric_path)
    metrics = importlib.util.module_from_spec(spec); spec.loader.exec_module(metrics)
    sys.path.insert(0, str(reference))
    from circuit.refined_chorus import process_refined_chorus
    from circuit.calibrated_chorus import process_calibrated_chorus

    source_path = reference / "references/v2/user-ONfIvtDOog0.wav"
    sr, original = wavfile.read(source_path, mmap=True)
    if sr != SR or original.dtype != np.int16 or original.ndim != 2 or original.shape[1] != 2:
        raise ValueError("Expected original48k stereo PCM16 source")
    events = out / "events.txt"
    notes, timeline, alignment = events_file(reference, events)
    full_protocol = read(reference / "results/v4/protocol.json")
    selected = set(range(100) if args.all_presets else (*TARGETS, *NEIGHBORS, *PRIOR_TRAIN, *PRIOR_REGRESSION))
    windows = [w for w in full_protocol["windows"] if w["patch"] in selected]
    protocol = {"version": 1, "sample_rate": SR, "targets": TARGETS, "neighbors": NEIGHBORS,
        "prior_training": PRIOR_TRAIN, "prior_regression": PRIOR_REGRESSION,
        "windows": windows, "data_status": "All100 already observed; no fresh holdout and no new fit",
        "events": "Full absolute video-time performance from zero; patch changes affect future notes only; no cropped-away context",
        "event_order": "At equal frames: program, prior note-offs, then stable note-ons; note-off frame=rounded onset+rounded gate",
        "channel_policy": "Both MIDI channels use the same program; channel IDs distinguish note-off matching",
        "alignment": alignment, "latency": "Remove reported nominal integer engine latency only; no local lag/phase/pitch search",
        "recorded_chorus_epoch": "Set native recorded-mode effect epoch to -reportedLatency/sampleRate, exactly compensating the later fixed-latency trim; legacy baseline retains its original epoch0",
        "controls": {"masterGain": 1., "outputCircuit": "on except raw", "toneCutoffHz": 0.,
            "dcBlock": False, "outputLimit": False, "drive": 0., "noiseRms": 0.,
            "legacy_chorusMix": 1., "legacy_rate_hz": .65, "legacy_depth_ms": 2.,
            "recorded_mode": "Full mix, global frozen v3 captured rate/depth from RecordedChorusProfile.h; no fit",
            "polyphony": 12, "vibrato_and_sustain": "Factory flags, identical to frozen offline behavior"},
        "stereo_metrics": "Frozen v4 metrics: one pair gain,64log bands80-14000Hz and STFT512/2048/8192; no per-channel fit",
        "effect_only": "Observed M→S, third-order100–4000Hz zero-phase Butterworth, programbar+.25 to+1.5s; .2s context; no level/time/phase fit",
        "source_sha256": {"recording": sha(source_path), "events": sha(events), "stereo_metrics": sha(metric_path),
            "v4_protocol": sha(reference / "results/v4/protocol.json"), "fixture": sha(fixture),
            "script": sha(Path(__file__)), "source": sources}}
    write_json(out / "protocol.json", protocol)  # Written before any estimates.
    executable = out / "hardware_sequence"
    command = ["c++", "-std=c++17", "-O2", "-I", str(out / "source"), str(out / fixture.name),
               str(out / "source/Press78Engine.cpp"), "-o", str(executable)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    effect_executable = None
    if (out / "source/RecordedChorus.h").exists():
        probe_source = ROOT / "Tools/ChorusProbe.cpp"
        shutil.copy2(probe_source, out / probe_source.name)
        effect_executable = out / "chorus_probe"
        subprocess.run(["c++", "-std=c++17", "-O2", "-I", str(out / "source"),
                        str(out / probe_source.name), "-o", str(effect_executable)], check=True, capture_output=True, text=True)
    rendered, render_metadata = {}, {}
    for mode in args.modes.split(","):
        path = out / f"native-{mode}-continuous.wav"; start = time.perf_counter()
        result = subprocess.run([str(executable), str(events), str(path), str(len(original) + 4096), str(SR), mode],
                                check=True, capture_output=True, text=True)
        detail = json.loads(result.stdout); detail["wall_seconds"] = time.perf_counter() - start
        rate, data = wavfile.read(path, mmap=True)
        if rate != SR or not np.isfinite(data).all(): raise ValueError("Invalid native output")
        latency = detail["latency_samples"]
        rendered["native_" + mode] = data[latency:latency+len(original)]
        render_metadata[mode] = {**detail, "file": str(path), "sha256": sha(path)}
        print(f"Rendered {mode} in {detail['wall_seconds']:.2f}s; latency {latency}", flush=True)
    cache_path = reference / "results/focused-v3/continuous-performance.npz"
    cache = np.load(cache_path); center = cache["selected"]
    baseline = read(args.baseline_report) if args.baseline_report else None
    if baseline:
        for mode, item in baseline["native_renders"].items():
            if mode == "raw": continue
            path = Path(item["file"])
            if sha(path) != item["sha256"]: raise ValueError("Frozen baseline audio changed")
            _, data = wavfile.read(path, mmap=True); latency = item["latency_samples"]
            rendered["baseline_" + mode] = data[latency:latency+len(original)]
    rows, examples = [], []
    for w in windows:
        p = w["patch"]; a, z = round(w["start_seconds"] * SR), round(w["end_seconds"] * SR)
        first, last = max(0, a-SR), min(len(center), z+round(.05*SR))
        offline = process_refined_chorus(center[first:last], SR, start_seconds=first/SR)[a-first:z-first]
        offline_v3 = process_calibrated_chorus(center[first:last], SR, start_seconds=first/SR)[a-first:z-first]
        ref = original[a:z].astype(float)/32768
        candidates = {k: v[a:z] for k, v in rendered.items() if k != "native_raw"}
        candidates["offline_v4_effective"] = offline
        candidates["offline_v3_effective"] = offline_v3
        scores = {k: metrics.stereo_compare(ref, y, SR) for k, y in candidates.items()}
        groups = [name for name, group in (("target", TARGETS), ("neighbor", NEIGHBORS),
                 ("prior_train", PRIOR_TRAIN), ("prior_regression", PRIOR_REGRESSION)) if p in group]
        rows.append({**w, "groups": groups or ["other_reused"], "scores": scores})
        if p in TARGETS:
            examples.append({**w, **audition(audio, p, ref, candidates)})
    # Input-driven effect comparison, independent of synthesized FM.
    mid = original.astype(float).mean(axis=1)/32768
    side = (original[:,0].astype(float)-original[:,1])/65536
    bandpass = signal.butter(3, [100,4000], fs=SR, btype="bandpass", output="sos")
    side = signal.sosfiltfilt(bandpass, side)
    effect_rows = []; effect_parity = []
    effect_temp = tempfile.TemporaryDirectory(prefix="press78-effect-", dir=out)
    for p in sorted(selected):
        start = timeline[p]["audio_start_seconds"]
        a, z, pad = round((start+.25)*SR), round((start+1.5)*SR), round(.2*SR)
        segment = mid[a-pad:z+pad]; t = (a-pad)/SR
        offline = process_refined_chorus(segment, SR, start_seconds=t)
        offline_v3 = process_calibrated_chorus(segment, SR, start_seconds=t)
        predictions = {"legacy_creative_reproduction": legacy_side(segment,t),
                       "offline_v3_effective": (offline_v3[:,0]-offline_v3[:,1])/2,
                       "offline_v4_effective": (offline[:,0]-offline[:,1])/2}
        if effect_executable:
            input_path, output_path = Path(effect_temp.name)/"mid.f64", Path(effect_temp.name)/"stereo.f64"
            np.asarray(segment, dtype=np.float64).tofile(input_path)
            subprocess.run([str(effect_executable), str(SR), str(t), str(input_path), str(output_path)],
                           check=True, capture_output=True, text=True)
            actual = np.fromfile(output_path, dtype=np.float64).reshape(-1,2)
            if actual.shape != offline_v3.shape or not np.isfinite(actual).all(): raise ValueError("Invalid effect probe")
            predictions["native_recorded_effect"] = (actual[:,0]-actual[:,1])/2
            effect_parity.append({"patch": p, "max_absolute_error": float(np.max(abs(actual[pad:-pad]-offline_v3[pad:-pad]))),
                                  "relative_rms_error": rms(actual[pad:-pad]-offline_v3[pad:-pad])/rms(offline_v3[pad:-pad])})
        scores = {key: side_metrics(signal.sosfiltfilt(bandpass, y)[pad:-pad], side[a:z])
                  for key, y in predictions.items()}
        effect_rows.append({"patch": p, "start_seconds": a/SR, "end_seconds": z/SR, "scores": scores})
    effect_temp.cleanup()
    aggregate = {}
    for group, patches in (("targets", TARGETS), ("neighbors", NEIGHBORS), ("prior_regression", PRIOR_REGRESSION), ("all_scored", selected)):
        subset = [r for r in rows if r["patch"] in patches]
        aggregate[group] = {k: {"count": len(subset), **{metric: float(np.mean([r["scores"][k][metric] for r in subset]))
                           for metric in ("joint_lr_band_rmse_db", "mid_band_rmse_db", "stereo_stft_convergence", "stereo_stft_log_error_db")}}
                           for k in subset[0]["scores"]}
    effect_summary = {group: {key: float(np.mean([r["scores"][key]["normalized_rmse"] for r in effect_rows if r["patch"] in patches]))
                      for key in effect_rows[0]["scores"]} for group, patches in (("targets", TARGETS), ("neighbors", NEIGHBORS), ("all_scored", selected))}
    parity = None
    if "native_raw" in rendered:
        expected = cache["raw"]; actual = rendered["native_raw"][:len(expected),0]
        parity = {"relative_rms_error": rms(actual-expected)/rms(expected), "max_absolute_error": float(np.max(abs(actual-expected))),
                  "scope": "Full program-performance implementation parity, not hardware; allocations and rounding may differ", "windows": []}
        for w in windows:
            a,z=round(w['start_seconds']*SR),round(w['end_seconds']*SR)
            parity['windows'].append({'patch':w['patch'],'relative_rms_error':rms(actual[a:z]-expected[a:z])/rms(expected[a:z]),
                                      'max_absolute_error':float(np.max(abs(actual[a:z]-expected[a:z])))})
    report = {"version": "native-hardware-descriptive-v1", "artifact_directory": str(out),
        "source_recording": {"url": "https://www.youtube.com/watch?v=ONfIvtDOog0", "sha256": sha(source_path),
            "redistribution": "External local research capture; no redistribution license found; not bundled in shipping repository"},
        "protocol": protocol, "native_renders": render_metadata, "native_source_sha256": sources,
        "executable_sha256": sha(executable), "compile_command": command,
        "rows": rows, "aggregate": aggregate, "examples": examples,
        "effect_only": {"rows": effect_rows, "mean_normalized_rmse": effect_summary, "native_v3_implementation_parity": effect_parity,
                        "probe_sha256": sha(effect_executable) if effect_executable else None}, "offline_parity": parity,
        "limitations": ["Polyphonic MIDI preset tour with reverb, chorus and vibrato enabled; no controlled dry isolated target capture.",
            "Global bar program schedule and MIDI file are inferred; sender settings and exact device behavior remain unknown.",
            "No fresh holdout: targets, neighbors and prior groups were observed during earlier model development.",
            "Native factory flag policy is the same behavioral hypothesis as offline; panel effects do not independently verify exact LFO/reverb laws.",
            "Offline analog cache uses4x192k MNA plus FIR up/downsampling; native analog uses the same MNA-derived circuit discretized at48k. Target raw FM parity is checked separately.",
            "Pair RMS matching removes absolute gain evidence; no per-channel, pitch, phase or local-latency fit.",
            "Legacy effect-only path is an analytic reproduction of old native delay taps; offline v4 is a globally fitted recording transfer, not a recovered BBD circuit.",
            "No capture noise bed or new nonlinear fit is used. Metrics do not measure a percentage of hardware fidelity."],
        "dependency_sha256": {"continuous_cache": sha(cache_path), "v4_profile": sha(reference/"circuit/v4_effective_stereo_profile.json"),
            "refined_chorus": sha(reference/"circuit/refined_chorus.py"), "calibrated_chorus": sha(reference/"circuit/calibrated_chorus.py"),
            "alignment": sha(reference/"references/v2/alignment.json"), "timeline": sha(reference/"references/v3_program_timeline.json"),
            "midi_events": sha(reference/"references/v2/eugenia-events.json"), "factory_bank": sha(ROOT/"Resources/FactoryBank/press78-factory.json")}}
    report["audio_sha256"] = {str(p): sha(p) for p in sorted(audio.glob("*.wav"))}
    write_json(out / "report.json", report); write_json(args.report, report)
    print(json.dumps({"aggregate_targets": aggregate["targets"], "effect_targets": effect_summary["targets"], "offline_parity": parity}, indent=2))


if __name__ == "__main__":
    main()
