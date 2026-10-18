"""Independent numerical parity against the frozen effective Python transfer."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Reference/Python'))
from circuit.calibrated_chorus import process_calibrated_chorus


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--probe', type=Path, default=ROOT/'build/press78_chorus_probe')
    parser.add_argument('--report', type=Path, default=ROOT/'Tests/results/recorded-chorus-parity.json')
    args = parser.parse_args()
    rows = []
    with tempfile.TemporaryDirectory(prefix='press78-chorus-') as temporary:
        tmp = Path(temporary)
        for rate, start in ((8000, 0), (44100, 17.123), (44117, -.25), (48000, 0),
                            (48000, 173.1234), (96000, 3.14159), (192000, 173.125)):
            n = int(rate * 1.1)
            rng = np.random.default_rng(780)
            t = np.arange(n)/rate
            x = (.17*np.sin(2*np.pi*997*t) + .1*np.sin(2*np.pi*3001*t)
                 + .03*rng.standard_normal(n))
            x[:97] = 0
            x[0] = .5  # Deliberate nonzero start tests zero-prehistory convention.
            x.astype('<f8').tofile(tmp/'in.f64')
            subprocess.run([str(args.probe.resolve()), str(rate), str(start), str(tmp/'in.f64'),
                            str(tmp/'out.f64')], check=True, capture_output=True)
            native = np.fromfile(tmp/'out.f64', dtype='<f8').reshape(-1,2)
            reference = process_calibrated_chorus(x, rate, start_seconds=start)
            delta = native-reference
            peak = float(np.max(abs(delta)))
            relative = float(np.sqrt(np.mean(delta*delta)/np.mean(reference*reference)))
            midpoint = float(np.max(abs(native.mean(axis=1)-x)))
            assert peak < 1e-7 and midpoint < 2e-16, (rate,start,peak,midpoint)
            rows.append({'sample_rate':rate,'start_seconds':start,'frames':n,
                         'maximum_absolute_error':peak,'relative_rms_error':relative,
                         'maximum_midpoint_error':midpoint})
    paths = [ROOT/'Source/DSP/RecordedChorus.h', ROOT/'Source/DSP/RecordedChorusProfile.h',
             ROOT/'Tools/ChorusProbe.cpp', Path(__file__),
             ROOT/'Reference/Python/circuit/calibrated_chorus.py',
             ROOT/'Reference/Python/circuit/video_chorus_profile.json']
    report = {'passed':True,'scope':'Numerical streaming parity with frozen v3 effective transfer, not physical BBD identification; no normalization.',
              'additional_algorithmic_latency_samples':0,'rows':rows,
              'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(f'{len(rows)} chorus parity fixtures passed; max error {max(r["maximum_absolute_error"] for r in rows):.4g}')


if __name__ == '__main__':
    main()
