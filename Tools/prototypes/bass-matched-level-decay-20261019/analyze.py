#!/usr/bin/env python3
"""Frozen matched-level analysis of saved H1 curves; never reads or writes PCM.

See design-frozen.json for crossing ambiguity, support, slope and null scope.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np


def binding(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def fit(offsets: np.ndarray, levels: np.ndarray) -> dict:
    matrix = np.column_stack([np.ones(len(offsets)), offsets])
    intercept, slope = np.linalg.lstsq(matrix, levels, rcond=None)[0]
    residual = levels - matrix @ np.array([intercept, slope])
    denominator = np.sum((levels - levels.mean())**2)
    return {"slope_db_per_second": float(slope), "intercept_dbfs": float(intercept),
            "r_squared": float(1 - np.sum(residual**2) / denominator)
                if denominator > 0 else None,
            "max_abs_residual_db": float(np.max(np.abs(residual))),
            "endpoint_drop_db": float(levels[0] - levels[-1])}


def measure(times: np.ndarray, levels: np.ndarray, target: float,
            offsets: np.ndarray) -> dict:
    row = {"target_dbfs": target, "qualified": False}
    if len(times) != 81 or len(levels) != 81 or not np.isfinite(times).all() \
            or not np.isfinite(levels).all() or not np.all(np.diff(times) > 0) \
            or np.max(np.abs(np.diff(times) - .005)) > 1e-10:
        return row | {"failure": "invalid curve; no repair"}
    equal = np.flatnonzero(levels == target)
    strict = np.flatnonzero((levels[:-1] - target) * (levels[1:] - target) < 0)
    row["exact_samples"] = equal.tolist()
    row["strict_straddling_segments"] = strict.tolist()
    if len(equal) > 1 and np.any(np.diff(equal) == 1):
        return row | {"failure": "target-level plateau"}
    if len(equal) + len(strict) != 1:
        return row | {"failure": "absent or ambiguous crossing"}
    if len(equal):
        j = int(equal[0])
        if j == 0 or j == len(levels)-1 or not levels[j-1] > target > levels[j+1]:
            return row | {"failure": "exact hit is not a guarded downward crossing"}
        crossing = float(times[j])
    else:
        j = int(strict[0])
        if not levels[j] > target > levels[j+1]:
            return row | {"failure": "unique crossing is upward"}
        fraction = (target - levels[j]) / (levels[j+1] - levels[j])
        crossing = float(times[j] + fraction * (times[j+1] - times[j]))
    row["crossing_time_seconds"] = crossing
    supports = crossing + offsets
    if supports[0] < times[0] or supports[-1] > times[-1]:
        return row | {"failure": "fixed neighborhood lacks full support",
                      "requested_support_seconds": [float(supports[0]), float(supports[-1])]}
    interpolated = np.interp(supports, times, levels)
    return row | {"qualified": True, "failure": None,
        "support_seconds": [float(supports[0]), float(supports[-1])],
        "offsets_seconds": offsets.tolist(), "levels_dbfs": interpolated.tolist(),
        **fit(offsets, interpolated)}


def inverse(function, value: float) -> float:
    low, high = -100.0, 100.0
    for _ in range(80):
        middle = (low + high) / 2
        if function(middle) < value:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def controls(design: dict, offsets: np.ndarray) -> dict:
    times = np.arange(81) * .005
    maps = {"identity": lambda x: x,
            "affine-compressor": lambda x: .5 * (x+24) - 24,
            "curved-monotonic": lambda x: x + .75 * np.tanh((x+24)/3)}
    result, errors, failures = [], [], []
    for name, function in maps.items():
        for target in design["levels_dbfs"]:
            analytic = fit(offsets, function(inverse(function, target) - 32 * offsets))
            slopes = []
            for i in range(16):
                coordinate = inverse(function, -20.5) + .02 * i
                row = measure(times, function(coordinate - 32 * times), target, offsets)
                row.update({"map": name, "start_index": i,
                            "analytic_slope_db_per_second": analytic["slope_db_per_second"]})
                if row["qualified"]:
                    error = abs(row["slope_db_per_second"] - analytic["slope_db_per_second"])
                    row["absolute_slope_error_db_per_second"] = error
                    errors.append(error)
                    slopes.append(row["slope_db_per_second"])
                    if error > .1:
                        failures.append({"kind": "sampled-vs-analytic", "row": row})
                else:
                    failures.append({"kind": "unqualified common-map control", "row": row})
                result.append(row)
            if len(slopes) != 16 or max(slopes)-min(slopes) > .1:
                failures.append({"kind": "common-map matched-level slope spread",
                                 "map": name, "target": target, "slopes": slopes})
    separating = []
    for i in range(16):
        speed = 24.33 if i < 8 else 28.46
        coordinate = -20.5 + .02 * i
        for target in design["levels_dbfs"]:
            row = measure(times, coordinate - speed * times, target, offsets)
            row.update({"start_index": i, "known_speed_db_per_second": speed})
            if not row["qualified"] or abs(row["slope_db_per_second"] + speed) > 1e-8:
                failures.append({"kind": "separating-rate control", "row": row})
            separating.append(row)
    return {"common_map_cases": result, "separating_cases": separating,
            "max_common_map_sampled_slope_error_db_per_second": max(errors, default=None),
            "failed_contracts": failures, "passed": not failures}


def main() -> None:
    prototype = Path(__file__).resolve().parent
    design_path = prototype / "design-frozen.json"
    design = json.loads(design_path.read_text())
    repo = prototype.parents[2]
    source_path = repo / design["source_json"]
    source_binding = binding(source_path)
    assert source_binding["sha256"] == design["expected_source_sha256"]
    assert source_binding["bytes"] == design["expected_source_bytes"]
    source = json.loads(source_path.read_text())["posthoc_harmonic_result"]["rows"]
    assert [row["inferred_musical_midi"] for row in source] == design["expected_notes"]
    offsets = np.array(design["slope_offsets_seconds"])
    rows = []
    for item in source:
        for target in design["levels_dbfs"]:
            row = measure(np.array(item["times_seconds"]), np.array(item["h1_dbfs"]),
                          target, offsets)
            rows.append(row | {"segment_index": item["segment_index"],
                "inferred_musical_midi": item["inferred_musical_midi"],
                "group": "low" if item["inferred_musical_midi"] < 60 else "high"})
    assert len(rows) == design["actual_case_count"] == 80
    summaries = []
    for target in design["levels_dbfs"]:
        subsets = {group: [row for row in rows if row["group"] == group
                           and row["target_dbfs"] == target] for group in ["low", "high"]}
        summary = {"target_dbfs": target, "groups": {}}
        for group, members in subsets.items():
            slopes = [row["slope_db_per_second"] for row in members if row["qualified"]]
            summary["groups"][group] = {"total": len(members), "qualified": len(slopes),
                "signed_slope_range_db_per_second": [min(slopes), max(slopes)] if slopes else None,
                "signed_slope_median_db_per_second": float(np.median(slopes)) if slopes else None}
        if all(row["qualified"] for row in subsets["low"] + subsets["high"]):
            differences, ratios = [], []
            for low in subsets["low"]:
                for high in subsets["high"]:
                    differences.append(high["slope_db_per_second"] - low["slope_db_per_second"])
                    ratios.append(high["slope_db_per_second"] / low["slope_db_per_second"])
            summary.update({"cross_group_pairs": 64,
                "all_signed_high_minus_low_db_per_second": differences,
                "signed_difference_range_db_per_second": [min(differences), max(differences)],
                "signed_difference_median_db_per_second": float(np.median(differences)),
                "all_high_over_low_decay_speed_ratios": ratios,
                "decay_speed_ratio_range": [min(ratios), max(ratios)],
                "decay_speed_ratio_median": float(np.median(ratios))})
        else:
            summary["comparison_failure"] = "Incomplete fixed grid; no pair replacement or subset summary"
        summaries.append(summary)
    synthetic = controls(design, offsets)
    result = {"classification": design["classification"],
        "bindings": {"design": binding(design_path), "runner": binding(Path(__file__)),
                     "source_json": source_binding},
        "source_prior_harmonic_protocol_sha256": "9a1662c57f99a19ec0b22d21dc5bb377060e918bd928bc48f210864e9f62c6ca",
        "all_actual_rows": rows, "qualified_actual": sum(row["qualified"] for row in rows),
        "summaries": summaries, "synthetic_controls": synthetic,
        "no_pcm_or_hardware_execution": True, "no_production_changes": True}
    output = Path(sys.argv[1])
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"actual_qualified": result["qualified_actual"], "actual_cases": len(rows),
        "synthetic_common_map_cases": len(synthetic["common_map_cases"]),
        "synthetic_separating_cases": len(synthetic["separating_cases"]),
        "synthetic_passed": synthetic["passed"],
        "failed_synthetic_contracts": len(synthetic["failed_contracts"]), "result": str(output)}))


if __name__ == "__main__":
    main()
