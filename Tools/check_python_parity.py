#!/usr/bin/env python3
"""Compare the native behavioral core with the frozen research implementation.

The externally supplied research directory is not bundled or licensed by this
test. It provides the original experiment and the separately sourced bank.
Nominal48k raw FM only: host resampler delay is removed, output effects bypassed.
This is implementation parity, not validation against a Yamaha instrument.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from scipy.io import wavfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--renderer", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--all-presets", action="store_true", help="also exercise the other96 presets with shorter held/release notes")
    args = parser.parse_args()
    source = args.reference_root / "src" / "pss780.py"
    sys.path.insert(0, str(source.parent))
    import pss780

    fixtures = [(65, 60, 100), (93, 60, 100), (97, 60, 100), (99, 69, 127)]
    if args.all_presets:
        fixtures += [(n, 60, 100) for n in range(100) if n not in (65, 93, 97, 99)]
    rows = []
    with tempfile.TemporaryDirectory(prefix="press78-parity-") as temp:
        for number, note, velocity in fixtures:
            patch = pss780.get_patch(number)
            seconds = 3.0 if number in (65, 93, 97, 99) else 0.6
            gate, sr, latency = seconds / 2, 48000, 32
            output = Path(temp) / f"preset-{number:02d}.wav"
            raw = bytes(patch["raw_data"]).hex()
            command = [str(args.renderer.resolve()), "--output", str(output), "--raw", raw,
                       "--transparent", "--rate", str(sr), "--note", str(note),
                       "--velocity", str(velocity), "--gate", str(gate),
                       "--seconds", str(seconds + latency / sr)]
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            rate, stereo = wavfile.read(output)
            assert rate == sr and stereo.shape[1] == 2
            actual = stereo[latency:, 0].astype(np.float64)
            expected = pss780.render_note(patch, note, velocity, seconds, gate, sr)
            error = actual - expected
            max_error = float(np.max(np.abs(error)))
            relative = float(np.linalg.norm(error) / max(np.linalg.norm(expected), 1e-20))
            rows.append({"preset": number, "name": patch["name"], "note": note, "velocity": velocity,
                         "max_absolute_error": max_error, "relative_rms_error": relative,
                         "stereo_equal": bool(np.array_equal(stereo[:, 0], stereo[:, 1])),
                         "passed": max_error < 2e-5 and relative < 2e-5,
                         "renderer": json.loads(result.stdout)})
    root = Path(__file__).resolve().parents[1]
    report = {"scope": "nominal48k raw behavioral-model parity; no hardware equivalence assertion",
              "latency_removed_internal_samples": 32, "passed": all(r["passed"] for r in rows),
              "reference_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "bank_sha256": hashlib.sha256((source.parent / "factory_voices.json").read_bytes()).hexdigest(),
              "renderer_sha256": hashlib.sha256(args.renderer.read_bytes()).hexdigest(),
              "parity_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "native_source_sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                                        for p in sorted((root / "Source" / "DSP").glob("Press78Engine.*"))},
              "fixtures": rows}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
