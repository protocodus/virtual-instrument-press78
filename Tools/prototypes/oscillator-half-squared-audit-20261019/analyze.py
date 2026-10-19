#!/usr/bin/env python3
"""Derived cross-waveform diagnostics, exactly the adjacent frozen protocol.

No PCM is opened and no harmonic/filter/phase/frequency is fit. The input is
the separately source-bound signed-square audit's already frozen coefficients.
Unknown capture response is retained as an unknown, never estimated for use.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np


def binding(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def wrapped(x: float) -> float:
    return float(np.angle(np.exp(1j * x)))


def coefficient(row: dict, n: int) -> complex:
    return complex(*row["coefficients"][n - 1])


def phase_invariant(row: dict, n: int) -> float:
    return wrapped(np.angle(coefficient(row, n)) - n * np.angle(coefficient(row, 1)))


def response_delta(a: dict, b: dict, n: int, ideal_a_db: float, ideal_b_db: float) -> dict:
    delta = ((b["relative_db"][n - 1] - ideal_b_db)
             - (a["relative_db"][n - 1] - ideal_a_db))
    frequency_delta = b["f0_hz"] - a["f0_hz"]
    # Conditional mean-value inequality only; no slope bound is assumed.
    required = abs(delta) / ((n + 1) * abs(frequency_delta))
    return {"table_a": a["table"], "table_b": b["table"],
            "support_a": a["part"], "support_b": b["part"], "harmonic": n,
            "f0_b_minus_a_hz": frequency_delta,
            "conditional_normalized_response_b_minus_a_db": delta,
            "necessary_max_response_slope_at_least_db_per_hz": required}


def synthetic(design: dict) -> dict:
    count = design["period_samples"]
    phase = 2 * np.pi * np.arange(count // 2) / count
    sine = np.sin(phase)
    families = [sine, sine**2, sine**3,
                np.rint(7 * sine**2) / 7, np.floor(31 * sine**2) / 31]
    kernel = np.zeros(count)
    kernel[:len(design["filter"])] = design["filter"]
    transfer = np.fft.rfft(kernel)
    output, checks = [], 0
    for name, positive in zip(design["positive_half_families"], families):
        q = np.concatenate((positive, -positive))
        r = np.concatenate((positive, np.zeros_like(positive)))
        qf, rf = np.fft.rfft(q) * (2 / count), np.fft.rfft(r) * (2 / count)
        odd = np.arange(1, count // 2, 2)
        error = float(np.max(np.abs(rf[odd] - .5 * qf[odd])))
        assert error <= design["absolute_tolerance"]
        checks += 1
        filtered_q, filtered_r = qf * transfer, rf * transfer
        filtered_error = float(np.max(np.abs(filtered_r[odd] - .5 * filtered_q[odd])))
        assert filtered_error <= design["absolute_tolerance"]
        checks += 1
        # Real gains and integer circular shifts alter gain/origin, not shape.
        bins = np.arange(len(qf))
        shifted_q = (filtered_q * design["gain_q"]
                     * np.exp(-2j * np.pi * bins * design["shift_q"] / count))
        shifted_r = (filtered_r * design["gain_r"]
                     * np.exp(-2j * np.pi * bins * design["shift_r"] / count))
        harmonic_rows = []
        for n in design["harmonics"]:
            if min(abs(qf[1]), abs(qf[n]), abs(rf[1]), abs(rf[n])) <= 1e-12:
                harmonic_rows.append({"harmonic": n, "phase_status": "undefined analytic/numerical coefficient null",
                                      "coefficient_identity_error": float(abs(rf[n] - .5 * qf[n]))})
                continue
            magnitude_error = float(abs(abs(shifted_r[n] / shifted_r[1])
                                        - abs(shifted_q[n] / shifted_q[1])))
            phase_error = wrapped((np.angle(shifted_r[n]) - n * np.angle(shifted_r[1]))
                                  - (np.angle(shifted_q[n]) - n * np.angle(shifted_q[1])))
            assert magnitude_error <= design["absolute_tolerance"]
            assert abs(phase_error) <= design["absolute_tolerance"]
            checks += 2
            harmonic_rows.append({"harmonic": n, "normalized_magnitude_error": magnitude_error,
                                  "normalized_phase_error_radians": phase_error})
        output.append({"family": name, "maximum_odd_coefficient_identity_error": error,
                       "maximum_filtered_odd_coefficient_identity_error": filtered_error,
                       "normalized_harmonics": harmonic_rows})
    return {"passed": True, "assertions": checks, "families": output}


def main() -> None:
    root = Path(__file__).resolve().parent
    design_path = root / "design-frozen.json"
    design = json.loads(design_path.read_text())
    for expected in design["inputs"].values():
        actual = binding(Path(expected["path"]))
        assert actual == expected
    source_path = Path(design["inputs"]["build/oscillator-signed-square-audit-20261019/result.json"]["path"])
    source = json.loads(source_path.read_text())
    rows = []
    for row in source["capture_rows"]:
        original = row["channels"]["mid"]
        rows.append({"table": row["table"], "part": row["part"],
                     "start_seconds": row["start"], "end_seconds": row["end"],
                     "f0_hz": row["f0_hz"], "coefficients": original["complex_sin_coefficients"],
                     "amplitudes": original["amplitudes"], "relative_db": original["harmonic_db_relative_fundamental"],
                     "rms": original["rms"], "fit_residual_relative_rms": original["residual_relative_rms"]})
    assert len(rows) == 16
    by_table = {table: [row for row in rows if row["table"] == table] for table in range(4)}
    assert all(len(part) == 4 for part in by_table.values())
    comparisons = []
    for a in by_table[1]:
        for b in by_table[3]:
            for n in [3, 5, 7, 9, 11]:
                item = response_delta(a, b, n, 0, 0)
                item["gain_time_shift_invariant_phase_b_minus_a_radians"] = wrapped(phase_invariant(b, n) - phase_invariant(a, n))
                comparisons.append(item)
    even = []
    half_h2_db = 20 * math.log10(4 / (3 * math.pi))
    squared_h2_db = 20 * math.log10(3 * math.pi / 16)
    for a in by_table[2]:
        for b in by_table[3]:
            even.append(response_delta(a, b, 2, half_h2_db, squared_h2_db))
    nulls = []
    for row in rows:
        null_harmonics = design["derived_capture"]["nulls"][str(row["table"])]
        amplitudes = np.asarray(row["amplitudes"])
        ratio = float(np.linalg.norm(amplitudes[np.asarray(null_harmonics) - 1]) / np.linalg.norm(amplitudes))
        nulls.append({"table": row["table"], "part": row["part"],
                      "analytically_absent_harmonics": null_harmonics,
                      "null_coefficient_vector_norm_relative_all_twelve": ratio,
                      "null_vector_db_relative_all_twelve": 20 * math.log10(ratio)})
    native_path = Path(sys.argv[1])
    native = json.loads(native_path.read_text())
    assert native["passed"] and native["assertions"] == 4 * 65536 + 25
    result = {
        "date": design["date"], "classification": design["classification"],
        "bindings": {"design": binding(design_path), "analysis_tool": binding(Path(__file__)),
                     "native_source": binding(root / "HalfSquaredProbe.cpp"),
                     "native_receipt": binding(native_path), "inputs": design["inputs"]},
        "native_probe": native, "copied_capture_rows": rows,
        "signed_square_vs_half_squared": comparisons, "half_vs_half_squared_h2": even,
        "analytic_null_diagnostics": nulls, "synthetic_probe": synthetic(design["synthetic_probe"]),
        "hardware_model_identified": False, "production_dsp_changed": False,
        "limits": ["The distinct measured frequencies require an unmeasured response-smoothness assumption to reject common LTI using unequal nonzero harmonic ratios.",
                   "Frequency estimates, partial-fit residuals, slow envelope/phase changes, effects, nonlinear output and capture remain unresolved.",
                   "Analytic-null coefficients cannot arise from a strictly static ideal waveform and LTI alone, but are not localized to OPU circuitry.",
                   "No filter, curve, quantizer width, physical clock/DAC/supply constant, new noise or product setting is fit or adopted."]}
    target = Path(sys.argv[2])
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": True, "copied_capture_rows": len(rows), "odd_comparisons": len(comparisons),
                      "even_comparisons": len(even), "null_diagnostics": len(nulls),
                      "native_assertions": native["assertions"], "synthetic_assertions": result["synthetic_probe"]["assertions"]}))


if __name__ == "__main__":
    main()
