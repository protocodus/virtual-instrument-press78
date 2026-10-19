"""Panasonic MN3206 settled-DC graph interpolator, research only.

Primary source: MN3206 printed p77, upper-left VO–VI graph, bound in
design-frozen-v3.json. Conditions are only VDD=5 V, VGG=14/15 VDD,
CP=10 kHz, Ta=25°C, relative to VSS=0 V. This is the graph's output,
not an identified target-keyboard pin/load or an instantaneous audio law.

The interpolation and pixel-shift scenarios are declared approximations to
reading the printed graph. They are not part tolerances or confidence bounds.
There is no time, audio, excitation, noise, supply scaling or Drive interface.
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


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f'{name} must be an explicit finite real number')
    try:
        finite = math.isfinite(value)
    except OverflowError as error:
        raise ValueError(f'{name} exceeds the numeric port domain') from error
    if not finite:
        raise ValueError(f'{name} must be finite')
    return Fraction(value)


def _outward_float(value, lower):
    result = float(value)
    if (lower and Fraction(result) > value) or (not lower and Fraction(result) < value):
        result = math.nextafter(result, -math.inf if lower else math.inf)
    return result


@dataclass(frozen=True)
class DCOperatingPoint:
    input_v: float
    nominal_output_v: float
    graph_scenario_low_v: float
    graph_scenario_high_v: float


class MN3206DC:
    """Stateless settled-DC lookup with explicit voltage/condition ports.

    Every query must supply all fixed graph conditions. The supported input
    interval is the common support of the frozen coordinate-reading scenarios.
    It is deliberately smaller than the graph's nominal digitized support.
    """

    VGG_EXACT_V = Fraction(14, 3)
    VGG_BINARY64_ALIAS_V = float(VGG_EXACT_V)

    def __init__(self):
        here = Path(__file__).resolve().parent
        design_bytes = (here / 'design-frozen-v3.json').read_bytes()
        design = json.loads(design_bytes)
        data = json.loads((here / 'digitized-pixels.json').read_text())
        if data['design_sha256'] != hashlib.sha256(design_bytes).hexdigest():
            raise ValueError('Digitization is not bound to this frozen design')
        if data['source_sha256'] != design['sources']['page_raster']['sha256']:
            raise ValueError('Digitization source mismatch')
        self._x = tuple(Fraction(x) for x in data['pixel_x'])
        self._y = tuple(Fraction(y) for y in data['pixel_y'])
        if (tuple(data['pixel_x']) != tuple(design['extraction']['pixel_x_knots'])
                or len(self._x) != len(self._y) or len(self._x) < 2
                or any(b <= a for a, b in zip(self._x, self._x[1:]))):
            raise ValueError('Invalid frozen pixel knots')
        axes = design['axes']
        self._x0 = Fraction(axes['x_zero_px'])
        self._x6 = Fraction(axes['x_six_volts_px'])
        self._y0 = Fraction(axes['y_zero_px'])
        self._y6 = Fraction(axes['y_six_volts_px'])
        axis_radius = Fraction(axes['axis_reading_radius_px'])
        trace_radius = Fraction(design['extraction']['centerline_reading_radius_px'])
        signs = (-1, 1)
        self._xs = tuple((self._x0 + a * axis_radius,
                          self._x6 + b * axis_radius, c * trace_radius)
                         for a, b, c in product(signs, repeat=3))
        self._ys = tuple((self._y0 + a * axis_radius,
                          self._y6 + b * axis_radius, c * trace_radius)
                         for a, b, c in product(signs, repeat=3))
        self.nominal_input_range_exact_v = (
            6 * (self._x[0] - self._x0) / (self._x6 - self._x0),
            6 * (self._x[-1] - self._x0) / (self._x6 - self._x0),
        )
        self.input_range_exact_v = (
            max(6 * (self._x[0] - dx - x0) / (x6 - x0) for x0, x6, dx in self._xs),
            min(6 * (self._x[-1] - dx - x0) / (x6 - x0) for x0, x6, dx in self._xs),
        )
        # These are inward-rounded public binary64 endpoints, not an empirical
        # epsilon. All subsequent support arithmetic uses exact rationals.
        low, high = self.input_range_exact_v
        self.input_range_v = (_outward_float(low, False), _outward_float(high, True))
        self.conditions = tuple(design['ports']['conditions'].items())

    def _pixel_output(self, x):
        if x < self._x[0] or x > self._x[-1]:
            raise ValueError('Query would extrapolate beyond measured curve pixels')
        i = min(len(self._x) - 2, max(0, bisect_right(self._x, x) - 1))
        weight = (x - self._x[i]) / (self._x[i + 1] - self._x[i])
        return self._y[i] + weight * (self._y[i + 1] - self._y[i])

    def operating_point(self, input_v, *, mode, vdd_v, vgg_v, cp_hz,
                        temperature_c, vss_v):
        if mode != 'settled_dc_only':
            raise ValueError('Only the fixed-condition settled_dc_only graph is supported')
        actual = dict(vdd_v=vdd_v, vgg_v=vgg_v, cp_hz=cp_hz,
                      temperature_c=temperature_c, vss_v=vss_v)
        for name, expected in self.conditions:
            value = _number(actual[name], name)
            # The graph specifies exactly (14/15)*5 = 14/3 V. Accept that
            # rational and its one nearest binary64 representation. Comparing
            # exact values preserves this representation alias without adding
            # a physical tolerance or rounding arbitrary nearby rationals.
            accepted = ((self.VGG_EXACT_V, Fraction(self.VGG_BINARY64_ALIAS_V))
                        if name == 'vgg_v' else (Fraction(expected),))
            if value not in accepted:
                raise ValueError(f'Unsupported graph condition: {name}')
        voltage = _number(input_v, 'input_v')
        low, high = self.input_range_exact_v
        if not low <= voltage <= high:
            raise ValueError('Input voltage is outside the common measured graph support')
        x = self._x0 + voltage / 6 * (self._x6 - self._x0)
        y = self._pixel_output(x)
        nominal = 6 * (self._y0 - y) / (self._y0 - self._y6)
        values = []
        for x0, x6, dx in self._xs:
            yp = self._pixel_output(x0 + voltage / 6 * (x6 - x0) + dx)
            for y0, y6, dy in self._ys:
                values.append(6 * (y0 - yp - dy) / (y0 - y6))
        return DCOperatingPoint(
            input_v=float(voltage), nominal_output_v=float(nominal),
            graph_scenario_low_v=_outward_float(min(values), True),
            graph_scenario_high_v=_outward_float(max(values), False),
        )
