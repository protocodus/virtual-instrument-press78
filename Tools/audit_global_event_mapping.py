#!/usr/bin/env python3
"""Freeze candidate audible-event maps, then measure held-out timing observations.

This research tool never renders DSP, changes an existing alignment, or scores audio
spectra. `freeze` uses a previous timing report and MIDI/patch metadata only;
`measure` refuses to overwrite results and verifies the frozen input hashes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION_PATCHES = (5, 18, 88, 99)
VALIDATION_PATCHES = (19, 52, 91, 98)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write_new(path, data):
    path = Path(path)
    if path.exists():
        raise ValueError(f'Refusing to replace completed artifact: {path}')
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def half_crossing(row, window=24):
    observed = next(x for x in row['observations'] if x['window_ms'] == window)
    result = next(x for x in observed['thresholds'] if x['fraction'] == .5)
    return result['residual_seconds'] if result['valid'] else None


def group_rows(rows, calibration=False):
    groups = []
    for patch in sorted(set(r['note']['patch'] for r in rows)):
        patch_rows = [r for r in rows if r['note']['patch'] == patch]
        for onset in sorted(set(r['note']['audio_on'] for r in patch_rows)):
            members = [r for r in patch_rows if r['note']['audio_on'] == onset]
            valid = [r for r in members if half_crossing(r) is not None]
            if valid:
                groups.append({'patch': patch, 'midi_on': valid[0]['note']['start'],
                    'old_mapped_on': onset,
                    'audible_on': onset + float(np.median([half_crossing(r) for r in valid])),
                    'old_map_residual_seconds': float(np.median([half_crossing(r) for r in valid])),
                    'midi_notes': [r['note']['midi'] for r in valid],
                    'valid_note_count': len(valid), 'invalid_note_count': len(members) - len(valid),
                    'calibration': calibration})
    return groups


def patch_summaries(groups, alignment):
    summaries = []
    for patch in sorted(set(g['patch'] for g in groups)):
        items = [g for g in groups if g['patch'] == patch]
        t = float(np.median([g['midi_on'] for g in items]))
        residual = float(np.median([g['old_map_residual_seconds'] for g in items]))
        observed = alignment['offset_seconds'] + alignment['scale'] * t + residual
        summaries.append({'patch': patch, 'unique_onset_groups': len(items),
            'median_midi_time': t, 'median_old_map_residual_seconds': residual,
            'summary_audible_time': observed})
    return summaries


def candidate_maps(summaries, old):
    x = np.array([s['median_midi_time'] for s in summaries])
    residual = np.array([s['median_old_map_residual_seconds'] for s in summaries])
    y = np.array([s['summary_audible_time'] for s in summaries])
    slopes = [(y[j] - y[i]) / (x[j] - x[i]) for i in range(len(x)) for j in range(i + 1, len(x))]
    robust_scale = float(np.median(slopes))
    return [
        {'id': 'unchanged', 'offset_seconds': old['offset_seconds'], 'scale': old['scale']},
        {'id': 'old_scale_median_offset', 'offset_seconds': old['offset_seconds'] + float(np.median(residual)), 'scale': old['scale']},
        {'id': 'nominal_scale_median_intercept', 'offset_seconds': float(np.median(y - x)), 'scale': 1.0},
        {'id': 'equal_patch_robust_affine', 'offset_seconds': float(np.median(y - robust_scale * x)), 'scale': robust_scale},
    ], [float(s) for s in slopes]


def select_notes(events, timeline, bank, alignment):
    notes = []
    for i, note in enumerate(events):
        begin = alignment['offset_seconds'] + alignment['scale'] * note['start']
        end = alignment['offset_seconds'] + alignment['scale'] * note['end']
        patch = max(t['patch'] for t in timeline if t['audio_start_seconds'] <= begin + 1e-8)
        notes.append({**note, 'id': i, 'audio_on': begin, 'audio_off': end, 'patch': patch})
    selected, selection_rows = [], []
    for patch in VALIDATION_PATCHES:
        raw = bank[patch]['raw_data']
        criteria = {'both_operators_raw_ar63': (raw[7] & 63) == 63 and (raw[8] & 63) == 63,
                    'modulator_tl_at_least40': raw[3] >= 40,
                    'carrier_sine': raw[12] >> 6 == 0,
                    'voice_vibrato_flag_off': (raw[24] & 128) == 0}
        if not all(criteria.values()):
            raise ValueError(f'Unexpected validation-patch metadata: {patch}: {criteria}')
        rejected = []
        for note in [n for n in notes if n['patch'] == patch]:
            reasons = []
            if note['midi'] < 72:
                reasons.append('midi_below72')
            if note['audio_on'] - timeline[patch]['audio_start_seconds'] < .10:
                reasons.append('less_than100ms_after_inferred_program_boundary')
            previous = [q['audio_off'] for q in notes if q['midi'] == note['midi'] and q['audio_on'] < note['audio_on'] - 1e-7]
            gap = note['audio_on'] - max(previous, default=-1e9)
            if gap < .25:
                reasons.append('previous_same_note_midi_off_less_than250ms_ago')
            if reasons:
                rejected.append({'id': note['id'], 'midi': note['midi'], 'audio_on': note['audio_on'], 'reasons': reasons})
                continue
            multiple = raw[2] & 15
            if multiple == 0:
                multiple = .5
            selected.append({**note, 'carrier_multiple': multiple,
                'frequency_nominal_hz': float(440 * 2 ** ((note['midi'] - 69) / 12) * multiple),
                'previous_same_note_gap_seconds': gap})
        selection_rows.append({'patch': patch, 'name': bank[patch]['name'], 'raw_data': raw,
            'metadata_criteria': criteria, 'selected_note_count': sum(n['patch'] == patch for n in selected),
            'metadata_rejections': rejected})
    return selected, selection_rows


def freeze(args):
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    ref = args.reference_root.resolve()
    files = {'calibration_report': args.calibration_report.resolve(), 'bank': args.bank.resolve(),
             'alignment': ref / 'references/v2/alignment.json',
             'events': ref / 'references/v2/eugenia-events.json',
             'timeline': ref / 'references/v3_program_timeline.json',
             'recording': ref / 'references/v2/user-ONfIvtDOog0.wav',
             'analysis_tool': Path(__file__).resolve()}
    calibration = read(files['calibration_report'])
    alignment = read(files['alignment'])
    cal_rows = calibration['result']['onsets']
    assert len(cal_rows) == 18
    assert sorted(set(r['note']['patch'] for r in cal_rows)) == list(CALIBRATION_PATCHES)
    cal_groups = group_rows(cal_rows, calibration=True)
    summaries = patch_summaries(cal_groups, alignment)
    maps, slopes = candidate_maps(summaries, alignment)
    selected, selections = select_notes(read(files['events'])['notes'], read(files['timeline'])['intervals'], read(files['bank'])['voices'], alignment)
    protocol = {'version': 1, 'date_utc': '2026-10-19', 'status': 'frozen before new onset audio measurement',
        'purpose': 'Held-out audible-event timing validation within one already reused hardware recording; not an independent recording or chip-clock identification.',
        'source_files': {k: {'path': str(v), 'sha256': sha(v)} for k, v in files.items()},
        'calibration_patches': list(CALIBRATION_PATCHES), 'validation_patches': list(VALIDATION_PATCHES),
        'old_alignment': alignment, 'calibration_note_count': len(cal_rows),
        'calibration_onset_groups': cal_groups, 'equal_weight_calibration_patch_summaries': summaries,
        'calibration_rule': 'Aggregate simultaneous notes by median residual first; then summarize each calibration patch by median unique-onset MIDI time and median unique-onset residual. Summary audible time=oldOffset+oldScale*medianTime+medianResidual. Four patch summaries have equal weight.',
        'candidate_fit_rules': {'unchanged': 'Original affine map.',
            'old_scale_median_offset': 'Retain old scale; add median of four patch-summary residuals to old offset.',
            'nominal_scale_median_intercept': 'Fix scale1; intercept=median of four(summaryAudibleTime-summaryMidiTime).',
            'equal_patch_robust_affine': 'Scale=median of six pairwise slopes among four patch-summary(time,audibleTime) points; intercept=median of four(audibleTime-scale*time).'},
        'calibration_pairwise_slopes': slopes, 'candidate_maps': maps,
        'metadata_selected_validation_notes': selected, 'validation_selection': selections,
        'selection_rule': 'Fixed patches19/52/91/98; both operators rawAR63, modTL>=40, carrier sine, voiceVibratoOFF. MIDI>=72; at least.10s after inferred program boundary; at least.25s since previous same-pitch source MIDI off. Zero-case patches stay absent; no replacement training/validation cases.',
        'measurement_rule': 'Exactly previous onset audit: arithmetic stereo mid, nominal carrier-frequency centered Hann demodulation12/24/48ms. Median beforeoldOn[-.12,-.07] and afteroldOn[+.07,+.11] define amplitude step; first crossing10/50/90% overoldOn[-.08,+.14], persist >threshold for >90% of next2ms samples. Primary24ms50% needs a crossing, after>before and after>=2*before. All failures retained. Candidate maps never change measurement windows.',
        'evaluation_rule': 'Aggregate valid simultaneous-note primary residuals by median to one audible-onset group. For each map, groupResidual=measuredAudibleOn-(offset+scale*sourceMidiOn). Per-patch error=median(abs(groupResidual)); primary score=mean of per-patch errors with equal weight across usable validation patches. Report signed patch medians, extrema, every group, and12/48ms sensitivity separately.',
        'acceptance_rule': {'minimum_usable_validation_patches': 3, 'minimum_total_valid_onset_groups': 6,
            'minimum_valid_groups_per_usable_patch': 2, 'minimum_primary_score_reduction_fraction_vs_unchanged': .20,
            'maximum_per_patch_median_absolute_error_regression_seconds': .005,
            'minimum_primary_score_margin_seconds_for_unique_map_selection': .003,
            'unique_selection_explanation': 'A unique supported candidate must satisfy coverage, improve primary score>=20% vs unchanged, regress no patch by>5ms, and beat every other improved eligible candidate by>=3ms. Otherwise improved maps remain indistinguishable/provisional; no production map is adopted.'},
        'no_dsp_model_render_spectral_metric_local_alignment_or_new_recording': True,
        'existing_alignment_scores_runtime_and_packages_unchanged': True}
    write_new(out / 'protocol-frozen.json', protocol)
    print(json.dumps({'candidate_maps': maps, 'validation_note_counts': {p: sum(n['patch'] == p for n in selected) for p in VALIDATION_PATCHES}}, indent=2))


def measure(args):
    out = args.output.resolve()
    if (out / 'result.json').exists():
        raise ValueError('Refusing to overwrite completed measurement')
    protocol = read(out / 'protocol-frozen.json')
    for name, source in protocol['source_files'].items():
        if sha(source['path']) != source['sha256']:
            raise ValueError(f'Frozen source changed: {name}')
    fs, audio = wavfile.read(protocol['source_files']['recording']['path'])
    if fs != 48000 or audio.dtype != np.int16:
        raise ValueError('Expected original48k PCM16 recording')
    mid = audio.astype(float).mean(axis=1) / 32768.
    measurements, curve_rows = [], []
    for note in protocol['metadata_selected_validation_notes']:
        onset = note['audio_on']
        begin, end = int((onset - .2) * fs), int((onset + .25) * fs)
        tt = np.arange(begin, end) / fs
        row = {'note': note, 'observations': []}
        for ms in (12, 24, 48):
            count = round(ms * .001 * fs)
            count += 1 - count % 2
            w = signal.windows.hann(count, sym=True)
            w /= w.sum()
            amplitude = 2 * abs(signal.fftconvolve(mid[begin:end] * np.exp(-2j * np.pi * note['frequency_nominal_hz'] * tt), w, mode='same'))
            relative = tt - onset
            before = float(np.median(amplitude[(relative >= -.12) & (relative <= -.07)]))
            after = float(np.median(amplitude[(relative >= .07) & (relative <= .11)]))
            observation = {'window_ms': ms, 'before_amplitude': before, 'after_amplitude': after,
                'contrast': after / max(before, 1e-12), 'thresholds': []}
            for fraction in (.1, .5, .9):
                target = before + fraction * (after - before)
                indices = np.flatnonzero((relative[:-1] >= -.08) & (relative[:-1] <= .14) & (amplitude[:-1] < target) & (amplitude[1:] >= target))
                crossing = None
                for j in indices:
                    if np.mean(amplitude[j + 1:j + 1 + round(.002 * fs)] >= target) > .9:
                        position = (target - amplitude[j]) / (amplitude[j + 1] - amplitude[j])
                        crossing = float(relative[j] + position / fs)
                        break
                observation['thresholds'].append({'fraction': fraction, 'residual_seconds': crossing,
                    'valid': bool(crossing is not None and after > before and after >= 2 * before)})
            row['observations'].append(observation)
            if ms == 24:
                curve_rows.append((note, relative, amplitude, before, after))
        measurements.append(row)
    groups = group_rows(measurements)
    usable = [p for p in VALIDATION_PATCHES if sum(g['patch'] == p for g in groups) >= 2]
    scores = []
    for mapping in protocol['candidate_maps']:
        group_scores = [{**g, 'candidate_residual_seconds': g['audible_on'] - (mapping['offset_seconds'] + mapping['scale'] * g['midi_on'])} for g in groups]
        patches = []
        for patch in VALIDATION_PATCHES:
            items = [g['candidate_residual_seconds'] for g in group_scores if g['patch'] == patch]
            patches.append({'patch': patch, 'valid_group_count': len(items), 'usable_for_primary': patch in usable,
                'median_signed_residual_seconds': float(np.median(items)) if items else None,
                'median_absolute_residual_seconds': float(np.median(abs(np.array(items)))) if items else None,
                'minimum_residual_seconds': min(items) if items else None,
                'maximum_residual_seconds': max(items) if items else None})
        errors = [p['median_absolute_residual_seconds'] for p in patches if p['usable_for_primary']]
        scores.append({'candidate': mapping, 'primary_score_seconds': float(np.mean(errors)) if errors else None,
            'patches': patches, 'groups': group_scores})
    rule = protocol['acceptance_rule']
    total = sum(g['patch'] in usable for g in groups)
    coverage = len(usable) >= rule['minimum_usable_validation_patches'] and total >= rule['minimum_total_valid_onset_groups']
    baseline = scores[0]
    for score in scores:
        score['primary_reduction_fraction_vs_unchanged'] = 1 - score['primary_score_seconds'] / baseline['primary_score_seconds'] if score['primary_score_seconds'] is not None else None
        regressions = [p['median_absolute_residual_seconds'] - b['median_absolute_residual_seconds'] for p, b in zip(score['patches'], baseline['patches']) if p['usable_for_primary']]
        score['maximum_patch_error_regression_seconds'] = max(regressions) if regressions else None
        score['improved_eligible'] = bool(coverage and score['candidate']['id'] != 'unchanged' and score['primary_reduction_fraction_vs_unchanged'] >= rule['minimum_primary_score_reduction_fraction_vs_unchanged'] and score['maximum_patch_error_regression_seconds'] <= rule['maximum_per_patch_median_absolute_error_regression_seconds'])
    eligible = sorted([s for s in scores if s['improved_eligible']], key=lambda s: s['primary_score_seconds'])
    unique = None
    if eligible:
        others = [s for s in eligible[1:]]
        if not others or all(s['primary_score_seconds'] - eligible[0]['primary_score_seconds'] >= rule['minimum_primary_score_margin_seconds_for_unique_map_selection'] for s in others):
            unique = eligible[0]['candidate']['id']
    sensitivity = []
    for row in measurements:
        primary = half_crossing(row)
        values = {str(ms): half_crossing(row, ms) for ms in (12, 24, 48)}
        sensitivity.append({'note_id': row['note']['id'], 'patch': row['note']['patch'], 'midi': row['note']['midi'],
            'half_crossings_seconds': values,
            'absolute_24_vs48_difference_seconds': abs(primary - values['48']) if primary is not None and values['48'] is not None else None})
    report = {'protocol_sha256': sha(out / 'protocol-frozen.json'), 'source_sha256': {k: v['sha256'] for k, v in protocol['source_files'].items()},
        'measurements': measurements, 'validation_onset_groups': groups, 'scores': scores,
        'coverage': {'usable_patches': usable, 'valid_groups_in_usable_patches': total, 'acceptance_coverage_pass': coverage},
        'unique_candidate_satisfying_frozen_rule': unique, 'window_sensitivity': sensitivity,
        'interpretation': 'Held-out timing observations within reused audio; no production map adopted, no chip-clock recovery claimed.',
        'old_alignment_scores_runtime_and_packages_changed': False}
    write_new(out / 'result.json', report)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(max(1, len(curve_rows)), 1, figsize=(9, max(3, len(curve_rows) * 2)), squeeze=False)
    for ax, (note, xx, yy, lo, hi) in zip(axes[:, 0], curve_rows):
        ax.plot(xx, (yy - lo) / max(hi - lo, 1e-12))
        ax.axvline(0, color='k')
        ax.axhline(.5, color='gray', ls=':')
        ax.set(xlim=(-.08, .14), ylim=(-.3, 1.6), title=f'Validation patch{note["patch"]} MIDI{note["midi"]}; old-map onset{note["audio_on"]:.6f}s')
    fig.tight_layout()
    fig.savefig(out / 'validation-onset-traces.png')
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 4))
    for score in scores:
        ax.scatter([g['old_mapped_on'] for g in score['groups']], [1000 * g['candidate_residual_seconds'] for g in score['groups']], label=score['candidate']['id'])
    ax.axhline(0, color='k')
    ax.set(xlabel='Old mapped audio time (seconds)', ylabel='Held-out onset residual (ms)')
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / 'candidate-validation-residuals.png')
    plt.close(fig)
    print(json.dumps({'coverage': report['coverage'], 'unique_candidate': unique,
        'scores': [{k: s[k] for k in ['candidate', 'primary_score_seconds', 'primary_reduction_fraction_vs_unchanged', 'maximum_patch_error_regression_seconds', 'improved_eligible']} for s in scores]}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['freeze', 'measure'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reference-root', type=Path)
    parser.add_argument('--calibration-report', type=Path, default=ROOT / 'Docs/research/midi-alignment-audit-2026-10-18.json')
    parser.add_argument('--bank', type=Path, default=ROOT / 'Assets/FactoryBank/press78-factory.json')
    args = parser.parse_args()
    if args.action == 'freeze':
        if args.reference_root is None:
            parser.error('--reference-root is required for freeze')
        freeze(args)
    else:
        measure(args)


if __name__ == '__main__':
    main()
