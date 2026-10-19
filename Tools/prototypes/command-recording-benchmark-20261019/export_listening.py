#!/usr/bin/env python3
"""One authorized listening-copy export, never a native render or metric fit.

listening-design-frozen.json binds exact stored pair-RMS gain × common safety
from key.json. The original metric PCM, original result and all old scores stay
unchanged. Float64 multiply by the stored combined gain, one Float32 rounding.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import math

import numpy as np
from scipy.io import wavfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("frozen_recording_runner", HERE / "run.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def main():
    plan_path = HERE / "listening-design-frozen.json"
    plan = runner.read(plan_path)
    for row in plan["inputs"]:
        runner.verify(row)
    if plan["exporter_sha256"] != runner.sha(Path(__file__)):
        raise ValueError("Listening exporter changed after freeze")
    design = runner.read(HERE / "design-frozen.json")
    output = ROOT / plan["output"]
    if output.exists():
        raise ValueError("Never overwrite or repeat this listening export")
    runner.budget(design, plan["maximum_output_bytes"])
    output.mkdir()
    runner.write_new(output / "before-export.json", {"plan": runner.record(plan_path), "inputs": plan["inputs"], "formula": plan["formula"]})
    rows = []
    try:
        for item in plan["copies"]:
            runner.verify(item["source"])
            rate, source = wavfile.read(item["source"]["path"], mmap=True)
            if rate != 48000 or source.dtype != np.float32 or source.ndim != 2 or source.shape[1] != 2:
                raise ValueError("Unexpected retained focus format")
            # No recomputed trim: use the exact already-stored binary64 values.
            gain = item["listening_pair_RMS_gain"]
            safety = item["common_pair_listening_safety"]
            if not all(x is not None and math.isfinite(x) and x > 0 for x in (gain, safety)):
                raise ValueError("No finite frozen listening gain")
            combined = gain * safety
            adjusted = (source.astype(np.float64) * combined).astype(np.float32)
            if not np.isfinite(adjusted).all():
                raise ValueError("Nonfinite listening copy")
            runner.budget(design, adjusted.nbytes + 256 + 1024 * 1024)
            folder = output / str(item["support"])
            folder.mkdir(exist_ok=True)
            path = folder / (item["letter"] + ".wav")
            if path.exists():
                raise ValueError("Existing listening file")
            wavfile.write(path, 48000, adjusted)
            rr, check = wavfile.read(path, mmap=True)
            if rr != rate or check.dtype != np.float32 or not np.array_equal(check, adjusted):
                raise ValueError("Listening file copy/rounding mismatch")
            rows.append({**item, "audio": runner.record(path), "combined_gain": combined,
                         "source_float32_support_sha256": hashlib.sha256(source.tobytes(order="C")).hexdigest(),
                         "output_float32_support_sha256": hashlib.sha256(adjusted.tobytes(order="C")).hexdigest(),
                         "output_rms": float(np.sqrt(np.mean(adjusted.astype(float) ** 2))),
                         "output_peak": float(np.max(np.abs(adjusted)))})
            del check, adjusted, source
        for source in plan["inputs"]:
            runner.verify(source)
        pairs = {}
        for support in plan["supports"]:
            a, b = [next(row for row in rows if row["support"] == support and row["letter"] == letter) for letter in ("A", "B")]
            relative = abs(a["output_rms"] - b["output_rms"]) / max(a["output_rms"], b["output_rms"])
            if relative > 1e-7:
                raise ValueError("Listening RMS equality exceeds Float32 rounding tolerance")
            pairs[str(support)] = {"relative_rms_difference": relative, "A_rms": a["output_rms"], "B_rms": b["output_rms"]}
        key = "# Frozen listening key\n\nA: unchanged shipping Engine baseline.\nB: complete one-owner command consumer.\n\nOnly unchanged/ascending_track; supports65/93/97/99/199/200. Each stereo file uses its exact pre-existing key.json pair-RMS gain multiplied by the same support safety. There is no new fit, normalization, DSP replay, preference or adoption decision. Raw scoring PCM and original scores remain unchanged. This compares bundled command policy, with Reverb audio still unsupported.\n"
        key_path = output / "key.md"
        runner.budget(design, len(key.encode()) + 1024 * 1024)
        with key_path.open("x") as stream:
            stream.write(key)
        runner.write_new(output / "manifest.json", {"status": "pass", "classification": "Constant-gain listening copies only; not DSP/native replay or new scoring.", "plan": runner.record(plan_path), "formula": plan["formula"], "rows": rows, "pairs": pairs, "key": runner.record(key_path), "original_result_unchanged": plan["inputs"][0], "scorer_calls": 0, "new_fit": False})
        runner.budget(design)
        print(json.dumps({"status": "pass", "files": len(rows), "manifest": runner.record(output / "manifest.json")}))
    except BaseException as error:
        runner.write_new(output / "failure.json", {"error": repr(error), "partial_outputs_retained": True})
        raise


if __name__ == "__main__":
    main()
