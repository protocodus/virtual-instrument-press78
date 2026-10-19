#!/usr/bin/env python3
"""Run exactly the adjacent frozen source-observability/parity protocol.

The scope is a necessary symmetry property, not a YM3420 implementation.
No audio is written. Only already retained local PCM is read.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
from scipy.io import wavfile


def binding(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def measure(y: np.ndarray, sample_rate: int, frequency: float, order: int) -> dict:
    # Include the old 12-harmonic basis unchanged. Additional terms describe
    # only slow fundamental nonstationarity; they never alter individual H2+.
    t = (np.arange(len(y)) - (len(y) - 1) / 2) / sample_rate
    angle = 2 * np.pi * frequency * t[:, None] * np.arange(1, 13)
    sine, cosine = np.sin(angle), np.cos(angle)
    columns = [np.ones(len(y)), *sine.T, *cosine.T]
    for power in range(1, order + 1):
        columns.extend([t**power * sine[:, 0], t**power * cosine[:, 0]])
    matrix = np.column_stack(columns)
    weight = np.hanning(len(y))
    coefficients = np.linalg.lstsq(matrix * weight[:, None], y * weight,
                                 rcond=None)[0]
    amplitude = np.hypot(coefficients[1:13], coefficients[13:25])
    phase = np.arctan2(coefficients[13:25], coefficients[1:13])
    residual = y - matrix @ coefficients
    return {
        "nuisance_order": order,
        "fundamental_amplitude": float(amplitude[0]),
        "harmonic_db_relative_fundamental":
            (20 * np.log10(np.maximum(amplitude / amplitude[0], 1e-15))).tolist(),
        "h2_minus_twice_h1_phase_radians":
            float(np.angle(np.exp(1j * (phase[1] - 2 * phase[0])))),
        "residual_relative_rms":
            float(np.sqrt(np.mean(residual**2) / np.mean(y**2))),
        "weighted_residual_relative_rms":
            float(np.linalg.norm(residual * weight) / np.linalg.norm(y * weight)),
        "matrix_condition_number": float(np.linalg.cond(matrix * weight[:, None])),
    }


def synthetic(design: dict) -> dict:
    n = design["period_samples"]
    phase = np.arange(n) / n
    reference = np.sin(2 * np.pi * phase)
    rows = []
    for phase_bits in design["phase_address_bits"]:
        addresses = 2**phase_bits
        half = np.sin(2 * np.pi * (np.arange(addresses // 2) + 0.5) / addresses)
        for amplitude_bits in design["symmetric_linear_amplitude_bits"]:
            levels = 2**(amplitude_bits - 1) - 1
            quantized_half = np.rint(half * levels) / levels
            table = np.concatenate((quantized_half, -quantized_half))
            y = table[np.floor(phase * addresses).astype(int)]
            spectrum = np.fft.rfft(y) * (2 / n)
            amplitude = np.abs(spectrum)
            parity = float(np.max(np.abs(y[:n // 2] + y[n // 2:])))
            dc = float(abs(y.mean()) / amplitude[1])
            even = float(np.max(amplitude[2::2]) / amplitude[1])
            assert parity == 0.0
            assert dc < 1e-12 and even < 1e-12
            rows.append({
                "phase_address_bits": phase_bits,
                "symmetric_linear_amplitude_bits": amplitude_bits,
                "half_wave_antisymmetry_max_error": parity,
                "dc_relative_to_h1": dc,
                "max_even_harmonic_relative_to_h1": even,
                "h3_db_relative_to_h1":
                    float(20 * np.log10(max(amplitude[3] / amplitude[1], 1e-15))),
                "relative_rms_error_versus_ideal_sine":
                    float(np.linalg.norm(y - reference) / np.linalg.norm(reference)),
            })
    alpha = 0.04
    y = reference + alpha * reference**2
    spectrum = np.abs(np.fft.rfft(y)) * (2 / n)
    h2_ratio = float(spectrum[2] / spectrum[1])
    assert abs(h2_ratio - alpha / 2) < 1e-12
    return {
        "candidates": rows,
        "positive_control": {"quadratic_alpha_test_fixture_only": alpha,
                             "h2_relative_to_h1": h2_ratio,
                             "h2_db_relative_to_h1": 20 * math.log10(h2_ratio)},
        "checks_passed": len(rows) * 3 + 1,
    }


def main() -> None:
    root = Path(__file__).resolve().parent
    design_path = root / "design-frozen.json"
    design = json.loads(design_path.read_text())
    source_path = Path(design["source"])
    source_binding = binding(source_path)
    assert source_binding["sha256"] == design["expected_source_sha256"]
    old_path = Path(design["old_analysis"])
    old = json.loads(old_path.read_text())
    old_row = next(row for row in old["windows"] if row["table"] == 0)
    assert [old_row["start"], old_row["end"]] == design["source_window_seconds"]
    frequency = old_row["f0_hz"]
    rate, audio = wavfile.read(source_path)
    assert rate == 48000 and audio.ndim == 2 and audio.shape[1] == 2
    if np.issubdtype(audio.dtype, np.integer):
        audio = audio.astype(np.float64) / max(abs(np.iinfo(audio.dtype).min),
                                             np.iinfo(audio.dtype).max)
    else:
        audio = audio.astype(np.float64)
    start, end = design["source_window_seconds"]
    windows = [("full", start, end)]
    windows.extend((f"part-{index + 1}", start + index * 0.05,
                    start + (index + 1) * 0.05) for index in range(7))
    rows = []
    for name, a, b in windows:
        clip = audio[round(a * rate):round(b * rate)]
        for channel in design["channels"]:
            y = clip.mean(axis=1) if channel == "arithmetic-mid" else clip[:,
                0 if channel == "left" else 1]
            for order in design["capture_fits"]["nuisance_orders"]:
                rows.append({"window": name, "start_seconds": a, "end_seconds": b,
                             "channel": channel,
                             **measure(y, rate, frequency, order)})
    assert len(rows) == 8 * 3 * 3
    result = {
        "scope": design["scope"],
        "bindings": {"design": binding(design_path), "runner": binding(Path(__file__)),
                     "retained_pcm": source_binding, "retained_analysis": binding(old_path)},
        "sample_rate": rate, "frequency_hz_unchanged": frequency,
        "stereo_channels_bit_identical": bool(np.array_equal(audio[:, 0], audio[:, 1])),
        "fits": rows,
        "synthetic_probe": synthetic(design["synthetic_probe"]),
        "production_dsp_changed": False,
    }
    target = Path(sys.argv[1])
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"result": str(target), "capture_fits": len(rows),
                      "synthetic_candidates": len(result["synthetic_probe"]["candidates"]),
                      "passed": True}))


if __name__ == "__main__":
    main()
