#!/usr/bin/env python3
"""Separate frozen bracket-duration follow-up; no slope interpolation or PCM.

See traversal-design-frozen.json for the reviewed restricted null and limits.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
import sys

import numpy as np


def binding(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def crossing_brackets(times: np.ndarray, levels: np.ndarray, targets: list) -> dict:
    result = {"qualified": False}
    if len(times) != 81 or len(levels) != 81 or not np.isfinite(times).all() \
            or not np.isfinite(levels).all() or not np.all(np.diff(times) > 0) \
            or np.max(np.abs(np.diff(times)-.005)) > 1e-10:
        return result | {"failure": "malformed curve; no repair"}
    differences = np.diff(levels)
    result["nondecreasing_sample_pairs"] = np.flatnonzero(differences >= 0).tolist()
    if np.any(differences >= 0):
        return result | {"failure": "curve is not globally strictly decreasing; no repair"}
    brackets = {}
    for target in targets:
        equal = np.flatnonzero(levels == target)
        strict = np.flatnonzero((levels[:-1]-target) * (levels[1:]-target) < 0)
        if len(equal) + len(strict) != 1:
            return result | {"failure": "absent or ambiguous target", "target_dbfs": target}
        if len(equal):
            j = int(equal[0])
            if j == 0 or j == len(levels)-1 or not levels[j-1] > target > levels[j+1]:
                return result | {"failure": "unguarded exact target", "target_dbfs": target}
            bracket = [float(times[j]), float(times[j])]
            indices = [j, j]
        else:
            j = int(strict[0])
            if not levels[j] > target > levels[j+1]:
                return result | {"failure": "upward target crossing", "target_dbfs": target}
            bracket = [float(times[j]), float(times[j+1])]
            indices = [j, j+1]
        brackets[str(target)] = {"level_dbfs": target,
            "sample_indices": indices, "time_interval_seconds": bracket}
    return result | {"qualified": True, "failure": None, "brackets": brackets}


def duration(curve: dict, higher: int, lower: int) -> dict:
    row = {"higher_level_dbfs": higher, "lower_level_dbfs": lower, "qualified": False}
    if not curve["qualified"]:
        return row | {"failure": "curve/crossing qualification failed"}
    high = curve["brackets"][str(higher)]
    low = curve["brackets"][str(lower)]
    h_lo, h_hi = high["time_interval_seconds"]
    l_lo, l_hi = low["time_interval_seconds"]
    interval = [max(0.0, l_lo-h_hi), l_hi-h_lo]
    if interval[1] <= 0 or interval[0] > interval[1]:
        return row | {"failure": "invalid traversal enclosure", "interval_seconds": interval}
    return row | {"qualified": True, "failure": None, "interval_seconds": interval,
                  "width_seconds": interval[1]-interval[0],
                  "higher_crossing": high, "lower_crossing": low,
                  "same_sample_interval": high["sample_indices"] == low["sample_indices"]}


def difference(high_pitch: dict, low_pitch: dict) -> dict:
    if not high_pitch["qualified"] or not low_pitch["qualified"]:
        return {"qualified": False, "failure": "missing duration; no pair substitution"}
    high, low = high_pitch["interval_seconds"], low_pitch["interval_seconds"]
    delta = [high[0]-low[1], high[1]-low[0]]
    label = "high-pitch shorter" if delta[1] < 0 else \
        "high-pitch longer" if delta[0] > 0 else "overlap"
    return {"qualified": True, "high_pitch_minus_low_pitch_interval_seconds": delta,
            "nominal_separation": label}


def inverse(function, value: float) -> float:
    low, high = -100.0, 100.0
    for _ in range(80):
        middle = (low+high)/2
        if function(middle) < value:
            low = middle
        else:
            high = middle
    return (low+high)/2


def controls(targets: list, pairs: list) -> dict:
    maps = {"identity": lambda x: x,
            "affine-compressor": lambda x: .5*(x+24)-24,
            "curved-monotonic": lambda x: x+.75*np.tanh((x+24)/3),
            "sharp-monotonic-review-counterexample": lambda x: x+5*np.tanh((x+24)/.005)}
    times = np.arange(81)*.005
    rows, comparisons, failed = [], [], []
    for name, function in maps.items():
        curves = []
        for i in range(16):
            coordinate = inverse(function, -20.5)+.02*i
            curves.append(crossing_brackets(times, function(coordinate-32*times), targets))
        for lower, higher in pairs:
            durations = []
            expected = (inverse(function, higher)-inverse(function, lower))/32
            for i, curve in enumerate(curves):
                row = duration(curve, higher, lower) | {"map": name, "start_index": i,
                    "analytic_duration_seconds": expected}
                durations.append(row)
                if not row["qualified"] or not row["interval_seconds"][0] <= expected <= row["interval_seconds"][1]:
                    failed.append({"kind": "analytic duration not enclosed", "row": row})
                rows.append(row)
            for low in range(8):
                for high in range(8,16):
                    row = difference(durations[high], durations[low]) | {"map": name,
                        "higher_level_dbfs": higher, "lower_level_dbfs": lower,
                        "low_start_index": low, "high_start_index": high}
                    if not row["qualified"] or row["nominal_separation"] != "overlap":
                        failed.append({"kind": "common-map intervals fail overlap", "row": row})
                    comparisons.append(row)
    base = np.linspace(-20.0, -28.0, 81)
    edge_rows = []
    for name, levels, target, expected in [
            ("ordinary-downward", base, -23.97, True),
            ("exact-singleton", base, -24.0, True),
            ("absent-target", base, -30.0, False),
            ("unique-upward", base[::-1], -24.0, False),
            ("multiple-crossings", base+3*np.sin(np.arange(81)*np.pi/10), -24.0, False),
            ("plateau", np.concatenate((base[:39], [-24., -24., -24.], base[42:])), -24.0, False)]:
        row = crossing_brackets(times, levels, [target]) | {"name": name,
                                                           "expected_qualified": expected}
        if row["qualified"] != expected:
            failed.append({"kind": "crossing-edge behavior", "row": row})
        edge_rows.append(row)
    return {"duration_cases": rows, "pair_comparisons": comparisons,
            "crossing_edges": edge_rows, "failed_contracts": failed, "passed": not failed}


def intersection(rows: list) -> dict:
    if not all(row["qualified"] for row in rows):
        return {"qualified": False, "failure": "missing duration; no subset replacement"}
    lower = max(row["interval_seconds"][0] for row in rows)
    upper = min(row["interval_seconds"][1] for row in rows)
    return {"qualified": True, "max_lower_seconds": lower, "min_upper_seconds": upper,
            "nonempty": lower <= upper, "gap_if_empty_seconds": max(0.0, lower-upper)}


def main() -> None:
    prototype = Path(__file__).resolve().parent
    design_path = prototype / "traversal-design-frozen.json"
    design = json.loads(design_path.read_text())
    repo = prototype.parents[2]
    source_path = repo / design["source_json"]
    source_binding = binding(source_path)
    assert source_binding["sha256"] == design["expected_source_sha256"]
    source = json.loads(source_path.read_text())["posthoc_harmonic_result"]["rows"]
    assert [row["inferred_musical_midi"] for row in source] == design["expected_notes"]
    targets = design["levels_dbfs"]
    pairs = list(itertools.combinations(targets,2))
    assert len(pairs) == 10
    curves = []
    for item in source:
        curves.append(crossing_brackets(np.array(item["times_seconds"]),
            np.array(item["h1_dbfs"]), targets) | {"segment_index": item["segment_index"],
            "inferred_musical_midi": item["inferred_musical_midi"],
            "group": "low" if item["inferred_musical_midi"] < 60 else "high"})
    durations, comparisons, summaries = [], [], []
    for lower, higher in pairs:
        group = {"low": [], "high": []}
        for item in curves:
            row = duration(item,higher,lower) | {"segment_index": item["segment_index"],
                "inferred_musical_midi": item["inferred_musical_midi"], "group": item["group"]}
            group[item["group"]].append(row)
            durations.append(row)
        pair_rows = []
        for low in group["low"]:
            for high in group["high"]:
                row = difference(high,low) | {"higher_level_dbfs": higher,
                    "lower_level_dbfs": lower,
                    "low_pitch": low["inferred_musical_midi"],
                    "high_pitch": high["inferred_musical_midi"]}
                pair_rows.append(row)
                comparisons.append(row)
        counts = {name: sum(row.get("nominal_separation") == name for row in pair_rows)
                  for name in ["high-pitch shorter", "high-pitch longer", "overlap"]}
        counts["unqualified"] = sum(not row["qualified"] for row in pair_rows)
        summaries.append({"higher_level_dbfs": higher, "lower_level_dbfs": lower,
            "cross_group_pair_counts": counts,
            "all16_interval_intersection": intersection(group["low"]+group["high"]),
            "low8_interval_intersection": intersection(group["low"]),
            "high8_interval_intersection": intersection(group["high"])})
    assert len(curves)==16 and len(durations)==160 and len(comparisons)==640
    synthetic = controls(targets,pairs)
    result = {"classification": design["classification"],
        "bindings": {"design": binding(design_path), "runner": binding(Path(__file__)),
                     "source_json": source_binding,
                     "original_slope_result_unchanged": binding(repo/"build/bass-matched-level-decay-20261019/result.json")},
        "curve_qualification": curves, "all_duration_enclosures": durations,
        "all_cross_group_comparisons": comparisons, "summaries": summaries,
        "synthetic_controls": synthetic,
        "no_interpolation_or_slope_used_for_followup": True,
        "no_pcm_or_hardware_execution": True, "no_production_changes": True}
    output = Path(sys.argv[1])
    output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"curves_qualified": sum(row["qualified"]for row in curves),
        "duration_enclosures": len(durations), "cross_group_comparisons": len(comparisons),
        "synthetic_duration_cases": len(synthetic["duration_cases"]),
        "synthetic_pair_comparisons": len(synthetic["pair_comparisons"]),
        "synthetic_passed": synthetic["passed"],
        "failed_synthetic_contracts": len(synthetic["failed_contracts"]), "result": str(output)}))


if __name__ == "__main__":
    main()
