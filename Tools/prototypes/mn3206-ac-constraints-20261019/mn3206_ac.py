"""Fixed-condition MN3206 typical aggregate-THD graph oracle, research only.

This is a manufacturer graph reader, not an audio or waveform component.
Input level is explicitly on the unresolved-reference dBm axis of p77; no
conversion from volts, power, target keyboard units or Drive is provided.
The returned coordinate scenarios are not part tolerance/confidence bounds.
"""
from bisect import bisect_right
from dataclasses import dataclass
from fractions import Fraction
import hashlib
from itertools import product
import json
import math
from numbers import Real
from pathlib import Path

DESIGN_SHA256 = 'f1bc043760ef6c45cbf6af129ec90e52755842c1c0b58efba292bc38e2aa1e7f'


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f'{name} must be an explicit finite real number')
    try:
        finite = math.isfinite(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f'{name} exceeds the numeric port domain') from exc
    if not finite:
        raise ValueError(f'{name} must be finite')
    return Fraction(value)


def _round_float(value, lower):
    result = float(value)
    if (lower and Fraction(result) > value) or (not lower and Fraction(result) < value):
        result = math.nextafter(result, -math.inf if lower else math.inf)
    return result


@dataclass(frozen=True)
class THDConstraint:
    input_level_axis_dbm: float
    nominal_thd_percent: float
    graph_scenario_low_percent: float
    graph_scenario_high_percent: float


class MN3206AC:
    """Stateless interpolation of one published typical THD panel.

    Supply all named conditions on each query. No default physical operating
    point, unspecified voltage reference or target calibration is inferred.
    """
    VGG_EXACT_V = Fraction(14, 3)
    VGG_BINARY64_ALIAS_V = float(VGG_EXACT_V)
    MODE = 'typical_thd_graph_only'
    AXIS_REFERENCE = 'manufacturer_dbm_reference_unspecified'

    def __init__(self):
        payload = Path(__file__).with_name('design-frozen.json').read_bytes()
        if hashlib.sha256(payload).hexdigest() != DESIGN_SHA256:
            raise ValueError('Model requires the exact frozen source/reading design')
        d = json.loads(payload)
        a, r = d['axis'], d['readings']
        self._x = tuple(Fraction(v) for v in r['pixel_x'])
        self._y = tuple(Fraction(v) for v in r['pixel_y'])
        if len(self._x) != len(self._y) or any(b <= a for a, b in zip(self._x, self._x[1:])):
            raise ValueError('Invalid frozen knots')
        self._x0, self._x1 = Fraction(a['x_low_px']), Fraction(a['x_high_px'])
        self._l0, self._l1 = Fraction(a['x_low_dbm']), Fraction(a['x_high_dbm'])
        self._y0, self._y1 = Fraction(a['y_zero_px']), Fraction(a['y_high_px'])
        self._h = Fraction(a['y_high_thd_percent'])
        ar, tr = Fraction(a['axis_endpoint_reading_radius_px']), Fraction(r['trace_coordinate_reading_radius_px'])
        self._xs = tuple((self._x0 + i*ar, self._x1 + j*ar, k*tr) for i,j,k in product((-1,1), repeat=3))
        self._ys = tuple((self._y0 + i*ar, self._y1 + j*ar, k*tr) for i,j,k in product((-1,1), repeat=3))
        self.nominal_input_range_exact_axis_dbm = tuple(self._level(x,self._x0,self._x1) for x in (self._x[0],self._x[-1]))
        self.input_range_exact_axis_dbm = (
            max(self._level(self._x[0]-dx,x0,x1) for x0,x1,dx in self._xs),
            min(self._level(self._x[-1]-dx,x0,x1) for x0,x1,dx in self._xs))
        low, high = self.input_range_exact_axis_dbm
        self.input_range_axis_dbm = (_round_float(low,False), _round_float(high,True))

    def _level(self, x, x0, x1):
        return self._l0 + (self._l1-self._l0)*(x-x0)/(x1-x0)

    def _trace(self, x):
        if not self._x[0] <= x <= self._x[-1]:
            raise ValueError('Query extrapolates beyond retained trace coordinates')
        i = min(len(self._x)-2,max(0,bisect_right(self._x,x)-1))
        return self._y[i]+(x-self._x[i])*(self._y[i+1]-self._y[i])/(self._x[i+1]-self._x[i])

    def _evaluate(self, level):
        t = (level-self._l0)/(self._l1-self._l0)
        y = self._trace(self._x0+t*(self._x1-self._x0))
        nominal = self._h*(self._y0-y)/(self._y0-self._y1)
        scenarios = tuple(self._h*(y0-self._trace(x0+t*(x1-x0)+dx)-dy)/(y0-y1)
                          for x0,x1,dx in self._xs for y0,y1,dy in self._ys)
        return nominal,min(scenarios),max(scenarios)

    def thd_constraint(self, input_level_axis_dbm, *, mode, axis_reference,
                       vdd_v, vgg_v, vss_v, cp_hz, signal_hz, temperature_c,
                       lpf_hz, lpf_db_per_octave):
        if mode != self.MODE or axis_reference != self.AXIS_REFERENCE:
            raise ValueError('Only the named typical panel and its unresolved-reference axis are supported')
        actual = dict(vdd_v=vdd_v,vgg_v=vgg_v,vss_v=vss_v,cp_hz=cp_hz,
                      signal_hz=signal_hz,temperature_c=temperature_c,
                      lpf_hz=lpf_hz,lpf_db_per_octave=lpf_db_per_octave)
        expected = dict(vdd_v=5,vss_v=0,cp_hz=40000,signal_hz=1000,
                        temperature_c=25,lpf_hz=20000,lpf_db_per_octave=-48)
        for name,value in actual.items():
            value = _number(value,name)
            allowed = ((self.VGG_EXACT_V,Fraction(self.VGG_BINARY64_ALIAS_V)) if name=='vgg_v' else (Fraction(expected[name]),))
            if value not in allowed:
                raise ValueError(f'Unsupported fixed graph condition: {name}')
        level = _number(input_level_axis_dbm,'input_level_axis_dbm')
        if not self.input_range_exact_axis_dbm[0] <= level <= self.input_range_exact_axis_dbm[1]:
            raise ValueError('Input level outside common graph-reading support')
        nominal,low,high = self._evaluate(level)
        return THDConstraint(float(level),float(nominal),_round_float(low,True),_round_float(high,False))

    def compare_aggregate_thd(self, candidate_thd_percent, input_level_axis_dbm, **conditions):
        """Compare with reading scenarios, not acceptance limits for real parts."""
        candidate = _number(candidate_thd_percent,'candidate_thd_percent')
        if candidate < 0:
            raise ValueError('Aggregate THD percent cannot be negative')
        self.thd_constraint(input_level_axis_dbm,**conditions)
        _,low,high = self._evaluate(Fraction(input_level_axis_dbm))
        return ('below_declared_reading_scenarios' if candidate < low else
                'above_declared_reading_scenarios' if candidate > high else
                'within_declared_reading_scenarios')
