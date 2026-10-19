#!/usr/bin/env python3
"""Check the bounded MN3206 DC component; no audio rendering or DSP imports."""

from fractions import Fraction as F
import hashlib
from itertools import product
import json
import math
from pathlib import Path
import sys

from mn3206_dc import MN3206DC


COUNT = 0


def check(condition, message):
    global COUNT
    COUNT += 1
    if not condition:
        raise AssertionError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    here = Path(__file__).resolve().parent
    out = Path(sys.argv[1])
    if out.exists():
        raise FileExistsError('Results are immutable; choose a new output path')
    design = json.loads((here / 'design-frozen-v3.json').read_text())
    pixels = json.loads((here / 'digitized-pixels.json').read_text())
    for source in design['sources'].values():
        if isinstance(source, dict) and 'path' in source:
            source_path = Path(source['path'])
            check(source_path.stat().st_size == source['bytes'], 'Source byte count')
            check(digest(source_path) == source['sha256'], 'Primary source hash')
    binding = json.loads((here / 'implementation-bound-v2.json').read_text())
    for name, expected in binding['files'].items():
        check(digest(here / name) == expected, 'Pre-execution implementation binding')
    first = json.loads((here / 'extraction-failed-support-v1.json').read_text())
    check(pixels['pixel_x'] == first['pixel_x'][:-1], 'Unchanged original 18 x knots')
    check(pixels['pixel_y'] == first['pixel_y'][:-1], 'Unchanged original 18 y knots')
    check(first['pixel_x'][-1] == 373 and first['pixel_y'][-1] is None, 'Failed support retained')
    history = here / 'historical-first-run'
    historical = json.loads((history / 'manifest.json').read_text())
    for name, expected in historical['files'].items():
        check(digest(history / name) == expected, 'Original successful source and receipt preserved')

    model = MN3206DC()
    conditions = dict(mode='settled_dc_only', vdd_v=5.0,
                      vgg_v=14 / 15 * 5, cp_hz=10000.0,
                      temperature_c=25.0, vss_v=0.0)
    check(model.nominal_input_range_exact_v == (F(0), F(1146, 269)), 'Nominal support')
    check(model.input_range_exact_v == (F(24, 269), F(1122, 269)), 'Common scenario support')
    check(F(model.input_range_v[0]) >= F(24, 269), 'Inward-rounded lower endpoint')
    check(F(model.input_range_v[1]) <= F(1122, 269), 'Inward-rounded upper endpoint')

    # Independent voltage-space representation of the digitized polyline.
    vx = [6 * F(x - 171, 269) for x in pixels['pixel_x']]
    vy = [6 * (F(553) - F(y)) / 358 for y in pixels['pixel_y']]

    def oracle(voltage):
        index = next(i for i in range(len(vx) - 1) if vx[i] <= voltage <= vx[i + 1])
        return ((vx[index + 1] - voltage) * vy[index] +
                (voltage - vx[index]) * vy[index + 1]) / (vx[index + 1] - vx[index])

    valid_knots = 0
    for voltage, expected in zip(vx, vy):
        if model.input_range_exact_v[0] <= voltage <= model.input_range_exact_v[1]:
            result = model.operating_point(voltage, **conditions)
            check(result.nominal_output_v == float(expected), 'Exact nominal graph knot')
            valid_knots += 1
    check(valid_knots == 16, 'All common-support knots tested')

    low, high = model.input_range_exact_v
    grid = [low + (high - low) * F(i, 100) for i in range(101)]
    results = [model.operating_point(v, **conditions) for v in grid]
    scenario_checks = 0
    for voltage, result in zip(grid, results):
        check(result.nominal_output_v == float(oracle(voltage)), 'Independent voltage interpolation')
        check(result.graph_scenario_low_v <= result.nominal_output_v <= result.graph_scenario_high_v,
              'Nominal is within declared graph-reading scenario envelope')
        scenario_values = []
        for ax, bx, dx, ay, by, dy in product((-1, 1), repeat=6):
            # Independently transform each requested graph voltage into the
            # nominal voltage coordinates, then use the voltage-space oracle.
            pixel_x = 171 + ax + voltage / 6 * (269 + bx - ax) + 3 * dx
            nominal_x_voltage = (pixel_x - 171) * 6 / 269
            nominal_y_voltage = oracle(nominal_x_voltage)
            pixel_y = 553 - nominal_y_voltage * 358 / 6 + 3 * dy
            output = 6 * (553 + ay - pixel_y) / (358 + ay - by)
            check(F(result.graph_scenario_low_v) <= output <= F(result.graph_scenario_high_v),
                  'Independent coordinate corner lies inside returned interval')
            scenario_values.append(output)
            scenario_checks += 1
        check(abs(result.graph_scenario_low_v - float(min(scenario_values))) <= 1e-14,
              'Lower scenario endpoint')
        check(abs(result.graph_scenario_high_v - float(max(scenario_values))) <= 1e-14,
              'Upper scenario endpoint')
    check([model.operating_point(v, **conditions) for v in reversed(grid)] == list(reversed(results)),
          'No query-order state')
    for voltage in model.input_range_v:
        check(math.isfinite(model.operating_point(voltage, **conditions).nominal_output_v),
              'Conservative binary64 boundary remains supported')

    def reject(input_v=2.5, **changed):
        candidate = dict(conditions)
        candidate.update(changed)
        try:
            model.operating_point(input_v, **candidate)
        except (ValueError, TypeError):
            check(True, 'Unsupported port rejected')
        else:
            check(False, 'Unsupported port unexpectedly accepted')

    for v in (F(0), F(9, 2), F(6), low - F(1, 10**12), high + F(1, 10**12),
              math.nextafter(model.input_range_v[0], -math.inf),
              math.nextafter(model.input_range_v[1], math.inf)):
        reject(v)
    for key, value in [('mode', 'audio'), ('mode', None), ('vdd_v', 4.0),
                       ('vdd_v', 5.01), ('vgg_v', 4.5), ('cp_hz', 40000.0),
                       ('temperature_c', 24.0), ('vss_v', 1.0)]:
        reject(**{key: value})
    invalid = (True, False, None, '2.5', complex(2, 0), float('nan'),
               float('inf'), -float('inf'), 10**1000)
    for value in invalid:
        reject(value)
        for name in ('vdd_v', 'vgg_v', 'cp_hz', 'temperature_c', 'vss_v'):
            reject(**{name: value})
    try:
        model.operating_point(2.5)
    except TypeError:
        check(True, 'All condition ports are required')
    else:
        check(False, 'Missing ports unexpectedly accepted')

    # Representation-only correction: no physical operating corner is added.
    canonical_vgg = float(F(14, 3))
    reference = model.operating_point(F(5, 2), **conditions)
    for value in (F(14, 3), canonical_vgg, F(canonical_vgg)):
        exact_ports = dict(conditions, vgg_v=value)
        check(model.operating_point(F(5, 2), **exact_ports) == reference,
              'Exact mathematical VGG and sole binary64 alias agree')
    for value in (math.nextafter(canonical_vgg, -math.inf),
                  math.nextafter(canonical_vgg, math.inf),
                  F(14, 3) - F(1, 10**12), F(14, 3) + F(1, 10**12),
                  F(14, 3) - F(1, 2**100), F(14, 3) + F(1, 2**100)):
        reject(vgg_v=value)
    for offset in (-1, 1):
        check(float(F(14, 3) + offset * F(1, 2**100)) == canonical_vgg,
              'Rejected nearby rational really would round to accepted float alias')

    examples = []
    for voltage in (.1, .5, 1.0, 2.0, 2.5, 3.0, 4.0, 4.15):
        examples.append(vars(model.operating_point(voltage, **conditions)))
    result = {
        'schema': 'press78.mn3206-dc-validation.v2', 'date': '2026-10-19',
        'passed': True, 'assertions': COUNT, 'digitized_points': len(vx),
        'common_support_knots_checked': valid_knots, 'interior_queries': len(grid),
        'independent_corner_checks': scenario_checks,
        'conditions': conditions,
        'nominal_digitized_support_exact_v': [str(v) for v in model.nominal_input_range_exact_v],
        'common_scenario_support_exact_v': [str(v) for v in model.input_range_exact_v],
        'common_scenario_support_v': model.input_range_v,
        'examples': examples,
        'files': {name: digest(here / name) for name in binding['files']},
        'implementation_binding_sha256': digest(here / 'implementation-bound-v2.json'),
        'condition_representation': {
            'vgg_exact_v': '14/3',
            'nearest_binary64_alias_hex': canonical_vgg.hex(),
            'nearest_binary64_alias_exact_v': str(F(canonical_vgg)),
            'nearby_rationals_or_adjacent_binary64_accepted': False,
            'physical_tolerance_added': False,
        },
        'historical_first_run': {
            'manifest_sha256': digest(history / 'manifest.json'),
            'validation_sha256': digest(history / 'validation.json'),
            'assertions': json.loads((history / 'validation.json').read_text())['assertions'],
            'root_review_sha256': digest(history / 'root-port-semantics-v1.json'),
            'correction_protocol_sha256': digest(here / 'port-semantics-correction-frozen.json'),
            'description': 'The first source passed its 6976 checks but rejected exact rational VGG14/3. Historical source, tests, receipt and publication remain unchanged; this run corrects representation semantics only.',
        },
        'primary_source': design['sources'],
        'scope': 'Fixed-condition, settled-DC graph interpolation and 64 declared coordinate-reading corner scenarios only. No audio, noise, dynamic response, device-tolerance estimate, target circuit or Drive calibration.',
        'production_changes': False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': True, 'assertions': COUNT,
                      'common_support_v': model.input_range_v,
                      'independent_corner_checks': scenario_checks}))


if __name__ == '__main__':
    main()
