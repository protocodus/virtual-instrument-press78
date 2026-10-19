#!/usr/bin/env python3
"""Fixed protocol: see design-frozen.json. No searches or physical fit.

Read retained local PSS-680 carrier-only captures; analyze existing windows
and equal thirds independently per channel. Native controls come from actual
shipping C++ compiled by Probe.cpp. Copyrighted media is never copied.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import numpy as np
from scipy.io import wavfile


def binding(path):
    b = Path(path).read_bytes()
    return dict(path=str(Path(path).resolve()), bytes=len(b), sha256=hashlib.sha256(b).hexdigest())


def fit(y, sr, hz):
    t = np.arange(len(y)) / sr
    h = np.arange(1, 13)
    m = np.column_stack((np.ones(len(y)), np.sin(2*np.pi*t[:, None]*hz*h), np.cos(2*np.pi*t[:, None]*hz*h)))
    w = np.hanning(len(y))
    c = np.linalg.lstsq(m*w[:, None], y*w, rcond=None)[0]
    z = c[1:13] + 1j*c[13:25]
    a = np.abs(z)
    return dict(amplitudes=a.tolist(), complex_sin_coefficients=[[float(v.real), float(v.imag)] for v in z],
                harmonic_db_relative_fundamental=(20*np.log10(np.maximum(a/a[0], 1e-15))).tolist(),
                dc=float(c[0]), rms=float(np.sqrt(np.mean(y*y))),
                residual_relative_rms=float(np.sqrt(np.mean((y-m@c)**2)/np.mean(y*y))))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    design = json.loads((here/'design-frozen.json').read_text())
    for b in design['inputs'].values():
        assert binding(b['path']) == b, b['path']
    sr, source = wavfile.read(design['inputs']['capture']['path'])
    assert sr == 48000 and source.ndim == 2 and source.shape[1] == 2
    source = source.astype(float)
    rows = []
    for window in design['windows']:
        slices = [('full', window['start'], window['end'])]
        edges = np.linspace(window['start'], window['end'], 4)
        slices += [(f'third-{j+1}', float(edges[j]), float(edges[j+1])) for j in range(3)]
        for label, start, end in slices:
            y = source[round(start*sr):round(end*sr)]
            channels = dict(left=y[:, 0], right=y[:, 1], mid=y.mean(axis=1), side=(y[:, 0]-y[:, 1])/2)
            rows.append(dict(table=window['table'], part=label, start=start, end=end, f0_hz=window['f0_hz'],
                             channels={k: fit(v, sr, window['f0_hz']) for k, v in channels.items() if np.any(v)}))
    harmonics = []
    for n in range(1, 13):
        b = -8 / (math.pi*n*(n*n-4)) if n % 2 else 0
        harmonics.append(dict(harmonic=n, sine_coefficient=b, relative_fundamental=b/(8/(3*math.pi)),
                              db_relative_fundamental=20*math.log10(abs(b/(8/(3*math.pi)))) if b else None))
    native = {}
    for name in ('dry', 'circuit'):
        path = args.output.parent/(name+'.f32')
        y = np.fromfile(path, dtype='<f4').astype(float)
        assert len(y) == 48000
        native[name] = dict(binding=binding(path), analysis=fit(y[31200:], sr, design['windows'][1]['f0_hz']))
    result = dict(date='2026-10-19', design=binding(here/'design-frozen.json'), tool=binding(__file__),
                  unchanged_engine=design['inputs']['engine'], mathematics=harmonics, capture_rows=rows,
                  native_controls=native, native_probe=json.loads((args.output.parent/'native-probe.json').read_text()),
                  classification='Descriptive new harmonic/stereo observability audit only; no hardware-ROM/bit-depth/capture-transfer fit or production change.')
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    for row in rows:
        if row['table'] in (1, 3):
            print(row['table'], row['part'], {k: [round(v['harmonic_db_relative_fundamental'][j], 5) for j in (2, 4)] for k, v in row['channels'].items()})
    print('native', {k: [v['analysis']['harmonic_db_relative_fundamental'][j] for j in (2, 4)] for k,v in native.items()})


if __name__ == '__main__':
    main()
