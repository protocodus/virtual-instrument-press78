#!/usr/bin/env python3
"""Validate the research-only local supply against independent circuit solves.

No media, actual supply waveform, DAC law or production DSP is used.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
# Import this dependency-free component directly, without the research
# package's NumPy/SciPy audio imports. The check also runs in standard CI.
sys.path.insert(0, str(ROOT / 'Tools' / 'reference' / 'circuit'))
from supply import LocalSupply


def binding(relative):
    data = (ROOT / relative).read_bytes()
    return {'path': relative, 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    model = LocalSupply()
    r, c = model.resistance_ohm, model.capacitance_farad
    checks = []

    def check(name, condition, **details):
        checks.append({'name': name, 'passed': bool(condition), **details})

    # Independent one-node AC KCL: (V-U)/R+j*w*C*V+I=0.
    rows = []
    ac_errors = []
    for hz in (0, .1, 1, 5, 7.2049, 10, 50, 60, 100, 120, 1000):
        h, z = model.transfer(hz)
        admittance = 1/r + 2j*math.pi*hz*c
        expected_h = (1/r)/admittance
        expected_z = -1/admittance
        ac_errors.extend((abs(h-expected_h), abs(z-expected_z)/r))
        rows.append({'hz': hz, 'upstream_voltage_gain_db':
                     20*math.log10(abs(h)), 'upstream_phase_deg':
                     math.degrees(math.atan2(h.imag, h.real)),
                     'load_impedance_magnitude_ohm': abs(z)})
    check('AC KCL two-port transfer', max(ac_errors) < 2e-15,
          max_normalized_error=max(ac_errors))

    # Separate explicit RK4 integrator for a prescribed, nonaudio excitation.
    # Segment boundaries are never crossed inside an integration step.
    prescribed = ((.003, .1, 0), (.017, .1, .001),
                  (.011, -.025, -.00025), (.083, 0, 0))
    exact = rk = 0.0
    rk_errors = []
    for seconds, upstream, load in prescribed:
        exact = model.advance(exact, upstream, load, seconds)
        steps = math.ceil(seconds / 1e-5)
        dt = seconds / steps
        def derivative(v):
            return ((upstream-v)/r-load)/c
        for _ in range(steps):
            k1 = derivative(rk)
            k2 = derivative(rk+dt*k1/2)
            k3 = derivative(rk+dt*k2/2)
            k4 = derivative(rk+dt*k3)
            rk += dt*(k1+2*k2+2*k3+k4)/6
        rk_errors.append(abs(exact-rk))
    check('Piecewise source/load versus independent RK4 KCL',
          max(rk_errors) < 1e-12, max_voltage_error=max(rk_errors))

    unit_load = []
    for seconds in (.001, .01, model.time_constant_seconds, .1, 1):
        voltage = model.advance(0, 0, .001, seconds)
        unit_load.append({'duration_seconds': seconds,
                          'local_delta_v': voltage})
    check('One mA load steady change is minus47mV',
          abs(unit_load[-1]['local_delta_v']+.047) < 1e-15)
    check('Source/load cancellation',
          model.advance(0, .047, .001, 1) == 0)
    check('No excitation is exactly silent',
          all(model.advance(0, 0, 0, dt) == 0
              for dt in (0, 1/192000, .001, 1, 1e9)))
    check('Elapsed time partition invariant',
          abs(model.advance(model.advance(.003, -.01, .002, .003),
                            -.01, .002, .007)
              - model.advance(.003, -.01, .002, .01)) < 1e-16)
    check('Zero duration preserves state', model.advance(.123, .1, .01, 0) == .123)

    # Explicit alternate component values, with no tolerance/aging distribution.
    other = LocalSupply(94, 235e-6)
    a, b = model.transfer(100), other.transfer(100)
    check('Same RC, doubled source resistance doubles load droop only',
          abs(a[0]-b[0]) < 1e-15 and abs(2*a[1]-b[1]) < 1e-14)
    rejected = 0
    bad_calls = [lambda: LocalSupply(0, c), lambda: LocalSupply(r, -1),
                 lambda: LocalSupply(float('inf'), c),
                 lambda: LocalSupply(1e300, 1e300),
                 lambda: LocalSupply(1e-300, 1e-300),
                 lambda: model.transfer(-1),
                 lambda: model.transfer(float('nan')),
                 lambda: model.advance(0, 0, 0, -1),
                 lambda: model.advance(float('nan'), 0, 0, 1)]
    for call in bad_calls:
        try:
            call()
        except ValueError:
            rejected += 1
    check('Nonphysical or nonfinite inputs rejected',
          rejected == len(bad_calls), rejected=rejected)
    result = {
        'schema': 'press78.local-supply-validation.v1',
        'scope': 'Research-only PSS480 incremental local RC supply; not audio or target780 validation.',
        'components': {'r_ohm': r, 'c_farad': c},
        'time_constant_seconds': model.time_constant_seconds,
        'corner_hz': 1/(2*math.pi*model.time_constant_seconds),
        'checks': checks, 'passed': all(row['passed'] for row in checks),
        'frequency_response': rows,
        'unit_response_1mA_extra_load': unit_load,
        'unit_response_limit': 'Specified1mA sensitivity probe, not measured instrument current or default audio sag.',
        'bindings': [binding('Tools/reference/circuit/supply.py'),
                     binding('Tools/check_supply.py'),
                     binding('Docs/research/lofi-signal-path-audit-2026-10-19.json')],
        'excluded': ['noise/excitation generation', 'actual operating point',
                     'DAC/headroom/pitch voltage coupling', 'regulator/input battery model',
                     'capacitor ESR/aging or tolerance distribution',
                     'target780 topology equivalence', 'production DSP changes']}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'passed': result['passed'], 'checks': len(checks),
                      'corner_hz': result['corner_hz'],
                      'max_rk4_voltage_error': max(rk_errors)}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
