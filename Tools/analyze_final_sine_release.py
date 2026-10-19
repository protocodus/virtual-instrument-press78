#!/usr/bin/env python3
"""Measure the already observed PSS-780 tour's final Sine Wave chord.

Uses fixed equal-tempered frequencies and gate-relative windows, without a
pitch, onset or model-parameter fit. Original audio must remain local/ignored.
The optional broken-line regression is explicitly descriptive calibration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from scipy import signal, stats
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[1]
WIDTHS = (0.012, 0.020, 0.030)
PRE = (-0.10, -0.03)
WINDOWS = ((0.05, 0.12), (0.12, 0.20), (0.20, 0.35), (0.35, 0.50))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def lock_in(audio, fs, frequency, width):
    window = signal.windows.hann(round(width * fs) + 1)
    window /= window.sum()
    oscillator = np.exp(-2j * np.pi * frequency * np.arange(len(audio)) / fs)
    return 2 * signal.fftconvolve(audio * oscillator[:, None], window[:, None],
                                  mode='same', axes=0)


def line_fit(t, db, lo, hi):
    mask = (t >= lo) & (t < hi)
    result = stats.linregress(t[mask], db[mask])
    return dict(seconds=[lo, hi], slope_db_per_second=float(result.slope),
                r_squared=float(result.rvalue ** 2),
                median_relative_db=float(np.median(db[mask])))


def descriptive_break(t, db):
    # No engine parameter is selected here. This searches only the measured
    # curve's bend, with a continuous two-line regression and fixed bounds.
    mask = (t >= .05) & (t < .40)
    x, y = t[mask], db[mask]
    best = None
    for change in np.arange(.09, .18001, .0005):
        basis = np.column_stack((np.ones(len(x)), x, np.maximum(x - change, 0)))
        beta = np.linalg.lstsq(basis, y, rcond=None)[0]
        error = float(np.mean((basis @ beta - y) ** 2))
        if best is None or error < best['mse_db2']:
            best = dict(break_seconds_after_inferred_off=float(change),
                        break_db_relative_pre=float(beta[0] + beta[1] * change),
                        first_slope_db_per_second=float(beta[1]),
                        second_slope_db_per_second=float(beta[1] + beta[2]),
                        mse_db2=error)
    return best


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-root', type=Path, required=True)
    parser.add_argument('--artifact-dir', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    ref, out = args.reference_root.resolve(), args.artifact_dir.resolve()
    if (out / 'report.json').exists():
        parser.error('Completed measurements are immutable; use a new directory')
    if out.is_relative_to(ROOT) and subprocess.run(
            ['git', 'check-ignore', '--quiet', str(out)], cwd=ROOT).returncode:
        parser.error('Audio-derived artifacts inside the repo must be ignored')
    out.mkdir(parents=True, exist_ok=True)
    source = ref / 'references/v2/user-ONfIvtDOog0.wav'
    align_path = ref / 'references/v2/alignment.json'
    events_path = ref / 'references/v2/eugenia-events.json'
    timeline_path = ref / 'references/v3_program_timeline.json'
    bank_path = ROOT / 'Assets/FactoryBank/press78-factory.json'
    fs, original = wavfile.read(source, mmap=True)
    assert fs == 48000 and original.dtype == np.int16 and original.shape[1] == 2
    alignment = read(align_path)
    timeline = read(timeline_path)['intervals']
    patch = next(v for v in read(bank_path)['voices'] if v['number'] == 99)
    raw = patch['raw_data']
    assert raw[3] == 127 and raw[14] == 8 and raw[8] == 63 and raw[24] == 0
    notes = []
    for event in read(events_path)['notes']:
        onset = alignment['offset_seconds'] + alignment['scale'] * event['start']
        gate = alignment['scale'] * event['gate']
        begin, end = round(onset * fs), round(onset * fs) + round(gate * fs)
        if event['velocity'] > 0 and onset >= timeline[99]['audio_start_seconds']:
            notes.append(dict(midi=event['midi'], velocity=event['velocity'],
                              channel=event['channel'], on_frame=begin, off_frame=end))
    last_on = max(n['on_frame'] for n in notes)
    chord = [n for n in notes if n['on_frame'] == last_on]
    assert sorted(n['midi'] for n in chord) == [39, 75, 79, 87]
    assert len(set(n['off_frame'] for n in chord)) == 1
    off_frame = chord[0]['off_frame']
    assert max(n['off_frame'] for n in notes) == off_frame
    first, last = last_on - round(.25 * fs), off_frame + round(1.0 * fs)
    protocol = dict(scope='Descriptive reuse/calibration; not a fresh holdout.',
        source_url='https://www.youtube.com/watch?v=ONfIvtDOog0',
        sample_rate=fs, chord=chord, source_frames=[first, last],
        reference_level_seconds_after_inferred_off=PRE,
        fit_windows_seconds_after_inferred_off=WINDOWS, hann_widths_seconds=WIDTHS,
        measurement='Fixed equal-tempered lock-in; RMS of channel magnitudes; one sample per millisecond.',
        descriptive_break='Two continuous lines over [.05,.40]s; bend searched [.09,.18]s in .5ms steps. No engine fit.',
        raw_patch=raw, primary_midi=79, corroborating_midi=75,
        diagnostic_only={'87': 'Octave of MIDI75; its second harmonic can contaminate.',
                         '39': 'Short windows contain few bass cycles and pick up nearby notes.'},
        source_sha256={str(p): sha(p) for p in
            (source, align_path, events_path, timeline_path, bank_path, Path(__file__))})
    save(out / 'protocol.json', protocol)
    audio = original[first:last].astype(float) / 32768
    t = (np.arange(len(audio)) + first - off_frame) / fs
    stride = fs // 1000
    traces, rows = {}, []
    for note in (79, 75, 87, 39):
        hz = 440 * 2 ** ((note - 69) / 12)
        for width in WIDTHS:
            z = lock_in(audio, fs, hz, width)
            amplitudes = dict(pair=np.sqrt(np.mean(abs(z) ** 2, axis=1)),
                              left=abs(z[:, 0]), right=abs(z[:, 1]), mid=abs(z.mean(axis=1)))
            for channel, amp in amplitudes.items():
                before = float(np.median(amp[(t >= PRE[0]) & (t < PRE[1])]))
                db = 20 * np.log10(np.maximum(amp / before, 1e-12))
                sampled_t, sampled_db = t[::stride], db[::stride]
                rows.append(dict(midi=note, frequency_hz=hz, hann_width_seconds=width,
                    channel=channel, pre_amplitude=before,
                    fits=[line_fit(sampled_t, sampled_db, *w) for w in WINDOWS],
                    descriptive_break=descriptive_break(sampled_t, sampled_db)))
                if width == .020 and channel == 'pair':
                    traces[f'midi{note}'] = db[::stride]
    np.savez(out / 'traces.npz', seconds_after_off=t[::stride], **traces)
    report = dict(protocol=protocol, rows=rows,
        candidate_predictions=dict(existing_rr8_db_per_second=96 / (48 * 2 ** (-34 / 4)),
            threefold_rr8_db_per_second=96 / (144 * 2 ** (-34 / 4)),
            threefold_rr4_db_per_second=96 / (144 * 2 ** (-18 / 4)),
            status='Hypotheses compared after observing this recording; not recovered OPU constants.'),
        limitations=['MIDI timing is global affine alignment, not measured key-off; local error can be about50ms.',
            'Reverb and Chorus are visibly on in the existing video audit; dry state is unavailable.',
            'Capture compression, AGC, gating and external processing remain undocumented.',
            'A slow tail/bend does not alone identify an internal threshold, rate cap, or trigger operator.',
            'Other chord notes/previous releasing notes and analog nonlinearity can contaminate partials.',
            'Regression R² describes the recorded curve, not confidence in a hardware mechanism.',
            'Hann smoothing has half-width support; channel, window-width and octave checks are reported.'])
    save(out / 'report.json', report)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        save(args.report, report)
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), constrained_layout=True)
    for axis, note in zip(axes, (79, 75)):
        for channel in ('pair', 'left', 'right', 'mid'):
            row = next(r for r in rows if r['midi'] == note and r['hann_width_seconds'] == .020 and r['channel'] == channel)
            # Recalculate the plotted curve from the same observed signal.
            z = lock_in(audio, fs, row['frequency_hz'], .020)
            amp = (np.sqrt(np.mean(abs(z) ** 2, axis=1)) if channel == 'pair' else
                   abs(z[:, 0]) if channel == 'left' else abs(z[:, 1]) if channel == 'right' else abs(z.mean(axis=1)))
            axis.plot(t[::stride], 20 * np.log10(np.maximum(amp[::stride] / row['pre_amplitude'], 1e-12)), label=channel)
        axis.axhline(-18, color='gray', linestyle='--', linewidth=.8)
        for lo, hi in WINDOWS:
            axis.axvspan(lo, hi, alpha=.04, color='black')
        axis.set(xlim=(-.10, .6), ylim=(-40, 4), title=f'Final Sine Wave chord: MIDI {note}',
                 xlabel='Seconds after inferred note-off', ylabel='Partial level relative to own pre-off (dB)')
        axis.grid(alpha=.15)
        axis.legend(ncol=4)
    fig.savefig(out / 'final-sine-release.png', dpi=160)
    plt.close(fig)
    print(json.dumps(dict(artifact_dir=str(out), chord=chord,
        primary=[r for r in rows if r['midi'] == 79 and r['hann_width_seconds'] == .020 and r['channel'] == 'pair']), indent=2))


if __name__ == '__main__':
    main()
