#!/usr/bin/env python3
"""Frozen public-API experiment: independent voices versus shared nonlinearity.

See adjacent design-frozen.json; reads no hardware audio and writes no PCM.
Compile Probe.cpp against the unchanged shipping Press78Engine.cpp first.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys

import numpy as np


def binding(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x**2)))


def relative(a: np.ndarray, b: np.ndarray) -> float:
    return rms(a - b) / max(rms(b), 1e-30)


def main() -> None:
    prototype = Path(__file__).resolve().parent
    design_path = prototype / "design-frozen.json"
    design = json.loads(design_path.read_text())
    executable, output = Path(sys.argv[1]), Path(sys.argv[2])
    cases = []
    for mode, tl, gain, notes in itertools.product(design["modes"],
            design["carrier_raw_tl"], design["master_gain"], design["note_sets"]):
        cases.append({"mode": mode, "tl": tl, "master_gain": gain, "notes": notes})
    assert len(cases) == design["case_count"] == 72
    stdin = "".join(f"{c['mode']} {c['tl']} {c['master_gain']} {len(c['notes'])} "
                    f"{c['notes'][0]} {c['notes'][-1]}\n" for c in cases)
    process = subprocess.run([str(executable.resolve())], input=stdin.encode(),
                             capture_output=True, check=True)
    frames = round(design["sample_rate_hz"] * design["duration_seconds"])
    pcm = np.frombuffer(process.stdout, dtype=np.float32).reshape(len(cases), frames)
    assert np.isfinite(pcm).all()
    a, b = [round(t * design["sample_rate_hz"]) for t in design["analysis_seconds"]]
    x = pcm[:, a:b].astype(np.float64)
    f1, f2 = [440 * 2**((note - 69) / 12) for note in design["notes"]]
    harmonic_frequencies = [h * frequency for frequency in [f1, f2]
                            for h in range(1, 13)]
    imd = [f2 - f1, f1 + f2, abs(2*f1 - f2), 2*f2 - f1,
           2*f1 + f2, 2*f2 + f1]
    frequencies = np.array(harmonic_frequencies + imd)
    t = (np.arange(b - a) - (b - a - 1) / 2) / design["sample_rate_hz"]
    angle = 2 * np.pi * t[:, None] * frequencies
    matrix = np.column_stack([np.ones(len(t)), np.sin(angle), np.cos(angle)])
    weight = np.hanning(len(t))
    weighted_matrix = matrix * weight[:, None]
    # One common linear analysis operation for every sample, no per-case fit
    # of timing/frequency/gain or nonlinear parameters.
    inverse = np.linalg.pinv(weighted_matrix)

    def amplitudes(y: np.ndarray) -> np.ndarray:
        c = inverse @ (y * weight)
        n = len(frequencies)
        return np.hypot(c[1:n+1], c[n+1:])

    rows, lookup = [], {}
    for index, case in enumerate(cases):
        amp = amplitudes(x[index])
        row = case | {"rms": rms(x[index]), "peak": float(np.max(np.abs(x[index]))),
            "full_float32_sha256": hashlib.sha256(pcm[index].tobytes()).hexdigest(),
            "fixed_frequency_amplitudes": amp.tolist()}
        rows.append(row)
        lookup[(case["mode"], case["tl"], case["master_gain"], tuple(case["notes"]))] = index
    failures = []
    additivity = []
    for mode, tl, gain in itertools.product(design["modes"], design["carrier_raw_tl"],
                                           design["master_gain"]):
        indexes = [lookup[(mode, tl, gain, tuple(notes))] for notes in design["note_sets"]]
        one, two, chord = [x[index] for index in indexes]
        residual = chord - one - two
        error = rms(residual) / max(rms(chord), 1e-30)
        imd_amplitudes = amplitudes(residual)[24:]
        ratio = float(np.sqrt(np.sum(imd_amplitudes**2) / 2)) / max(rms(chord), 1e-30)
        additivity.append({"mode": mode, "tl": tl, "master_gain": gain,
            "residual_rms_relative_to_chord": error,
            "six_imd_witnesses_rms_relative_to_chord": ratio,
            "six_imd_witness_amplitudes": imd_amplitudes.tolist()})
        if mode in ["linear", "circuit", "fm0", "fm6"] and error >= 2e-6:
            failures.append({"contract": "independent-voice additivity", "mode": mode,
                             "tl": tl, "master_gain": gain, "observed": error})
    master = []
    for mode, tl, notes in itertools.product(design["modes"], design["carrier_raw_tl"],
                                            design["note_sets"]):
        low, high = [x[lookup[(mode, tl, gain, tuple(notes))]] for gain in [0.25, 2.0]]
        error = relative(high / 2, low / .25)
        master.append({"mode": mode, "tl": tl, "notes": notes,
                       "gain_removed_relative_rms_error": error,
                       "high_over_low_rms": rms(high) / rms(low)})
        if mode != "limit" and error >= 2e-6:
            failures.append({"contract": "post-nonlinearity master placement",
                             "mode": mode, "tl": tl, "notes": notes, "observed": error})
    carrier = []
    expected_gain = 10**(-24 * .75 / 20)
    for mode, gain, notes in itertools.product(design["modes"], design["master_gain"],
                                              design["note_sets"]):
        loud, quiet = [x[lookup[(mode, tl, gain, tuple(notes))]] for tl in [0, 24]]
        carrier.append({"mode": mode, "master_gain": gain, "notes": notes,
                        "nominal_tl_gain_removed_relative_rms_error":
                            relative(quiet / expected_gain, loud)})
    limit_comparisons = []
    for tl, gain, notes in itertools.product(design["carrier_raw_tl"],
                                            design["master_gain"], design["note_sets"]):
        baseline, limited = [x[lookup[(mode, tl, gain, tuple(notes))]]
                             for mode in ["linear", "limit"]]
        error = relative(limited, baseline)
        limit_comparisons.append({"tl": tl, "master_gain": gain, "notes": notes,
                                  "limit_vs_linear_relative_rms_error": error})
        if gain == .25 and not np.array_equal(limited, baseline):
            failures.append({"contract": "low-master transparent limiter", "tl": tl,
                             "notes": notes, "observed": error})
    repo = prototype.parents[2]
    result = {"scope": design["scope"], "case_count": len(cases),
        "bindings": {"design": binding(design_path), "native_probe": binding(prototype / "Probe.cpp"),
                     "analysis_runner": binding(Path(__file__)), "executable": binding(executable)},
        "shipping_source_bindings": [binding(p) for p in sorted((repo / "Source/DSP").glob("*")) if p.is_file()],
        "frequencies_hz": frequencies.tolist(), "imd_witness_frequencies_hz": imd,
        "matrix_condition_number": float(np.linalg.cond(weighted_matrix)),
        "cases": rows, "additivity": additivity, "master_gain_placement": master,
        "carrier_level_dependence": carrier, "limit_vs_linear": limit_comparisons,
        "failed_contracts": failures, "passed": not failures,
        "rendered_seconds": frames / design["sample_rate_hz"] * len(cases),
        "no_pcm_retained": True, "no_hardware_calibration": True,
        "native_stderr": process.stderr.decode()}
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"cases": len(cases), "passed": not failures,
                      "failed_contracts": failures, "result": str(output)}))


if __name__ == "__main__":
    main()
