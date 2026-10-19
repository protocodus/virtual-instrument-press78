#!/usr/bin/env python3
"""Reproduce the frozen, posthoc OPU frequency candidate; never edit production.

The tracked research ledger contains every input observation needed for scoring:
  python3 Tools/audit_opu_frequency.py \
    --report Reference/Research/opu-frequency-hypothesis-20261019.json \
    --out build/opu-frequency-reproduction

Alternatively supply --protocol, --producer, --pitch-result and --pitch-protocol
to verify and consume the original local JSONs. Requires NumPy, no recordings.
Use --prototype-source Source/DSP to additionally copy a research engine into
the new output directory and replace ONLY its base-frequency expression. This
does not compile, render, modify CMake or install anything. Its header/recipe is
an arithmetic hypothesis, not an OPU register-width or native-clock claim.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import shutil
import statistics

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = [round(440 * 2 ** ((60 + c - 69) / 12) * 2 ** 24 / 5500000) for c in range(12)]
REQUIRED_BASE = [798, 846, 896, 949, 1005, 1065, 1129, 1196, 1267, 1342, 1422, 1507]
SCORE_KEYS = ('producer_offsets', 'producer_summary', 'producer_by_pack', 'producer_rows',
              'old780_anchor_ids', 'old780_offsets', 'old780_summary', 'old780_by_note',
              'old780_rows', 'fixed_interval_predictions')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def et(note):
    return 440 * 2 ** ((note - 69) / 12)


def word(note):
    require(isinstance(note, int) and 0 <= note <= 127, 'MIDI note outside0..127')
    return math.floor(6 * BASE[note % 12] * 2 ** ((note - 60) // 12))


def frequency(note):
    return 5500000 / (6 * 2 ** 24) * word(note)


def cents(a, b):
    require(math.isfinite(a) and math.isfinite(b) and a > 0 and b > 0,
            'Frequency must be finite and positive')
    return 1200 * math.log2(a / b)


def stats(values):
    a = np.asarray(values, dtype=float)
    require(len(a) > 0 and np.isfinite(a).all(), 'Empty/nonfinite score group')
    return {'count': len(values), 'mean_abs_cents': float(np.mean(np.abs(a))),
            'rms_cents': float(np.sqrt(np.mean(a * a))),
            'median_abs_cents': float(np.median(np.abs(a))),
            'max_abs_cents': float(np.max(np.abs(a))),
            'mean_signed_cents': float(np.mean(a)),
            'min_cents': float(np.min(a)), 'max_cents': float(np.max(a))}


def score(protocol, notes, old_rows, anchor_ids):
    """Same equations/order as the original evaluator; retain rejected rows."""
    require(BASE == REQUIRED_BASE, 'Derived seeds disagree with frozen candidate')
    candidate = protocol['candidate']
    require(candidate['base12_C_to_B'] == BASE and candidate['nominal_clock_hz'] == 5500000
            and candidate['denominator'] == 6 * 2 ** 24 and candidate['noise'] == 0,
            'Protocol is not the frozen candidate')
    require(len(notes) == 63 and sum(x['interval_fixture_accepted'] for x in notes) == 62,
            'Expected original63 rows with62 source-qualified observations')
    models = {'equal_tempered': et, 'candidate': frequency}
    producer = []
    pack_offsets, pack_summaries = {}, {}
    for pack in sorted({x['file'] for x in notes}):
        rows = [x for x in notes if x['file'] == pack]
        offsets = {name: statistics.median(
            statistics.mean(cents(x[m], fun(x['expected_musical_midi_under_authored_sequence']))
                            for m in ('fft_frequency_hz', 'phase_frequency_hz'))
            for x in rows if x['interval_fixture_accepted']) for name, fun in models.items()}
        pack_offsets[pack] = {name: {'cents': o, 'combined_clock_tuning_ratio_ppm': (2 ** (o / 1200) - 1) * 1e6}
                              for name, o in offsets.items()}
        for x in rows:
            row = dict(x)
            n = x['expected_musical_midi_under_authored_sequence']
            row.update(candidate_word=word(n), candidate_hz=frequency(n), equal_tempered_hz=et(n))
            row['residuals_cents'] = {name: {method: cents(x[key], fun(n)) - offsets[name]
                                            for method, key in [('fft', 'fft_frequency_hz'), ('phase', 'phase_frequency_hz')]}
                                     for name, fun in models.items()}
            producer.append(row)
        selected = [x for x in producer if x['file'] == pack and x['interval_fixture_accepted']]
        pack_summaries[pack] = {name: {m: stats([x['residuals_cents'][name][m] for x in selected])
                                      for m in ('fft', 'phase')} for name in models}
    producer_summary = {name: {m: stats([x['residuals_cents'][name][m] for x in producer
                                         if x['interval_fixture_accepted']])
                               for m in ('fft', 'phase')} for name in models}
    anchors = [x for x in old_rows if x['source'] == 'opus_float' and x['channel'] == 'mid'
               and x['window']['window_variant'] == 'original' and x['window']['event_index'] in anchor_ids]
    require(sorted(anchor_ids) == [1760, 1770] and len(anchors) == 2
            and all(x['window']['midi'] == 67 and x['estimates']['phase12']['valid'] for x in anchors),
            'Expected the two original long G67 calibration anchors')
    old_offsets = {name: statistics.mean(cents(x['estimates']['phase12']['hz'], fun(67)) for x in anchors)
                   for name, fun in models.items()}
    output_rows = []
    for x in old_rows:
        if x['window']['window_variant'] != 'original':
            continue
        row = dict(x)
        n = x['window']['midi']
        row.update(calibration_anchor=x['window']['event_index'] in anchor_ids,
                   candidate_hz=frequency(n), equal_tempered_hz=et(n), candidate_word=word(n))
        row['residuals_cents'] = {name: {method: (cents(value['hz'], fun(n)) - old_offsets[name]
                                                 if value.get('valid') and value.get('hz', 0) > 0 else None)
                                        for method, value in x['estimates'].items()}
                                 for name, fun in models.items()}
        output_rows.append(row)
    primary = [x for x in output_rows if x['source'] == 'opus_float' and x['channel'] == 'mid']
    require(len(primary) == 19, 'Expected all19 original Opus-mid windows')
    old_summary = {}
    groups = [('all19', primary), ('noncalibration17', [x for x in primary if not x['calibration_anchor']]),
              ('unfitted_D62_Ab68', [x for x in primary if x['window']['midi'] in (62, 68)])]
    for label, selected in groups:
        old_summary[label] = {name: stats([x['residuals_cents'][name]['phase12'] for x in selected
                                           if x['residuals_cents'][name]['phase12'] is not None]) for name in models}
    class_summary = {str(n): {name: stats([x['residuals_cents'][name]['phase12'] for x in primary
                                           if x['window']['midi'] == n]) for name in models}
                     for n in sorted({x['window']['midi'] for x in primary})}
    predictions = [{'low_midi': low, 'high_midi': high,
                    'interval_error_cents': cents(frequency(high) / frequency(low), et(high) / et(low))}
                   for low, high in [(39, 51), (39, 75), (39, 79), (67, 75), (75, 79), (56, 62), (68, 72), (62, 68)]]
    return {'producer_offsets': pack_offsets, 'producer_summary': producer_summary,
            'producer_by_pack': pack_summaries, 'producer_rows': producer,
            'old780_anchor_ids': sorted(anchor_ids),
            'old780_offsets': {k: {'cents': v, 'combined_clock_tuning_ratio_ppm': (2 ** (v / 1200) - 1) * 1e6}
                               for k, v in old_offsets.items()},
            'old780_summary': old_summary, 'old780_by_note': class_summary, 'old780_rows': output_rows,
            'fixed_interval_predictions': predictions}


def emit_prototype(source, output):
    """Generate a reviewable copy; never write to the input source directory."""
    source = source.resolve()
    require(source.is_dir() and (source / 'Press78Engine.cpp').is_file(), 'Missing DSP source directory')
    require(not output.is_relative_to(source), 'Output must not be inside the DSP input directory')
    destination = output / 'prototype' / 'Source' / 'DSP'
    destination.mkdir(parents=True)
    paths = sorted([*source.glob('*.h'), *source.glob('*.cpp')])
    original_hashes = {p.name: sha(p) for p in paths}
    for path in paths:
        shutil.copyfile(path, destination / path.name)
    header = '''#pragma once
#include <array>
#include <cstdint>
// Behavioral hypothesis only: no recovered OPU register width or cadence.
namespace press78_research {
inline constexpr std::array<std::uint32_t,12> base{SEEDS};
constexpr std::uint32_t phaseWord(int n) noexcept {
  n=n<0?0:n>127?127:n; const int octave=n/12-5;
  const auto word=6U*base[static_cast<std::size_t>(n%12)];
  return octave>=0?word<<octave:word>>(-octave);
}
constexpr double frequencyHz(int n) noexcept {return (5500000.0/(6.0*16777216.0))*phaseWord(n);}
}
'''.replace('SEEDS', ','.join(map(str, BASE)))
    (destination / 'FrequencyHypothesis.h').write_text(header)
    cpp = destination / 'Press78Engine.cpp'
    code = cpp.read_text()
    old = 'const double base = 440.0 * std::pow(2.0, (note - 69) / 12.0);'
    require(code.count(old) == 1, 'Copied source no longer matches the reviewed step() expression')
    code = code.replace('#include "Press78Engine.h"', '#include "Press78Engine.h"\n#include "FrequencyHypothesis.h"', 1)
    code = code.replace(old, 'const double base = press78_research::frequencyHz(note);')
    cpp.write_text(code)
    probe = '''#include "FrequencyHypothesis.h"
#include <iomanip>
#include <iostream>
int main(){std::cout<<std::setprecision(17);
for(int n=0;n<128;++n)std::cout<<n<<" "<<press78_research::phaseWord(n)<<" "<<press78_research::frequencyHz(n)<<"\\n";}
'''
    (output / 'prototype' / 'FrequencyProbe.cpp').write_text(probe)
    (output / 'prototype' / 'README.md').write_text(
        '# Research-only copied engine\n\nOnly step() base-frequency selection changed. No common capture-clock correction is embedded. '
        'The source retains its own internal rate, latency, multiplier/detune laws and controls. '
        'No production, CMake, GUI or host file is modified.\n\n'
        'From this generated prototype directory, compile the arithmetic probe:\n\n'
        '```sh\nc++ -std=c++17 -O2 -ISource/DSP FrequencyProbe.cpp -o frequency_probe\n'
        './frequency_probe\n```\n\n'
        'Compare all128 lines with ../result.json midi_words. For an offline instrument render, compile '
        'the repository Tools/NativeRender.cpp against this copied Press78Engine.cpp, using this copied '
        'Source/DSP include directory. Use --transparent and zero clock/drift, drive and chorus controls '
        'for pure-carrier checks. Do not install this executable or substitute the copy into production.\n')
    require(all(sha(source / name) == digest for name, digest in original_hashes.items()), 'Original source changed during copy')
    return {'input_source_directory': str(source), 'input_sha256': original_hashes,
            'generated_sha256': {str(p.relative_to(output)): sha(p) for p in sorted((output / 'prototype').rglob('*')) if p.is_file()},
            'production_unchanged_during_generation': True, 'compiled_or_rendered': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--report', type=Path, help='Tracked complete frozen research ledger; simplest reproducible input')
    parser.add_argument('--protocol', type=Path, help='Original frozen candidate protocol, for raw-input mode')
    parser.add_argument('--producer', type=Path, help='Original fixture-notes.json')
    parser.add_argument('--pitch-result', type=Path, help='Original pitch-grid result.json')
    parser.add_argument('--pitch-protocol', type=Path, help='Original pitch-grid protocol-frozen.json')
    parser.add_argument('--out', type=Path, required=True, help='New/empty output; inside this repository it must be under an ignored build directory')
    parser.add_argument('--prototype-source', type=Path, help='Optional DSP directory to copy into output; never modified')
    args = parser.parse_args()
    raw_paths = [args.protocol, args.producer, args.pitch_result, args.pitch_protocol]
    require(bool(args.report) != any(raw_paths), 'Choose --report OR all four original JSON options')
    ledger = None
    if args.report:
        ledger = json.loads(args.report.read_text())
        protocol, notes, old_rows = ledger['protocol'], ledger['producer_rows'], ledger['old780_rows']
        anchor_ids = set(ledger['old780_anchor_ids'])
        input_hashes = {str(args.report.resolve()): sha(args.report)}
    else:
        require(all(raw_paths), 'Raw-input mode requires all four JSON options')
        protocol = json.loads(args.protocol.read_text())
        bindings = [('build/isolated-source-search-20261019/fixture-notes.json', args.producer),
                    ('build/pitch-grid-audit-20261019/result.json', args.pitch_result),
                    ('build/pitch-grid-audit-20261019/protocol-frozen.json', args.pitch_protocol)]
        for key, path in bindings:
            require(sha(path) == protocol['source_sha256'][key], 'Frozen input hash mismatch: ' + key)
        notes = json.loads(args.producer.read_text())
        old_rows = json.loads(args.pitch_result.read_text())['rows']
        anchor_ids = {x[0] for x in json.loads(args.pitch_protocol.read_text())['primary_pair_events']}
        input_hashes = {str(p.resolve()): sha(p) for p in raw_paths}
    result = score(protocol, notes, old_rows, anchor_ids)
    if ledger is not None:
        require(all(result[k] == ledger[k] for k in SCORE_KEYS), 'Recomputed scores differ from frozen ledger')
    result['base12_C_to_B'] = BASE
    result['midi_words'] = [{'midi': n, 'word': word(n), 'hz': frequency(n)} for n in range(128)]
    primary = [x for x in result['old780_rows'] if x['source'] == 'opus_float' and x['channel'] == 'mid']
    result['all19_primary_residuals_descending'] = sorted([
        {'event_index': x['window']['event_index'], 'midi': x['window']['midi'],
         'candidate_cents': x['residuals_cents']['candidate']['phase12'],
         'equal_tempered_cents': x['residuals_cents']['equal_tempered']['phase12']} for x in primary],
        key=lambda x: abs(x['candidate_cents']), reverse=True)
    output = args.out.resolve()
    if output.is_relative_to(ROOT):
        relative = output.relative_to(ROOT)
        require(len(relative.parts) > 1 and relative.parts[0].startswith('build'), 'Repository output must be under build*/')
    require(not output.exists() or (output.is_dir() and not any(output.iterdir())), 'Refusing nonempty output directory')
    output.mkdir(parents=True, exist_ok=True)
    prototype = emit_prototype(args.prototype_source, output) if args.prototype_source else None
    receipt = {'scope': 'Tooling reproduction of previously frozen posthoc arithmetic/scores, not a new measurement or holdout.',
               'input_sha256': input_hashes, 'tool_sha256': sha(__file__), 'numpy_version': np.__version__,
               'frozen_ledger_exact_numerical_reproduction': True if ledger is not None else None,
               'base_count': 12, 'midi_word_count': 128, 'producer_rows': 63, 'producer_qualified': 62,
               'old780_primary_rows': 19, 'outliers_removed': 0, 'prototype': prototype,
               'noise_added': False, 'production_modified': False}
    (output / 'result.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    receipt['result_sha256'] = sha(output / 'result.json')
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('prototype', 'input_sha256')}, indent=2))


if __name__ == '__main__':
    main()
