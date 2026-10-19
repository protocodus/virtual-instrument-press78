#!/usr/bin/env python3
"""Research receipt crosschecks; no new audio rendering or parameter fits."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import numpy as np
from scipy.io import wavfile


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('result',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    result=json.loads(args.result.read_text())
    design=json.loads(Path(result['design']['path']).read_text())
    checks=0
    def check(condition):
        nonlocal checks
        assert condition
        checks+=1
    for b in [result['design'],result['tool'],*design['inputs'].values()]:
        payload=Path(b['path']).read_bytes()
        check(len(payload)==b['bytes'])
        check(hashlib.sha256(payload).hexdigest()==b['sha256'])
    sr,source=wavfile.read(design['inputs']['capture']['path'])
    check(sr==48000)
    for window in design['windows']:
        y=source[round(window['start']*sr):round(window['end']*sr)]
        check(np.array_equal(y[:,0],y[:,1]))
    old=json.loads(Path(design['inputs']['old_analysis']['path']).read_text())
    for window in old['waveform_analysis']['windows']:
        row=next(r for r in result['capture_rows'] if r['table']==window['table'] and r['part']=='full')
        for a,b in zip(row['channels']['mid']['harmonic_db_relative_fundamental'],window['harmonic_db_relative_fundamental']):
            check(abs(a-b)<1e-10)
        for channel in row['channels'].values():
            check(channel==row['channels']['mid'])
    # Independent direct integration of the mathematical shape, not calling
    # the coefficient formula used by analyze.py.
    t=2*np.pi*np.arange(65536)/65536
    y=np.sin(t)*np.abs(np.sin(t))
    check(abs(np.mean(y))<1e-14)
    for h in result['mathematics']:
        n=h['harmonic']
        check(abs(2*np.mean(y*np.sin(n*t))-h['sine_coefficient'])<1e-11)
        check(abs(2*np.mean(y*np.cos(n*t)))<1e-14)
    native=result['native_probe']
    check(native['identity_max_error']==0)
    check(native['pm_identity_max_error']==0)
    check(abs(native['coherent_mean'])<1e-14)
    for lane in result['native_controls'].values():
        b=lane['binding'];payload=Path(b['path']).read_bytes()
        check(len(payload)==b['bytes'])
        check(hashlib.sha256(payload).hexdigest()==b['sha256'])
        check(np.isfinite(np.frombuffer(payload,dtype='<f4')).all())
    dry=result['native_controls']['dry']['analysis']['harmonic_db_relative_fundamental']
    check(abs(dry[2]-20*math.log10(1/5))<1e-6)
    check(abs(dry[4]-20*math.log10(1/35))<1e-6)
    args.output.write_text(json.dumps(dict(passed=True,checks=checks,
        scope='Input hashes, four analyzed-window exact L/R identities, 48 retained full-window harmonic results, analytic Fourier coefficients by independent numerical integration, native wave/PM algebra, finite native control bindings. Not hardware bit accuracy.'),indent=2)+'\n')
    print(json.dumps(dict(passed=True,checks=checks)))


if __name__=='__main__':
    main()
