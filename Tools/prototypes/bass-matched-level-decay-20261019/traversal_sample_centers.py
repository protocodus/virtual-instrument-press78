#!/usr/bin/env python3
"""Correct v1 timestamp arithmetic with original extraction-center integers.

All grids and decisions are fixed in traversal-sample-centers-design-frozen.json.
Only stored JSON and original Python source text are read; never PCM.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path
import sys

import numpy as np

from traversal import binding, crossing_brackets, inverse


def curve(times, levels, targets, fs):
    result = crossing_brackets(times, levels, targets)
    centers = np.rint(times*fs).astype(np.int64)
    if np.any(np.diff(centers) <= 0):
        return result | {"qualified": False, "failure": "nonincreasing PCM centers"}
    result["pcm_centers"] = centers.tolist()
    result["nominal_timestamps_seconds"] = times.tolist()
    if result["qualified"]:
        for bracket in result["brackets"].values():
            bracket["pcm_center_interval_samples"] = [int(centers[i]) for i in bracket["sample_indices"]]
    return result


def duration(item, higher, lower, fs):
    row = {"higher_level_dbfs": higher, "lower_level_dbfs": lower, "qualified": False}
    if not item["qualified"]:
        return row | {"failure": "curve/crossing qualification failed"}
    high = item["brackets"][str(higher)]
    low = item["brackets"][str(lower)]
    h0,h1 = high["pcm_center_interval_samples"]
    l0,l1 = low["pcm_center_interval_samples"]
    interval = [max(0,l0-h1),l1-h0]
    if interval[1] <= 0 or interval[0] > interval[1]:
        return row | {"failure": "invalid duration enclosure", "interval_samples": interval}
    return row | {"qualified": True, "failure": None,
        "interval_samples": interval, "denominator_samples_per_second": fs,
        "interval_seconds_display_only": [i/fs for i in interval],
        "higher_crossing": high, "lower_crossing": low,
        "same_sample_interval": high["sample_indices"]==low["sample_indices"]}


def difference(high,low,fs):
    if not high["qualified"] or not low["qualified"]:
        return {"qualified": False, "failure": "missing duration; no pair substitution"}
    hi,lo = high["interval_samples"],low["interval_samples"]
    interval = [hi[0]-lo[1],hi[1]-lo[0]]
    label = "high-pitch shorter" if interval[1] < 0 else \
        "high-pitch longer" if interval[0] > 0 else "overlap"
    return {"qualified": True, "high_pitch_minus_low_pitch_interval_samples": interval,
        "denominator_samples_per_second": fs,
        "difference_seconds_display_only": [i/fs for i in interval],
        "nominal_separation": label}


def intersection(rows,fs):
    if not all(row["qualified"] for row in rows):
        return {"qualified": False, "failure": "missing duration; no subset replacement"}
    lower = max(row["interval_samples"][0] for row in rows)
    upper = min(row["interval_samples"][1] for row in rows)
    return {"qualified": True, "max_lower_samples": lower, "min_upper_samples": upper,
        "denominator_samples_per_second": fs, "nonempty": lower<=upper,
        "gap_if_empty_samples": max(0,lower-upper)}


def controls(targets,pairs,fs):
    maps = {"identity": lambda x:x,
        "affine-compressor": lambda x:.5*(x+24)-24,
        "curved-monotonic": lambda x:x+.75*np.tanh((x+24)/3),
        "sharp-monotonic-review-counterexample": lambda x:x+5*np.tanh((x+24)/.005)}
    times = np.arange(81)*.005
    actual_times = np.rint(times*fs)/fs
    rows, comparisons, failures = [], [], []
    for name,function in maps.items():
        curves = [curve(times,function(inverse(function,-20.5)+.02*i-32*actual_times),targets,fs)
                  for i in range(16)]
        for lower,higher in pairs:
            expected = (inverse(function,higher)-inverse(function,lower))/32
            durations = []
            for i,item in enumerate(curves):
                row = duration(item,higher,lower,fs) | {"map": name, "start_index": i,
                    "analytic_duration_seconds": expected}
                durations.append(row)
                if not row["qualified"] or not row["interval_samples"][0]/fs <= expected <= row["interval_samples"][1]/fs:
                    failures.append({"kind": "analytic common duration not enclosed", "row": row})
                rows.append(row)
            for low in range(8):
                for high in range(8,16):
                    row = difference(durations[high],durations[low],fs) | {"map": name,
                        "higher_level_dbfs": higher,"lower_level_dbfs": lower,
                        "low_start_index": low,"high_start_index": high}
                    if not row["qualified"] or row["nominal_separation"]!="overlap":
                        failures.append({"kind": "common-map pair intervals fail overlap", "row": row})
                    comparisons.append(row)
    base = np.linspace(-20.,-28.,81)
    edges=[]
    for name,levels,target,expected in [
        ("ordinary-downward",base,-23.97,True),
        ("exact-singleton",base,-24.,True),
        ("absent-target",base,-30.,False),
        ("unique-upward",base[::-1],-24.,False),
        ("multiple-crossings",base+3*np.sin(np.arange(81)*np.pi/10),-24.,False),
        ("plateau",np.concatenate((base[:39],[-24.,-24.,-24.],base[42:])),-24.,False)]:
        row=curve(times,levels,[target],fs)|{"name":name,"expected_qualified":expected}
        if row["qualified"]!=expected:
            failures.append({"kind":"crossing-edge behavior","row":row})
        edges.append(row)
    return {"duration_cases":rows,"pair_comparisons":comparisons,
        "crossing_edges":edges,"failed_contracts":failures,"passed":not failures}


def main():
    prototype=Path(__file__).resolve().parent
    repo=prototype.parents[2]
    design_path=prototype/"traversal-sample-centers-design-frozen.json"
    design=json.loads(design_path.read_text())
    old_design_path=prototype/"traversal-design-frozen.json"
    old_design=json.loads(old_design_path.read_text())
    source_path=repo/design["source_json"]
    extractor_path=Path(design["original_extractor"])
    protocol_path=Path(design["original_extractor_protocol"])
    header_path=repo/design["header_inventory"]
    v1path=repo/design["original_traversal_result"]
    for path,key in [(source_path,"expected_source_sha256"),
        (extractor_path,"expected_extractor_sha256"),
        (protocol_path,"expected_extractor_protocol_sha256"),
        (header_path,"expected_header_inventory_sha256"),
        (v1path,"expected_original_traversal_result_sha256"),
        (prototype/"traversal.py","expected_original_traversal_runner_sha256")]:
        assert binding(path)["sha256"]==design[key]
    source=json.loads(source_path.read_text())["posthoc_harmonic_result"]["rows"]
    protocol=json.loads(protocol_path.read_text())
    assert protocol["source_sha256"]==design["expected_original_pcm_sha256_from_retained_protocol"]
    inventory=json.loads(header_path.read_text())["header_inventory"]
    header=next(item for item in inventory if item["member"]=="synth_bass_1.wav")
    fmt=next(item["fields"]for item in header["chunks"]if item["id"]=="fmt ")
    assert fmt[0]==1 and fmt[1]==1 and fmt[2]==44100 and fmt[5]==16
    fs=int(fmt[2])
    assert [item["inferred_musical_midi"]for item in source]==old_design["expected_notes"]
    targets=old_design["levels_dbfs"]
    pairs=list(itertools.combinations(targets,2))
    curves=[]
    hops=[]
    rounding=[]
    for item,original in zip(source,protocol["rows"]):
        assert item["times_seconds"]==original["times_seconds"]
        times=np.array(item["times_seconds"])
        row=curve(times,np.array(item["h1_dbfs"]),targets,fs)
        centers=np.array(row["pcm_centers"])
        assert np.isin(np.diff(centers),[220,221]).all()
        hops.extend(np.diff(centers).tolist())
        rounding.extend(np.abs(centers/fs-times).tolist())
        # A mathematical half-sample plus two representation ULPs; not an
        # empirical H1 uncertainty or an interval-separation tolerance.
        assert np.all(np.abs(centers/fs-times)<=.5/fs+2*np.spacing(np.abs(times)))
        curves.append(row|{"segment_index":item["segment_index"],
            "inferred_musical_midi":item["inferred_musical_midi"],
            "group":"low"if item["inferred_musical_midi"]<60 else"high"})
    v1=json.loads(v1path.read_text())
    for new,old in zip(curves,v1["curve_qualification"]):
        assert new["qualified"]==old["qualified"]
        if new["qualified"]:
            for target in targets:
                assert new["brackets"][str(target)]["sample_indices"]==old["brackets"][str(target)]["sample_indices"]
                assert new["brackets"][str(target)]["time_interval_seconds"]==old["brackets"][str(target)]["time_interval_seconds"]
    durations,comparisons,summaries=[],[],[]
    for lower,higher in pairs:
        groups={"low":[],"high":[]}
        for item in curves:
            row=duration(item,higher,lower,fs)|{"segment_index":item["segment_index"],
                "inferred_musical_midi":item["inferred_musical_midi"],"group":item["group"]}
            groups[item["group"]].append(row)
            durations.append(row)
        pair_rows=[]
        for low in groups["low"]:
            for high in groups["high"]:
                row=difference(high,low,fs)|{"higher_level_dbfs":higher,"lower_level_dbfs":lower,
                    "low_pitch":low["inferred_musical_midi"],"high_pitch":high["inferred_musical_midi"]}
                pair_rows.append(row)
                comparisons.append(row)
        counts={name:sum(row.get("nominal_separation")==name for row in pair_rows)
                for name in ["high-pitch shorter","high-pitch longer","overlap"]}
        counts["unqualified"]=sum(not row["qualified"]for row in pair_rows)
        summaries.append({"higher_level_dbfs":higher,"lower_level_dbfs":lower,
            "cross_group_pair_counts":counts,
            "all16_interval_intersection":intersection(groups["low"]+groups["high"],fs),
            "low8_interval_intersection":intersection(groups["low"],fs),
            "high8_interval_intersection":intersection(groups["high"],fs)})
    changes=[]
    for new,old in zip(comparisons,v1["all_cross_group_comparisons"]):
        assert all(new[key]==old[key]for key in ["higher_level_dbfs","lower_level_dbfs","low_pitch","high_pitch","qualified"])
        if new.get("nominal_separation")!=old.get("nominal_separation"):
            changes.append({"v1":old,"v2":new})
    synthetic=controls(targets,pairs,fs)
    result={"classification":design["classification"],
        "bindings":{"design":binding(design_path),"runner":binding(Path(__file__)),
            "qualification_runner_unchanged":binding(prototype/"traversal.py"),
            "v1_design_unchanged":binding(old_design_path),"v1_result_unchanged":binding(v1path),
            "source_json":binding(source_path),"original_extractor":binding(extractor_path),
            "original_extractor_protocol":binding(protocol_path),"header_inventory":binding(header_path)},
        "source_sample_rate_hz":fs,"source_header_fields":fmt,
        "center_count":sum(len(row["pcm_centers"])for row in curves),
        "all_hop_counts":{str(i):hops.count(i)for i in sorted(set(hops))},
        "max_label_center_rounding_seconds":max(rounding),
        "curve_qualification":curves,"all_duration_enclosures":durations,
        "all_cross_group_comparisons":comparisons,"summaries":summaries,
        "v1_to_v2_classification_changes":changes,"synthetic_controls":synthetic,
        "no_interpolation_used_for_followup":True,"no_pcm_read_or_hardware_execution":True,
        "no_production_changes":True}
    assert len(curves)==16 and len(durations)==160 and len(comparisons)==640
    output=Path(sys.argv[1])
    output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"curves":len(curves),"durations":len(durations),"comparisons":len(comparisons),
        "classification_changes":len(changes),"synthetic_passed":synthetic["passed"],
        "failed_synthetic_contracts":len(synthetic["failed_contracts"]),"result":str(output)}))


if __name__=="__main__":
    main()
