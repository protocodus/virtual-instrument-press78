#!/usr/bin/env python3
"""Post-observation diagnostic requested by independent review.

No capture re-fit: derive normalized odd-harmonic transfer which would be
required if the ideal SIN²/HALF² shapes and a downstream LTI path were true.
Frequency differences, effects, dynamics, gates and capture remain unknown;
these are conditional transfer requirements, not fitted hardware coefficients.
"""
import argparse
import json
import math
from pathlib import Path


def summarize(row):
    channel = row['channels']['mid']
    z = [complex(*c) for c in channel['complex_sin_coefficients']]
    phase1 = math.atan2(z[0].imag, z[0].real)
    h = []
    for n in (3, 5, 7, 9, 11):
        ideal = 3 / (n*(n*n-4))
        phase_n = math.atan2(z[n-1].imag, z[n-1].real)
        h.append(dict(harmonic=n, ideal_db_relative_fundamental=20*math.log10(ideal),
                      required_transfer_db_relative_fundamental=channel['harmonic_db_relative_fundamental'][n-1] - 20*math.log10(ideal),
                      required_transfer_phase_invariant_rad=math.remainder(phase_n-n*phase1-math.pi, 2*math.pi)))
    return dict(table=row['table'], part=row['part'], f0_hz=row['f0_hz'], harmonics=h)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('result', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    data = json.loads(args.result.read_text())
    rows = [summarize(r) for r in data['capture_rows'] if r['table'] in (1, 3)]
    differences = []
    for part in ('full', 'third-1', 'third-2', 'third-3'):
        a = next(r for r in rows if r['table']==1 and r['part']==part)
        b = next(r for r in rows if r['table']==3 and r['part']==part)
        differences.append(dict(part=part, half_square_minus_full_square=[dict(
            harmonic=x['harmonic'], required_transfer_db_difference=y['required_transfer_db_relative_fundamental']-x['required_transfer_db_relative_fundamental'],
            required_transfer_phase_invariant_difference_rad=math.remainder(y['required_transfer_phase_invariant_rad']-x['required_transfer_phase_invariant_rad'], 2*math.pi))
            for x,y in zip(a['harmonics'],b['harmonics'])]))
    out=dict(status='post-observation conditional-LTI diagnostic; no re-fit, no thresholds or adoption', rows=rows, comparisons=differences,
             interpretation='A common capture/effect response could attenuate fifth partials in both tables. Differences across recorded passages prevent treating any inferred response as calibrated. Phase-invariant differences remove arbitrary note starting phase, but not time-varying capture effects.')
    args.output.write_text(json.dumps(out,indent=2)+'\n')


if __name__=='__main__':
    main()
