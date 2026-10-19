#!/usr/bin/env python3
"""Check the complete causal 4x circuit against independent component-network MNA.

The circuit is the documented PSS480 volume-pot-top surrogate. This verifies a
numerical approximation, not an identified PSS780 board or YM3420 DAC. No noise,
recorded samples, fitted gain or per-rate normalization enters these checks.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

import numpy as np
from scipy import linalg, signal
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Tools/reference"))
sys.path.insert(0, str(ROOT / "Tools"))
from circuit.model import build_circuit
from generate_analog import retarget
from generate_analog_oversampling import halfband_coefficients

RATES = (8000, 44100, 44117, 48000, 96000, 192000)
LATENCY = 80
FRAMES = 1 << 18


def db(value):
    return 20 * np.log10(np.maximum(np.abs(value), 1e-300))


def phase(value):
    return np.angle(value) * 180 / np.pi


def response(coefficients, rate, frequencies):
    return signal.freqz(coefficients, worN=np.asarray(frequencies), fs=rate)[1]


def probe_json(probe, *args):
    return json.loads(subprocess.check_output([str(probe), *map(str, args)], text=True))


def check_rate(probe, work, rate, circuit, endpoint, base_sos, outer, inner):
    audio = {}
    for mode in ("baseline", "oversampled", "resampler"):
        path = work / f"{mode}-{rate}.f64"
        subprocess.run([str(probe), "impulse", str(rate), mode, str(FRAMES), str(path)], check=True)
        audio[mode] = np.fromfile(path, dtype=np.float64)
        assert len(audio[mode]) == FRAMES and np.isfinite(audio[mode]).all()

    maximum_hz = min(20000, rate * 0.45)
    bins = np.unique(np.round(np.geomspace(20, maximum_hz, 4001) / rate * FRAMES).astype(int))
    frequencies = bins / FRAMES * rate
    native = {mode: np.fft.rfft(x)[bins] for mode, x in audio.items()}
    # Direct full descriptor frequency solve; no polynomial or SOS reduction.
    continuous = circuit.frequency_response(frequencies, endpoint)
    remove_latency = np.exp(2j * np.pi * frequencies * LATENCY / rate)
    baseline_db = db(native["baseline"] / continuous)
    oversampled_db = db(native["oversampled"] / continuous)
    baseline_phase = phase(native["baseline"] / continuous)
    oversampled_phase = phase(native["oversampled"] * remove_latency / continuous)
    resampler_db = db(native["resampler"])
    resampler_phase = phase(native["resampler"] * remove_latency)

    bands = []
    for stop in (4000, 10000, 12000, 16000, 20000):
        selected = frequencies <= min(stop, maximum_hz)
        bands.append({
            "band_hz": [20, min(stop, maximum_hz)],
            "dense_points": int(sum(selected)),
            "baseline_max_absolute_db_error": float(max(abs(baseline_db[selected]))),
            "oversampled_max_absolute_db_error": float(max(abs(oversampled_db[selected]))),
            "baseline_max_absolute_phase_error_degrees": float(max(abs(baseline_phase[selected]))),
            "oversampled_latency_removed_max_phase_error_degrees": float(max(abs(oversampled_phase[selected]))),
            "resampler_only_max_absolute_db_error": float(max(abs(resampler_db[selected]))),
            "resampler_latency_removed_max_phase_error_degrees": float(max(abs(resampler_phase[selected]))),
        })
    assert bands[1]["oversampled_max_absolute_db_error"] < 0.15
    assert bands[2]["oversampled_max_absolute_db_error"] < 0.3
    assert max(abs(resampler_phase)) < 1e-6

    points = []
    sample_positions = np.arange(FRAMES)
    for hz in (20, 50, 100, 1000, 2000, 3000, 3600, 4000, 5000, 8000, 10000, 12000, 16000, 18000, 20000):
        if hz > maximum_hz:
            continue
        kernel = np.exp(-2j * np.pi * hz / rate * sample_positions)
        raw = {mode: np.dot(x, kernel) for mode, x in audio.items()}
        desired = circuit.frequency_response([hz], endpoint)[0]
        correction = np.exp(2j * np.pi * hz * LATENCY / rate)
        entry = {
            "frequency_hz": hz,
            "continuous_db": float(db(desired)),
            "baseline_db_error": float(db(raw["baseline"] / desired)),
            "oversampled_db_error": float(db(raw["oversampled"] / desired)),
            "baseline_phase_error_degrees": float(phase(raw["baseline"] / desired)),
            "oversampled_raw_phase_error_degrees": float(phase(raw["oversampled"] / desired)),
            "oversampled_latency_removed_phase_error_degrees": float(phase(raw["oversampled"] * correction / desired)),
            "resampler_db": float(db(raw["resampler"])),
            "resampler_latency_removed_phase_degrees": float(phase(raw["resampler"] * correction)),
        }
        if hz == 10000:
            assert abs(entry["oversampled_db_error"]) < 0.15
        if hz == 12000:
            assert abs(entry["oversampled_db_error"]) < 0.3
        points.append(entry)

    # Independent upfirdn interpolators, followed by the full 19-variable
    # descriptor trapezoid, followed by independent upfirdn decimators.
    impulse = np.zeros(FRAMES)
    impulse[0] = 1
    interpolated = signal.upfirdn(2 * inner, signal.upfirdn(2 * outer, impulse, up=2), up=2)
    left = 8 * rate * circuit.C + circuit.G
    right = 8 * rate * circuit.C - circuit.G
    descriptor_a = linalg.solve(left, right)
    descriptor_b = linalg.solve(left, circuit.B[:, 0])
    assert circuit.G.shape == (19, 19) and circuit.index(endpoint) == 9
    paths = {name: work / f"descriptor-{name}.f64" for name in ("A", "B", "input", "output")}
    descriptor_a.astype(np.float64).tofile(paths["A"])
    descriptor_b.astype(np.float64).tofile(paths["B"])
    interpolated.astype(np.float64).tofile(paths["input"])
    subprocess.run([str(probe), "descriptor", *map(str, (paths[n] for n in ("A", "B", "input", "output")))], check=True)
    descriptor_high = np.fromfile(paths["output"], dtype=np.float64)
    descriptor_reference = signal.upfirdn(outer, signal.upfirdn(inner, descriptor_high, down=2), down=2)[:FRAMES]
    # A second, separately generated SOS reference is only a supplementary
    # cross-check. The descriptor reference above does not use SOS or SVD.
    mna_sos = signal.sosfilt(circuit.discrete_sos(4 * rate, endpoint), interpolated)
    sos_reference = signal.upfirdn(outer, signal.upfirdn(inner, mna_sos, down=2), down=2)[:FRAMES]
    resampler_reference = signal.upfirdn(outer, signal.upfirdn(inner, interpolated, down=2), down=2)[:FRAMES]

    # Exact phase-0 four-image alias expression verifies the complete native
    # conversion path, including aliases, rather than multiplying passbands.
    branches = []
    for image in range(4):
        f = frequencies + image * rate
        h = response(outer, 2 * rate, f) * response(inner, 4 * rate, f)
        analog = signal.sosfreqz(retarget(base_sos, 4 * rate), worN=f, fs=4 * rate)[1]
        branches.append(h * h * analog)
    formula = np.sum(branches, axis=0)
    alias_relative_db = db(sum(branches[1:]) / branches[0])
    errors = {
        "native_vs_full_descriptor_upfirdn_max_abs": float(max(abs(audio["oversampled"] - descriptor_reference))),
        "native_vs_full_descriptor_upfirdn_relative_l2": float(np.linalg.norm(audio["oversampled"] - descriptor_reference) / np.linalg.norm(descriptor_reference)),
        "native_vs_separate_mna_sos_upfirdn_max_abs": float(max(abs(audio["oversampled"] - sos_reference))),
        "resampler_vs_independent_upfirdn_max_abs": float(max(abs(audio["resampler"] - resampler_reference))),
        "native_vs_exact_alias_sum_max_complex": float(max(abs(native["oversampled"] - formula))),
        "impulse_final_second_peak": float(max(abs(audio["oversampled"][-rate:]))),
    }
    assert errors["native_vs_full_descriptor_upfirdn_max_abs"] < 1e-7
    assert errors["native_vs_full_descriptor_upfirdn_relative_l2"] < 1e-6
    assert errors["native_vs_separate_mna_sos_upfirdn_max_abs"] < 1e-7
    assert errors["resampler_vs_independent_upfirdn_max_abs"] < 1e-12
    assert errors["native_vs_exact_alias_sum_max_complex"] < 1e-7

    image_levels = []
    fundamental = response(outer, 2 * rate, frequencies) * response(inner, 4 * rate, frequencies)
    for image in range(1, 4):
        shifted = frequencies + image * rate
        amplitude = response(outer, 2 * rate, shifted) * response(inner, 4 * rate, shifted)
        image_levels.append({"image_index": image, "maximum_relative_db": float(max(db(amplitude / fundamental)))})
    result = {
        "sample_rate": rate, "integration_rate": 4 * rate,
        "latency_frames": LATENCY, "latency_ms": 1000 * LATENCY / rate,
        "frequency_rows": points, "dense_comparison": bands,
        "independent_checks": errors,
        "outer_halfband_stopband_db_max_0_6_to_1_host_rate": float(max(db(response(outer, 2 * rate, np.linspace(0.6 * rate, rate, 20001))))),
        "inner_halfband_stopband_db_max_1_2_to_2_host_rate": float(max(db(response(inner, 4 * rate, np.linspace(1.2 * rate, 2 * rate, 20001))))),
        "interpolation_image_levels": image_levels,
        "alias_sum_relative_to_fundamental_db_max": float(max(alias_relative_db)),
        "native_runtime": probe_json(probe, "validate", rate),
        "cpu_benchmark": probe_json(probe, "benchmark", rate, 1 << 20),
    }
    (work / f"dense-{rate}.json").write_text(json.dumps({
        "frequencies_hz": frequencies.tolist(),
        "baseline_db_error": baseline_db.tolist(), "oversampled_db_error": oversampled_db.tolist(),
        "baseline_phase_error_degrees": baseline_phase.tolist(),
        "oversampled_phase_error_degrees_latency_removed": oversampled_phase.tolist(),
        "resampler_db": resampler_db.tolist(), "alias_sum_relative_db": alias_relative_db.tolist(),
    }, indent=2) + "\n")
    return result


def run(probe, work):
    subprocess.run([sys.executable, str(ROOT / "Tools/generate_analog_oversampling.py"), "--check"], check=True)
    circuit, endpoint = build_circuit(model="pss480")
    base_sos = circuit.discrete_sos(48000, endpoint)
    filters = halfband_coefficients()
    metadata = probe_json(probe, "metadata")
    assert metadata["latency_frames"] == LATENCY and metadata["instance_bytes"] < 6144
    rows = [check_rate(probe, work, rate, circuit, endpoint, base_sos, filters["outer"], filters["inner"]) for rate in RATES]
    sources = ("Source/DSP/OversampledAnalogOutput.h", "Source/DSP/AnalogOutput.h",
               "Tools/generate_analog_oversampling.py", "Tools/generate_analog.py",
               "Tools/OversampledAnalogProbe.cpp", "Tools/check_analog_oversampled.py",
               "Tools/reference/circuit/model.py")
    return {
        "passed": True,
        "scope": "Complete causal 4x integration of documented PSS480 volume-pot-top surrogate; not identified PSS780 AUX circuit or YM3420 converter.",
        "policy": {"factor": 4, "outer_taps": 129, "inner_taps": 65, "window": "Kaiser beta10, exact halfband zeros, odd sum0.5, center0.5",
                   "decimation_phase": 0, "fixed_fir_delay_host_frames": LATENCY,
                   "normalization": "fixed FIR unity DC only; no signal/voice/rate fit or makeup gain",
                   "maximum_db_error_through_10khz": 0.15, "maximum_db_error_through_12khz": 0.3,
                   "dc_final_second_after_5s_step_peak_limit": 1e-7},
        "instance": metadata, "sanitization": probe_json(probe, "sanitize"), "rows": rows,
        "platform": platform.platform(), "machine": platform.machine(), "python": platform.python_version(),
        "numpy": np.__version__, "scipy": scipy.__version__,
        "probe_sha256": hashlib.sha256(probe.read_bytes()).hexdigest(),
        "source_sha256": {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in sources},
        "limitations": [
            "80-frame FIR delay must also be applied to dry/bypass paths and added to device latency; this isolated tool does not verify engine integration.",
            "Noise-free linear numerical component, not a recovered hardware DAC schedule, bit depth or complete PSS780 board.",
            "All 8kHz frequency claims stop at3.6kHz; no above-Nyquist10/12kHz claim is made.",
            "Existing retargeted SOS has small numerical unit-step DC residue; measured and accepted below1e-7, not hidden by an extra high-pass.",
            "Alias figures below numerical verification floor are analytical coefficient predictions, not measured hardware performance.",
            "CPU figures concern this mono output component in the supplied standalone binary; no whole-instrument/Reason performance claim.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=ROOT / "Tests/results/analog-oversampled.json")
    parser.add_argument("--work-dir", type=Path, help="Retain impulses and dense metrics in this ignored directory")
    args = parser.parse_args()
    if args.work_dir:
        args.work_dir.mkdir(parents=True, exist_ok=True)
        result = run(args.probe.resolve(), args.work_dir.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix="press78-analog-4x-") as temporary:
            result = run(args.probe.resolve(), Path(temporary))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": True, "rates": RATES, "latency_frames": LATENCY,
                      "instance_bytes": result["instance"]["instance_bytes"], "report": str(args.report)}, indent=2))


if __name__ == "__main__":
    main()
