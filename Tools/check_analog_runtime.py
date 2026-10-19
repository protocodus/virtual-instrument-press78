#!/usr/bin/env python3
"""Independent native impulse comparison with the original MNA-derived filter.

Unlike generate_analog.py's frequency-domain coefficient checks, this exercises
the compiled C++ processing equations and state for a full1-second impulse.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "Tools/reference"))
    from circuit.model import build_circuit

    circuit, output = build_circuit(model="pss480")
    rows = []
    with tempfile.TemporaryDirectory(prefix="press78-analog-") as temp:
        for sr in [8000, 44100, 44117, 48000, 96000, 192000]:
            path = Path(temp) / f"impulse-{sr}.f64"
            subprocess.run([str(args.probe.resolve()), str(sr), str(sr), str(path)], check=True)
            actual = np.fromfile(path, dtype=np.float64)
            impulse = np.zeros(sr)
            impulse[0] = 1
            expected = circuit.process(impulse, sr, output)
            error = actual - expected
            max_error = float(np.max(np.abs(error)))
            relative = float(np.linalg.norm(error) / np.linalg.norm(expected))
            rows.append({"sample_rate": sr, "frames": len(actual), "max_absolute_error": max_error,
                         "relative_rms_error": relative,
                         "passed": bool(np.all(np.isfinite(actual)) and max_error < 1e-7 and relative < 1e-6)})
    paths = [root / "Source/DSP/AnalogOutput.h", root / "Tools/AnalogProbe.cpp",
             Path(__file__), root / "Tools/reference/circuit/model.py"]
    report = {"scope": "C++ circuit runtime vs frozen PSS480 MNA; not original PSS780 hardware verification",
              "passed": all(r["passed"] for r in rows), "rows": rows,
              "probe_sha256": hashlib.sha256(args.probe.read_bytes()).hexdigest(),
              "source_sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
