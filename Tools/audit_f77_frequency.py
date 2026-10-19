#!/usr/bin/env python3
"""Reproduce the frozen, inconclusive F77 frequency diagnostic without fitting.

Requires NumPy/SciPy and the protocol-bound local PCM16, Opus, AAC and finite-tail
research-render files. Media is not bundled, downloaded or rendered by this tool.
The original absolute input paths and SHA-256 bindings must be available locally.
Only the exact frozen protocol is accepted; no window, tuning or gate is changed.

Example, from the repository root:
  python3 Tools/audit_f77_frequency.py \
    --protocol build/f77-frequency-prediction-20261019/protocol-frozen.json \
    --out build/f77-frequency-reproduction-new

Output must be a NEW directory below this checkout's ignored build*/ tree.
Existing directories are refused, even when empty. The tool writes only a copy
of the frozen protocol and result JSON; no full WAV or production file is written.
The original result is inconclusive because all eight finite-tail control gates
fail, although analytic controls, capture codec agreement and quiet gates pass.
Reproducing those failures is success; it is not a new experiment or a fitted fix.
"""
from pathlib import Path
import argparse
import hashlib, json, math, time
import numpy as np
from scipy import signal, optimize
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[1]
FROZEN_PROTOCOL_SHA256 = '37587fdf8cc946d649e6060a4da6e491c8f9b39e616f08b1836c78bce45d4f46'
parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('--protocol', type=Path, required=True, help='Exact frozen F77 protocol JSON; bound local media must exist')
parser.add_argument('--out', type=Path, required=True, help='New output below ignored build*/; existing directories are never replaced')
args = parser.parse_args()
OUT = args.out.resolve()
if not OUT.is_relative_to(ROOT):
    parser.error('--out must be below this checkout, under its ignored build*/ tree')
relative = OUT.relative_to(ROOT)
if len(relative.parts) < 2 or not relative.parts[0].startswith('build'):
    parser.error('--out must be a new subdirectory under ignored build*/')
if '/build*/' not in (ROOT / '.gitignore').read_text().splitlines():
    parser.error('Expected /build*/ ignore rule is missing; refusing research output')
if OUT.exists():
    parser.error('Refusing an existing output directory; choose a new --out')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol_bytes = args.protocol.read_bytes()
if hashlib.sha256(protocol_bytes).hexdigest() != FROZEN_PROTOCOL_SHA256:
    parser.error('--protocol is not the exact frozen F77 protocol')
pr = json.loads(protocol_bytes)
assert not (OUT / 'result.json').exists()
for row in pr['sources'].values():
    assert sha(row['path']) == row['sha256']
for path, digest in pr['metadata_bindings'].items():
    assert sha(path) == digest
OUT.mkdir(parents=True, exist_ok=False)
(OUT / 'protocol-frozen.json').write_bytes(protocol_bytes)
fs = pr['sample_rate']
nominal = pr['candidate']['nominal_hz']
began = time.perf_counter()

def filtered(x, origin, cutoff, start, end):
    a = math.floor((start - .5 - origin) * fs)
    b = math.ceil((end + .5 - origin) * fs)
    if a < 0 or b > len(x):
        raise ValueError('Insufficient fixed context')
    tt = origin + np.arange(a, b) / fs
    zz = signal.sosfiltfilt(signal.butter(4, cutoff, fs=fs, output='sos'),
                           2 * x[a:b] * np.exp(-2j * np.pi * nominal * tt))
    return tt, zz

def endpoint(x, origin, cutoff, window, captured):
    start, end = window['start_seconds'], window['end_seconds']
    tt, z = filtered(x, origin, cutoff, start, end)
    phase = np.unwrap(np.angle(z))
    a, b = np.interp([start, end], tt, phase)
    frequency = nominal + (b - a) / (2 * np.pi * window['duration_seconds'])
    amp = abs(z)
    inside = (tt >= start) & (tt <= end)
    minimum, median = float(min(amp[inside])), float(np.median(amp[inside]))
    quality = {'minimum_amplitude': minimum, 'median_amplitude': median,
               'minimum_amplitude_dbfs': float(20 * np.log10(max(minimum, 1e-30))),
               'median_amplitude_dbfs': float(20 * np.log10(max(median, 1e-30))),
               'endpoint_amplitudes': [float(v) for v in np.interp([start, end], tt, amp)],
               'fraction_below_point2_median': float(np.mean(amp[inside] < .2 * median))}
    if captured:
        fa, fb = pr['quiet_floor_seconds']
        ft, fz = filtered(x, origin, cutoff, fa, fb)
        floor = float(np.median(abs(fz[(ft >= fa) & (ft <= fb)])))
        quality.update(empirical_floor_median_amplitude=floor,
                       minimum_above_floor_db=float(20 * np.log10(max(minimum, 1e-30) / max(floor, 1e-30))),
                       quiet_gate=bool(minimum >= .2 * median and minimum >= 10 * floor and minimum > 0))
    else:
        quality['quiet_gate'] = None
    return {'hz': float(frequency), 'valid': bool(np.isfinite(frequency) and frequency > 0),
            'phase_start_radians': float(a), 'phase_end_radians': float(b), 'quality': quality}

def spectral(x, origin, taper, window):
    aa = round((window['start_seconds'] - origin) * fs)
    bb = round((window['end_seconds'] - origin) * fs)
    v = x[aa:bb].astype(float)
    if len(v) < 32 or max(abs(v)) == 0:
        raise ValueError('Too short or silent')
    v /= max(abs(v))
    taper_fn = signal.windows.hann if taper == 'hann' else signal.windows.blackman
    w = taper_fn(len(v), sym=False)
    nfft = 2 ** math.ceil(math.log2(16 * len(v)))
    ff = np.fft.rfftfreq(nfft, 1 / fs)
    power = abs(np.fft.rfft(v * w, n=nfft)) ** 2
    low, high = nominal * 2 ** (-75 / 1200), nominal * 2 ** (75 / 1200)
    ids = np.flatnonzero((ff >= low) & (ff <= high))
    k = int(ids[np.argmax(power[ids])])
    step = fs / nfft
    yy = v * w
    yy /= np.linalg.norm(yy)
    tt = np.arange(len(v)) / fs
    fit = optimize.minimize_scalar(
        lambda frequency: -abs(np.dot(yy, np.exp(-2j * np.pi * frequency * tt))) ** 2,
        bounds=(max(low, ff[k] - 2 * step), min(high, ff[k] + 2 * step)),
        method='bounded', options={'xatol': 1e-9})
    return {'hz': float(fit.x), 'valid': bool(fit.success and k != ids[0] and k != ids[-1]),
            'boundary_peak': bool(k == ids[0] or k == ids[-1]),
            'sample_window_seconds': len(v) / fs}

def measure(source, channel, x, origin, window, captured, truth=None):
    estimates = {}
    for cutoff in [6, 12]:
        try:
            estimates[f'phase{cutoff}'] = endpoint(x, origin, cutoff, window, captured)
        except ValueError as error:
            estimates[f'phase{cutoff}'] = {'valid': False, 'reason': str(error)}
    for taper in ['hann', 'blackman']:
        try:
            estimates[taper] = spectral(x, origin, taper, window)
            if captured:
                estimates[taper]['quality'] = estimates.get('phase12', {}).get('quality', {'quiet_gate': False})
        except ValueError as error:
            estimates[taper] = {'valid': False, 'reason': str(error)}
    for result in estimates.values():
        if 'hz' not in result or result['hz'] <= 0:
            continue
        result['cents_from_nominal'] = float(1200 * np.log2(result['hz'] / nominal))
        if truth is not None:
            result['known_frequency_error_cents'] = float(1200 * np.log2(result['hz'] / truth))
        else:
            residuals = {}
            for model in ['equal_tempered', 'candidate']:
                base = nominal if model == 'equal_tempered' else pr['candidate']['candidate_hz_before_nuisance']
                predicted = base * 2 ** (pr['fixed_G_anchor_nuisances'][model]['cents'] / 1200)
                residuals[model] = {'fixed_prediction_hz': predicted,
                                    'residual_cents': float(1200 * np.log2(result['hz'] / predicted))}
            result['fixed_model_residuals'] = residuals
    return {'source': source, 'channel': channel, 'event_index': window['event']['event_index'],
            'window_seconds': [window['start_seconds'], window['end_seconds']], 'estimates': estimates}

rows, control_names = [], []
for window in pr['windows']:
    ca = math.floor((window['start_seconds'] - .5) * fs)
    cb = math.ceil((window['end_seconds'] + .5) * fs)
    tt, origin = np.arange(ca, cb) / fs, ca / fs
    for shape in ['stationary', 'exponential']:
        for common in [0., -2.]:
            for phase_rule in ['all_zero', 'golden']:
                source = f'{shape}_{common:g}c_{phase_rule}'
                if source not in control_names:
                    control_names.append(source)
                x = np.zeros(len(tt))
                for midi in pr['analytic_controls']['all_control_midi']:
                    frequency = 440 * 2 ** ((midi - 69) / 12) * 2 ** (common / 1200)
                    phase = 0. if phase_rule == 'all_zero' else 2 * np.pi * ((midi * .6180339887498949) % 1)
                    amplitude = .02
                    if shape == 'exponential':
                        amplitude *= 10 ** (-14 * (tt - window['event']['off_seconds']) / 20)
                    x += amplitude * np.sin(2 * np.pi * frequency * (tt - window['event']['off_seconds']) + phase)
                rows.append(measure(source, 'mono', x, origin, window, False, nominal * 2 ** (common / 1200)))
    print('Analytic controls', window['event']['event_index'], 'elapsed', round(time.perf_counter() - began, 2), flush=True)

for source in ['research_rr3_carrier', 'pcm16', 'opus_float', 'aac_float']:
    sr, data = wavfile.read(pr['sources'][source]['path'], mmap=True)
    assert sr == fs and data.ndim == 2
    trim = pr['source_trims_frames'][source]
    ca = math.floor((min(w['start_seconds'] for w in pr['windows']) - .6) * fs)
    cb = math.ceil((max(pr['quiet_floor_seconds'][1], max(w['end_seconds'] for w in pr['windows'])) + .6) * fs)
    if cb + trim > len(data):
        raise ValueError('Source lacks fixed target/floor context: ' + source)
    subset = data[ca + trim:cb + trim].astype(float)
    if data.dtype == np.int16:
        subset /= 32768
    origin = ca / fs
    for channel, x in {'mid': subset.mean(axis=1), 'left': subset[:, 0], 'right': subset[:, 1]}.items():
        for window in pr['windows']:
            rows.append(measure(source, channel, x, origin, window, source != 'research_rr3_carrier',
                                nominal if source == 'research_rr3_carrier' else None))
    print('Measured', source, 'elapsed', round(time.perf_counter() - began, 2), flush=True)

index = {(r['source'], r['channel'], r['event_index']): r for r in rows}
checks = []
for window in pr['windows']:
    event = window['event']['event_index']
    for estimator in ['phase6', 'phase12', 'hann', 'blackman']:
        controls = [{'source': name, **index[name, 'mono', event]['estimates'][estimator]} for name in control_names]
        controls.append({'source': 'research_rr3_carrier', **index['research_rr3_carrier', 'mid', event]['estimates'][estimator]})
        control_ok = all(c['valid'] and abs(c.get('known_frequency_error_cents', math.inf)) <= .05 for c in controls)
        opus, aac = [index[source, 'mid', event]['estimates'][estimator] for source in ['opus_float', 'aac_float']]
        difference = aac['cents_from_nominal'] - opus['cents_from_nominal'] if all('cents_from_nominal' in c for c in [opus, aac]) else None
        quiet = all(c['valid'] and c.get('quality', {}).get('quiet_gate', False) for c in [opus, aac])
        codec_ok = difference is not None and abs(difference) <= .05
        checks.append({'event_index': event, 'estimator': estimator, 'control_rows': controls,
                       'control_eligible': control_ok, 'captured_quiet_valid_gate': quiet,
                       'aac_minus_opus_cents': difference, 'codec_agreement': codec_ok,
                       'qualified': bool(control_ok and quiet and codec_ok)})

summary = []
for window in pr['windows']:
    event = window['event']['event_index']
    methods = [c['estimator'] for c in checks if c['event_index'] == event and c['qualified']]
    family = any(m in methods for m in ['phase6', 'phase12']) and any(m in methods for m in ['hann', 'blackman'])
    residuals = []
    for method in methods:
        for source in ['opus_float', 'aac_float']:
            residuals.append({'source': source, 'estimator': method,
                              **index[source, 'mid', event]['estimates'][method]['fixed_model_residuals']})
    summary.append({'event_index': event, 'qualified_estimators': methods,
                    'phase_and_spectral_families': family, 'evaluable': family,
                    'all_qualified_residuals': residuals,
                    'all_qualified_estimates_closer_to_candidate': all(abs(r['candidate']['residual_cents']) < abs(r['equal_tempered']['residual_cents']) for r in residuals) if residuals else None})

result = {'protocol_sha256': sha(OUT / 'protocol-frozen.json'), 'analysis_script_sha256': sha(__file__),
          'rows': rows, 'control_codec_quiet_checks': checks, 'summary': summary,
          'all_source_hashes_unchanged': all(sha(r['path']) == r['sha256'] for r in pr['sources'].values()),
          'elapsed_seconds': time.perf_counter() - began,
          'scope': 'Reused-source, posthoc selected note-class falsification diagnostic with frozen new tail windows; no target or engine fit. All eligibility failures retained.'}
(OUT / 'result.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
print(json.dumps({'summary': summary, 'checks': [{k: v for k, v in c.items() if k != 'control_rows'} for c in checks]}, indent=2))
