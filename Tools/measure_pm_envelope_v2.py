#!/usr/bin/env python3
"""Conservative, control-first PM-envelope sets for an explicitly finite family.

This research tool does not change the instrument or add noise. It preserves the
failed v1 experiment. The empirical multi-window disks are NOT certified error
bounds or confidence intervals. Even surviving cells need not contain an exact
common-parameter trajectory: dependencies are deliberately widened.

First bind the frozen design and implementation, then run into a fresh ignored
directory. Existing local v1 native controls are required; no native rebuild,
downloads or original hardware are used. Source PCM is decoded only with
--source and after EVERY frozen numerical gate passes.
"""
from __future__ import annotations

import argparse
import bisect
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import sys
import time
import warnings

import numpy as np
from scipy.io import wavfile
from scipy.special import jv
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
RATE = 44100
EPS = np.finfo(float).eps
PAIRS = [(j, h) for j in range(6) for h in range(j + 1, 6)]
ORDER = [16, 17, 33, 8, 24, 4, 12, 20, 28] + [
    i for i in range(1, 34) if i not in [16, 17, 33, 8, 24, 4, 12, 20, 28]]
CENTERS = np.r_[np.linspace(.15, .55, 17), np.linspace(.65, 1.05, 17)]
threadpool_limits(1)
warnings.filterwarnings('ignore', category=RuntimeWarning)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [clean(v) for v in value]
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, complex):
        return [value.real, value.imag]
    if isinstance(value, float) and not math.isfinite(value):
        return '-infinity' if value < 0 else 'infinity' if value > 0 else None
    return value


def write(path, value):
    path = Path(path)
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(clean(value), indent=2, allow_nan=False) + '\n')


def artifact(path):
    p = Path(path)
    return {'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size,
            'sha256': sha(p)}


def check_artifact(row):
    path = ROOT / row['path']
    if path.stat().st_size != row['bytes'] or sha(path) != row['sha256']:
        raise ValueError('Changed bound artifact: ' + str(path))


def fresh_build(path, directory=True):
    path = path.resolve()
    path.relative_to((ROOT / 'build').resolve())
    if path == (ROOT / 'build').resolve() or path.exists():
        raise FileExistsError('A fresh ignored build path is required')
    if directory:
        path.mkdir(parents=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
    return path


def old_module():
    name = 'press78_pm_v1_frozen'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            name, ROOT / 'Tools/measure_pm_envelope.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


# These float intervals are padded conventions, not formally certified scipy
# special-function enclosures. Independent high-precision tests are mandatory.
def outward(lo, hi):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    scale = np.maximum(1., np.maximum(np.abs(lo), np.abs(hi)))
    margin = np.where(np.isfinite(scale), 64 * EPS * scale, 0.)
    return np.nextafter(lo - margin, -np.inf), np.nextafter(hi + margin, np.inf)


def add(a, b):
    lo, hi = a[0] + b[0], a[1] + b[1]
    return outward(np.where(np.isnan(lo), -np.inf, lo),
                   np.where(np.isnan(hi), np.inf, hi))


def sub(a, b):
    return add(a, (-b[1], -b[0]))


def mul(a, b):
    vals = np.array([a[0] * b[0], a[0] * b[1],
                     a[1] * b[0], a[1] * b[1]])
    # Extended-real interval endpoints: the zero factor contributes exactly0
    # even when the other endpoint is infinite. No NaN may narrow an interval.
    vals = np.where(np.isnan(vals), 0., vals)
    return outward(np.min(vals, axis=0), np.max(vals, axis=0))


def scale(a, factor):
    return outward(a[0] * factor, a[1] * factor) if factor >= 0 else (
        outward(a[1] * factor, a[0] * factor))


def square(a):
    lo = np.minimum(a[0] ** 2, a[1] ** 2)
    lo = np.where((a[0] <= 0) & (a[1] >= 0), 0., lo)
    hi = np.maximum(a[0] ** 2, a[1] ** 2)
    lo, hi = outward(lo, hi)
    return np.maximum(lo, 0.), hi


def log_amplitude(lo, hi):
    """20log10 amplitude interval; zeros remain minus infinity."""
    low = np.where(np.asarray(lo) > 0, 20 * np.log10(lo), -np.inf)
    high = np.where(np.asarray(hi) > 0, 20 * np.log10(hi), -np.inf)
    return outward(low, high)


def log_power(lo, hi):
    low = np.where(np.asarray(lo) > 0, 10 * np.log10(lo), -np.inf)
    high = np.where(np.asarray(hi) > 0, 10 * np.log10(hi), -np.inf)
    return outward(low, high)


def wrap(angle):
    return np.angle(np.exp(1j * angle))


def rectangle_phase(real, imag):
    """Circular hull center/radius; rectangles touching origin give full circle."""
    rc, ic = (real[0] + real[1]) / 2, (imag[0] + imag[1]) / 2
    center = np.arctan2(ic, rc)
    angles = np.array([np.arctan2(y, x) for x in real for y in imag])
    radius = np.max(np.abs(wrap(angles - center)), axis=0)
    origin = ((real[0] <= 0) & (real[1] >= 0) &
              (imag[0] <= 0) & (imag[1] >= 0))
    return center, np.where(origin, np.pi, np.minimum(np.pi, radius + 64 * EPS))


def disk_phase(z, radius):
    magnitude = np.abs(z)
    angle_radius = np.where(radius >= magnitude, np.pi,
                            np.arcsin(np.minimum(1., radius / magnitude)))
    return np.angle(z), np.minimum(np.pi, angle_radius + 64 * EPS)


@dataclass
class Projector:
    matrix: np.ndarray
    design: np.ndarray
    weight: np.ndarray
    complex_rows: np.ndarray
    condition: float
    rank: int

    def measure(self, samples):
        c = self.matrix @ samples
        z = self.complex_rows @ samples
        residual = samples - self.design @ c
        mean = np.sum(self.weight * samples) / np.sum(self.weight)
        denom = np.sum(self.weight * (samples - mean) ** 2)
        q = np.sum(np.abs(self.complex_rows), axis=1) / (2 * 32768)
        return {'z': z, 'quant_bound': q,
                'residual_fraction': float(np.sum(self.weight * residual ** 2) /
                                           max(denom, 1e-100)),
                'condition': self.condition, 'rank': self.rank,
                'columns': self.design.shape[1]}


PROJECTORS = {}


def projector(n, frequency, degree):
    key = (n, float(frequency), degree)
    if key not in PROJECTORS:
        # Every fit evaluates its constant term at the SAME integer center frame;
        # this matters for the even-length 35ms nested support.
        t = (np.arange(n) - n // 2) / RATE
        u = t / (n / RATE)
        columns = [np.ones(n), u]
        indices = []
        for h in range(1, 11):
            cosine, sine = np.cos(2 * np.pi * h * frequency * t), np.sin(
                2 * np.pi * h * frequency * t)
            indices.append(len(columns))
            for k in range(degree + 1):
                columns.extend([u ** k * cosine, u ** k * sine])
        design = np.array(columns).T
        weight = np.hanning(n)
        u_svd, singular, vh = np.linalg.svd(
            design * np.sqrt(weight[:, None]), full_matrices=False)
        condition = float(singular[0] / singular[-1])
        rank = int(np.sum(singular > singular[0] * 1e-12))
        inverse = (vh.T / singular) @ (u_svd.T * np.sqrt(weight))
        rows = np.array([(inverse[i] - 1j * inverse[i + 1]) / 2 for i in indices])
        PROJECTORS[key] = Projector(inverse, design, weight, rows, condition, rank)
    return PROJECTORS[key]


def extract(signal, frequency, entry=.3, eligible=(True, True)):
    quiet_start, quiet_end = round((entry - .15) * RATE), round((entry - .05) * RATE)
    if quiet_start < 0 or quiet_end > len(signal):
        return {'anchor_valid': False, 'reason': 'fixed quiet reference unavailable', 'cells': []}
    quiet = projector(quiet_end - quiet_start, frequency, 2).measure(signal[quiet_start:quiet_end])
    allowance = np.abs(quiet['z']) + quiet['quant_bound']
    cells = []
    for i, local in enumerate(CENTERS):
        if not eligible[i // 17]:
            cells.append({'valid': False, 'reason': 'retained metadata-ineligible interval',
                          'local': float(local)})
            continue
        center = round((entry + local) * RATE)
        fitted, frames = [], []
        for seconds, degree in [(.05, 2), (.05, 1), (.035, 1)]:
            n = round(seconds * RATE)
            start, end = center - n // 2, center - n // 2 + n
            if start < 0 or end > len(signal):
                break
            fitted.append(projector(n, frequency, degree).measure(signal[start:end]))
            frames.append([start, end])
        if len(fitted) != 3:
            cells.append({'valid': False, 'reason': 'fixed outer/nested support unavailable',
                          'local': float(local)})
            continue
        main, outer, nested = fitted
        z = main['z'][:6]
        disagreement = np.maximum(np.abs(z - outer['z'][:6]), np.abs(z - nested['z'][:6]))
        radius = 2 * disagreement + main['quant_bound'][:6] + allowance[:6]
        lo, hi = np.maximum(np.abs(z) - radius, 0.), np.abs(z) + radius
        pcenter, pradius = disk_phase(z, radius)
        samples = signal[frames[0][0]:frames[0][1]]
        h1_fraction = float(abs(main['z'][0]) ** 2 / max(np.sum(np.abs(main['z']) ** 2), 1e-100))
        conditions = [x['rank'] == x['columns'] and x['condition'] <= 1e8 for x in fitted]
        valid = (all(conditions) and np.all(np.isfinite(samples)) and
                 float(np.max(np.abs(samples))) < .98 and
                 main['residual_fraction'] <= .1 and h1_fraction >= .005 and lo[0] > 0)
        reason = None if valid else ('H1 disk includes zero' if lo[0] == 0 else
                  'conditioning, residual, H1 fraction, peak or finite-data gate')
        cells.append({'local': float(local), 'center_frame': center, 'source_frames': frames,
                      'valid': bool(valid), 'reason': reason,
                      'complex_harmonics': z, 'radius': radius,
                      'amplitude_lo': lo, 'amplitude_hi': hi,
                      'phase_center': pcenter, 'phase_radius': pradius,
                      'fit_disagreement': disagreement,
                      'PCM16_bound': main['quant_bound'][:6],
                      'quiet_allowance': allowance[:6], 'fit_condition': [x['condition'] for x in fitted],
                      'weighted_residual_fraction': main['residual_fraction'],
                      'H1_power_fraction': h1_fraction, 'peak': float(np.max(np.abs(samples)))})
    return {'anchor_valid': bool(cells and cells[0]['valid']), 'cells': cells,
            'reason': None if cells and cells[0]['valid'] else 'unchanged first-body anchor not usable',
            'quiet_frames': [quiet_start, quiet_end], 'quiet_allowance': allowance[:6]}


GRID = {}


def grid_geometry(denser=False):
    if denser not in GRID:
        beta = np.geomspace(.001, 8., 4801 if denser else 2401)
        middle = np.sqrt(beta[:-1] * beta[1:])
        blo, bhi = np.r_[beta[0], middle], np.r_[middle, beta[-1]]
        delta = np.linspace(0., np.pi / 2, 65 if denser else 33)
        dm = (delta[:-1] + delta[1:]) / 2
        dlo, dhi = np.r_[delta[0], dm], np.r_[dm, delta[-1]]
        GRID[denser] = beta, blo, bhi, delta, dlo, dhi
    return GRID[denser]


def grid_model(delta_index, denser=False):
    beta, blo, bhi, delta, dlo, dhi = grid_geometry(denser)
    extent = np.maximum(beta - blo, bhi - beta)[:, None]
    orders = np.arange(8)
    centers = jv(orders[None, :], beta[:, None])
    derivative = (jv(orders[None, :] - 1, beta[:, None]) -
                  jv(orders[None, :] + 1, beta[:, None])) / 2
    error = abs(derivative) * extent + .5 * extent ** 2
    jlo, jhi = outward(centers - error, centers + error)
    m, p = (jlo[:, :6], jhi[:, :6]), (jlo[:, 2:8], jhi[:, 2:8])
    dl, dh = float(dlo[delta_index]), float(dhi[delta_index])
    sin_delta = outward(math.sin(dl), math.sin(dh))
    cos_delta = outward(math.cos(dh), math.cos(dl))
    cos_twice = outward(math.cos(2 * dh), math.cos(2 * dl))
    sign = (-1.) ** (np.arange(1, 7) + 1)
    sp = (np.minimum(p[0] * sign, p[1] * sign), np.maximum(p[0] * sign, p[1] * sign))
    real = scale(mul(sin_delta, add(m, sp)), .5)
    imag = scale(mul(cos_delta, sub(m, sp)), -.5)
    cross = mul(mul(m, p), cos_twice)
    cross = (np.minimum(-2 * sign * cross[0], -2 * sign * cross[1]),
             np.maximum(-2 * sign * cross[0], -2 * sign * cross[1]))
    mag = scale(add(add(square(m), square(p)), cross), .25)
    rectangle_mag = add(square(real), square(imag))
    low = np.maximum(0., np.maximum(mag[0], rectangle_mag[0]))
    high = np.minimum(mag[1], rectangle_mag[1])
    if np.any(low > high):
        raise ArithmeticError('Empty intersected coefficient enclosure')
    phase_center, phase_radius = rectangle_phase(real, imag)
    logs = log_power(low, high)
    pair_lo, pair_hi, pair_pc, pair_pr = [], [], [], []
    for j, h in PAIRS:
        lo, hi = sub((logs[0][:, h], logs[1][:, h]), (logs[0][:, j], logs[1][:, j]))
        pair_lo.append(lo); pair_hi.append(hi)
        pair_pc.append((j + 1) * phase_center[:, h] - (h + 1) * phase_center[:, j])
        pair_pr.append(np.minimum(np.pi, (j + 1) * phase_radius[:, h] +
                                  (h + 1) * phase_radius[:, j]))
    return {'beta': beta, 'beta_lo': blo, 'beta_hi': bhi,
            'delta': float(delta[delta_index]), 'delta_lo': dl, 'delta_hi': dh,
            'absB_squared_lo': low, 'absB_squared_hi': high,
            'phase_center': phase_center, 'phase_radius': phase_radius,
            'pair_db_lo': np.array(pair_lo).T, 'pair_db_hi': np.array(pair_hi).T,
            'pair_phase_center': np.array(pair_pc).T, 'pair_phase_radius': np.array(pair_pr).T,
            'B1_db_lo': logs[0][:, 0], 'B1_db_hi': logs[1][:, 0]}


class IntervalIndex:
    """Exact interval-overlap queries using sorted endpoint prefix bitsets."""
    def __init__(self, low, high):
        lower_order, upper_order = np.argsort(low, kind='stable'), np.argsort(high, kind='stable')
        self.lower = low[lower_order]
        self.upper = high[upper_order]
        self.low_prefix, self.high_prefix = [0], [0]
        for index in lower_order:
            self.low_prefix.append(self.low_prefix[-1] | (1 << int(index)))
        for index in upper_order:
            self.high_prefix.append(self.high_prefix[-1] | (1 << int(index)))

    def query(self, low, high):
        if np.isnan(low) or np.isnan(high):
            raise ArithmeticError('NaN interval query')
        # Closed overlap: candidate.lower <= query.upper and
        # candidate.upper >= query.lower, including infinite endpoints.
        il = bisect.bisect_right(self.lower, high)
        ih = bisect.bisect_left(self.upper, low)
        return self.low_prefix[il] & ~self.high_prefix[ih]


MODEL_CACHE = {}


def indexed_model(di, denser=False):
    key = (di, denser)
    if key not in MODEL_CACHE:
        model = grid_model(di, denser)
        model['B1_db_global_low'] = float(np.min(model['B1_db_lo']))
        model['B1_db_global_high'] = float(np.max(model['B1_db_hi']))
        model['indices'] = [IntervalIndex(model['pair_db_lo'][:, k], model['pair_db_hi'][:, k])
                            for k in range(len(PAIRS))]
        # Cache the modest coarse domain, but not65 large dense prefix sets.
        if not denser:
            MODEL_CACHE[key] = model
        return model
    return MODEL_CACHE[key]


def bit_indices(mask):
    out = []
    while mask:
        bit = mask & -mask
        out.append(bit.bit_length() - 1)
        mask ^= bit
    return np.array(out, dtype=int)


def observations(measured):
    if not measured['anchor_valid']:
        return []
    anchor = measured['cells'][0]
    anchor_logs = log_amplitude(anchor['amplitude_lo'], anchor['amplitude_hi'])
    result = []
    for ti, cell in enumerate(measured['cells']):
        if not cell['valid']:
            result.append(None)
            continue
        logs = log_amplitude(cell['amplitude_lo'], cell['amplitude_hi'])
        qlo, qhi, pc, pr = [], [], [], []
        for j, h in PAIRS:
            current = sub((logs[0][h], logs[1][h]), (logs[0][j], logs[1][j]))
            old = sub((anchor_logs[0][h], anchor_logs[1][h]),
                      (anchor_logs[0][j], anchor_logs[1][j]))
            dl, dh = sub(current, old)
            qlo.append(float(dl)); qhi.append(float(dh))
            pc.append((j + 1) * (cell['phase_center'][h] - anchor['phase_center'][h]) -
                      (h + 1) * (cell['phase_center'][j] - anchor['phase_center'][j]))
            pr.append(min(np.pi, (j + 1) * (cell['phase_radius'][h] + anchor['phase_radius'][h]) +
                          (h + 1) * (cell['phase_radius'][j] + anchor['phase_radius'][j])))
        al, ah = sub((logs[0][0], logs[1][0]), (anchor_logs[0][0], anchor_logs[1][0]))
        result.append({'low': np.array(qlo), 'high': np.array(qhi),
                       'phase_center': np.array(pc), 'phase_radius': np.array(pr),
                       'A_obs_low': float(al), 'A_obs_high': float(ah),
                       'unconstrained': bool(np.all(np.isneginf(qlo)) and
                                             np.all(np.isposinf(qhi)) and np.all(np.asarray(pr) >= np.pi))})
    return result


def slope_range(low, high, indices):
    t = CENTERS[indices]
    weights = (t - t.mean()) / np.sum((t - t.mean()) ** 2)
    # No center has exactly0 weight for these17 evenly spaced epochs, apart
    # from the midpoint. Define0*infinity as0 for that irrelevant coordinate.
    lower = np.where(weights > 0, low[indices], high[indices])
    upper = np.where(weights > 0, high[indices], low[indices])
    l = np.sum(np.where(weights == 0, 0., weights * lower))
    h = np.sum(np.where(weights == 0, 0., weights * upper))
    return -float(h), -float(l)


def bound_record(low, high, status=None):
    finite = bool(np.isfinite(low) and np.isfinite(high))
    return {'status': status or ('finite_outer_set' if finite else 'unbounded_outer_set'),
            'low': low, 'high': high, 'finite': finite,
            'width': high - low if finite else np.inf}


def cell_ids(value, low, high):
    return np.flatnonzero((low <= value) & (high >= value))


def profile(measured, out, name, denser=False, truth=None):
    obs = observations(measured)
    if not obs:
        return {'status': 'unobserved_bad_anchor', 'reason': measured['reason'],
                'not_excluded_cells': 0, 'body': None, 'late': None,
                'true_branch_retained': None, 'endpoint_warning': False}
    beta, blo, bhi, delta, dlo, dhi = grid_geometry(denser)
    n = len(beta)
    beta_db_lo, beta_db_hi = 20 * np.log10(blo), 20 * np.log10(bhi)
    visible = np.array([o is not None for o in obs])
    point_a_lo, point_a_hi = np.full(34, np.inf), np.full(34, -np.inf)
    point_b_lo, point_b_hi = point_a_lo.copy(), point_a_hi.copy()
    records = []
    generating_branch = False
    truth_eligible = truth is not None and truth.get('beta') is not None and np.all(truth['beta'] > 0)
    actual_beta_ids = [cell_ids(v, blo, bhi) for v in truth['beta']] if truth_eligible else None
    true_anchor_ids = set(actual_beta_ids[0]) if truth_eligible else set()
    for di in range(len(delta)):
        model = indexed_model(di, denser)
        true_delta = bool(truth_eligible and dlo[di] <= truth['delta'] <= dhi[di])
        for sign in (1, -1):
            for ai in range(n):
                a_low, a_high = np.full(34, -np.inf), np.full(34, np.inf)
                b_low, b_high = a_low.copy(), a_high.copy()
                a_low[0] = a_high[0] = 0.
                b_low[0], b_high[0] = beta_db_lo[ai], beta_db_hi[ai]
                endpoint = ai in (0, n - 1)
                true_path = bool(true_delta and sign == 1 and ai in true_anchor_ids)
                alive = True
                for ti in ORDER:
                    row = obs[ti]
                    if row is None:
                        continue
                    if row['unconstrained']:
                        a_low[ti] = row['A_obs_low'] + model['B1_db_lo'][ai] - model['B1_db_global_high']
                        a_high[ti] = row['A_obs_high'] + model['B1_db_hi'][ai] - model['B1_db_global_low']
                        b_low[ti], b_high[ti] = beta_db_lo[0], beta_db_hi[-1]
                        endpoint = True
                        if true_path:
                            ids = actual_beta_ids[ti]
                            al = row['A_obs_low'] + model['B1_db_lo'][ai] - model['B1_db_hi'][ids]
                            ah = row['A_obs_high'] + model['B1_db_hi'][ai] - model['B1_db_lo'][ids]
                            true_path = bool(len(ids) and np.min(al) <= truth['A_relative_db'][ti] <= np.max(ah))
                        continue
                    mask = (1 << n) - 1
                    for k in range(len(PAIRS)):
                        target_low = float(model['pair_db_lo'][ai, k] + row['low'][k])
                        target_high = float(model['pair_db_hi'][ai, k] + row['high'][k])
                        if np.isnan(target_low): target_low = -np.inf
                        if np.isnan(target_high): target_high = np.inf
                        mask &= model['indices'][k].query(target_low, target_high)
                        if not mask:
                            break
                    if not mask:
                        alive = False
                        break
                    ids = bit_indices(mask)
                    for k in range(len(PAIRS)):
                        radii = np.minimum(np.pi, model['pair_phase_radius'][ids, k] +
                                           model['pair_phase_radius'][ai, k] + row['phase_radius'][k])
                        centers = sign * (model['pair_phase_center'][ids, k] -
                                          model['pair_phase_center'][ai, k]) - row['phase_center'][k]
                        ids = ids[np.abs(wrap(centers)) <= radii + 64 * EPS]
                        if not len(ids): break
                    if not len(ids):
                        alive = False
                        break
                    al = row['A_obs_low'] + model['B1_db_lo'][ai] - model['B1_db_hi'][ids]
                    ah = row['A_obs_high'] + model['B1_db_hi'][ai] - model['B1_db_lo'][ids]
                    al = np.where(np.isnan(al), -np.inf, al)
                    ah = np.where(np.isnan(ah), np.inf, ah)
                    a_low[ti], a_high[ti] = np.min(al), np.max(ah)
                    b_low[ti], b_high[ti] = np.min(beta_db_lo[ids]), np.max(beta_db_hi[ids])
                    endpoint |= bool(ids[0] == 0 or ids[-1] == n - 1)
                    if true_path:
                        chosen = np.isin(ids, actual_beta_ids[ti])
                        true_path = bool(np.any(chosen) and np.min(al[chosen]) <= truth['A_relative_db'][ti] <= np.max(ah[chosen]))
                if not alive:
                    continue
                generating_branch |= true_path
                point_a_lo = np.minimum(point_a_lo, a_low); point_a_hi = np.maximum(point_a_hi, a_high)
                point_b_lo = np.minimum(point_b_lo, b_low); point_b_hi = np.maximum(point_b_hi, b_high)
                ranges = []
                for ii in (np.arange(17), np.arange(17, 34)):
                    ranges.extend(slope_range(a_low, a_high, ii))
                    ranges.extend(slope_range(b_low, b_high, ii))
                records.append([delta[di], sign, ai, *ranges, float(endpoint), float(true_path)])
    branches = np.asarray(records, float).reshape((-1, 13))
    path = out / (name + '-cells.npz')
    if path.exists(): raise FileExistsError(path)
    np.savez_compressed(path, cells=branches, columns=np.array([
        'delta_center', 'conjugate_sign', 'beta_anchor_index', 'body_A_low', 'body_A_high',
        'body_beta_low', 'body_beta_high', 'late_A_low', 'late_A_high',
        'late_beta_low', 'late_beta_high', 'endpoint_warning', 'true_branch_retained']))
    result = {'status': 'not_excluded_outer_cells' if len(branches) else 'incompatible',
              'not_excluded_cells': len(branches), 'profile_artifact': artifact(path),
              'endpoint_warning': bool(len(branches) and np.any(branches[:, 11])),
              'true_branch_retained': bool(generating_branch) if truth_eligible else None,
              'observable_cells': visible,
              'pointwise_relative_A_db': np.column_stack([point_a_lo, point_a_hi]) if len(branches) else None,
              'pointwise_absolute_beta_db': np.column_stack([point_b_lo, point_b_hi]) if len(branches) else None,
              'anchor_beta_range': [float(np.min(blo[branches[:, 2].astype(int)])),
                                    float(np.max(bhi[branches[:, 2].astype(int)]))] if len(branches) else None}
    for kind, column in [('body', 3), ('late', 7)]:
        result[kind] = None if not len(branches) else {
            'A': bound_record(float(np.min(branches[:, column])), float(np.max(branches[:, column + 1]))),
            'beta': bound_record(float(np.min(branches[:, column + 2])), float(np.max(branches[:, column + 3])))}
    return result


def analytic_v2(case):
    elapsed = np.arange(2 * RATE) / RATE - .3
    tau = np.maximum(elapsed, 0) * (1 + case['clock_ppm'] * 1e-6)
    theta = 2 * np.pi * (case['frequency_hz'] * tau + case['initial_modulator_phase_cycles'])
    acoef, bcoef = case['carrier_attenuation_polynomial_db'], case['beta_attenuation_polynomial_db']
    poly = lambda coefficients: sum(c * tau ** (i + 1) for i, c in enumerate(coefficients))
    amplitude = case['initial_carrier_peak'] * 10 ** (-poly(acoef) / 20)
    beta = case['initial_beta'] * 10 ** (-poly(bcoef) / 20)
    y = amplitude * np.sin(theta + case['relative_phase'] + beta * np.sin(theta))
    y[elapsed < 0] = 0
    processing = case['processing']
    if processing == 'nearby_tone':
        extra = (case['interferer_relative_peak'] * amplitude *
                 np.sin(2 * np.pi * ((case['frequency_hz'] + case['interferer_frequency_offset_hz']) * tau +
                                    case['interferer_phase_cycles'])))
        y += np.where(elapsed >= 0, extra, 0)
    elif processing == 'independent_H2':
        extra = case['harmonic_relative_peak'] * amplitude * np.sin(
            2 * theta + case['phase_mod_depth_radians'] * np.sin(
                2 * np.pi * case['phase_mod_frequency_hz'] * tau))
        y += np.where(elapsed >= 0, extra, 0)
    elif processing == 'delayedcopy':
        frames = round(case['delay_seconds'] * RATE)
        y += np.r_[np.zeros(frames), case['wet_gain'] * y[:-frames]]
    elif processing == 'chorus':
        delay = (case['delay_seconds'] + case['depth_seconds'] *
                 np.sin(2 * np.pi * case['rate_hz'] * tau)) * RATE
        wet = np.interp(np.arange(len(y)) - delay, np.arange(len(y)), y, left=0., right=0.)
        y = case['dry_gain'] * y + case['wet_gain'] * wet
    elif processing == 'dynamic_gain':
        gain = sum(c * tau ** (i + 1) for i, c in enumerate(case['gain_polynomial_db']))
        y *= 10 ** (gain / 20)
    elif processing != 'none':
        raise ValueError('Undeclared prospective processor: ' + processing)
    return y, case['frequency_hz'] * (1 + case['clock_ppm'] * 1e-6)


def latent_truth(case, native=False):
    t = np.array([round((.3 + v) * RATE) / RATE - .3 for v in CENTERS])
    factor = 1 + case['clock_ppm'] * 1e-6
    if native:
        if case['profile'] != 'transparent': factor = 1.
        a = -2 * 2 ** (case['carrier_D2R'] / 4) * factor * t
        b = -2 * 2 ** (case['mod_D2R'] / 4) * factor * t
        beta = None
    else:
        tau = t * factor
        aa = case.get('carrier_attenuation_polynomial_db', [case.get('carrier_db_per_second'), 0., 0.])
        bb = case.get('beta_attenuation_polynomial_db', [case.get('beta_db_per_second'), 0., 0.])
        a = -sum(c * tau ** (i + 1) for i, c in enumerate(aa))
        b = -sum(c * tau ** (i + 1) for i, c in enumerate(bb))
        beta = case['initial_beta'] * 10 ** (b / 20)
        if case.get('processing') == 'dynamic_gain':
            a += sum(c * tau ** (i + 1) for i, c in enumerate(case['gain_polynomial_db']))
        elif case['id'] == 'dynamic-gain-nonidentifiability':
            a += 12 * t  # Preserve the exact old processor's host-time equation.
    result = {'A_relative_db': a - a[0], 'beta_absolute_db': b,
              'beta': beta, 'delta': case.get('relative_phase')}
    for kind, ii in [('body', np.arange(17)), ('late', np.arange(17, 34))]:
        weight = (CENTERS[ii] - CENTERS[ii].mean()) / np.sum((CENTERS[ii] - CENTERS[ii].mean()) ** 2)
        result[kind] = {'A': -float(np.sum(weight * a[ii])), 'beta': -float(np.sum(weight * b[ii]))}
    return result


def quantify(summary, truth):
    result = {}
    for kind in ('body', 'late'):
        result[kind] = {}
        for quantity, width in [('A', 3.), ('beta', 4.)]:
            bound = summary.get(kind, {}).get(quantity) if summary.get(kind) else None
            defined = quantity != 'beta' or truth.get('beta_defined', True)
            value = truth[kind][quantity] if defined else None
            covered = bool(defined and bound and bound['low'] <= value <= bound['high'])
            unknown = summary['status'] == 'unobserved_bad_anchor' or bool(bound and not bound['finite'])
            precise = bool(bound and bound['finite'] and bound['width'] <= width and
                           not summary['endpoint_warning'])
            result[kind][quantity] = {'truth_db_per_second': value, 'range': bound,
                                      'unexpanded_truth_coverage': covered if defined else None,
                                      'explicitly_unknown': unknown,
                                      'coverage_gate': covered or unknown,
                                      'informative': precise,
                                      'zero_decay_excluded': bool(bound and (bound['low'] > 0 or bound['high'] < 0))}
    return result


def point_coverage(summary, truth):
    if summary['status'] == 'unobserved_bad_anchor':
        return {'passed': True, 'status': 'not_testable_bad_anchor'}
    if summary['status'] == 'incompatible':
        return {'passed': False, 'status': 'empty_set_on_observed_data'}
    a = np.asarray(summary['pointwise_relative_A_db'])
    b = np.asarray(summary['pointwise_absolute_beta_db'])
    visible = np.asarray(summary['observable_cells'])
    good_a = (a[:, 0] <= truth['A_relative_db']) & (truth['A_relative_db'] <= a[:, 1])
    if truth['beta'] is not None and np.all(truth['beta'] > 0):
        beta_db = 20 * np.log10(truth['beta'])
        good_b = (b[:, 0] <= beta_db) & (beta_db <= b[:, 1])
        branch = bool(summary['true_branch_retained'])
    else:
        good_b = np.ones(34, bool)
        branch = True  # Native exact phase/beta-anchor is deliberately unknown.
    return {'passed': bool(np.all(good_a[visible]) and np.all(good_b[visible]) and branch),
            'visible_epoch_count': int(visible.sum()), 'A_covered': good_a,
            'beta_covered': good_b, 'generating_branch_retained': summary['true_branch_retained']}


def endpoint_change(a, b):
    if a == b: return 0.
    if not np.isfinite(a) or not np.isfinite(b): return np.inf
    return abs(a - b)


def compare_grids(coarse, dense, constant_beta=False):
    if constant_beta:
        def nonunique(s):
            v = s.get('anchor_beta_range')
            return bool(v and (v[1] / v[0] >= 4 or s['endpoint_warning']))
        return {'passed': nonunique(coarse) and nonunique(dense),
                'rule': 'Absolute beta remains nonunique on both grids'}
    checks = []
    for kind in ('body', 'late'):
        for q, tolerance in [('A', .5), ('beta', 1.)]:
            a, b = coarse.get(kind), dense.get(kind)
            change = np.inf if a is None or b is None else max(
                endpoint_change(a[q][edge], b[q][edge]) for edge in ('low', 'high'))
            checks.append({'interval': kind, 'quantity': q,
                           'endpoint_change': change, 'tolerance': tolerance,
                           'passed': change <= tolerance})
    return {'passed': all(v['passed'] for v in checks) and
                      coarse['endpoint_warning'] == dense['endpoint_warning'], 'checks': checks}


def math_check():
    """Fixed1020 cells x7 points x6 harmonics; never uses a source recording."""
    import mpmath as mp
    from scipy.special import jn_zeros, jnp_zeros
    mp.mp.dps = 80
    rng = np.random.default_rng(20261019)
    fractions = [(0., 0.), (1., 1.), (.5, .5), (.25, .75), (.75, .25), (0., 1.), (1., 0.)]
    misses, cells, points, max_phase_excess = [], 0, 0, -np.inf
    nulls = [1.8411837813406593]
    for order in range(8):
        nulls.extend(x for x in jn_zeros(order, 2) if x <= 8)
        nulls.extend(x for x in jnp_zeros(order, 2) if x <= 8)
    for denser in (False, True):
        beta, blo, bhi, delta, dlo, dhi = grid_geometry(denser)
        phase_ids = list(range(0, len(delta), 4 if denser else 2))
        anchors = list(dict.fromkeys([0, len(beta) - 1] + [int(np.argmin(abs(beta - v))) for v in nulls]))[:30]
        while len(anchors) < 30:
            candidate = int(rng.integers(0, len(beta)))
            if candidate not in anchors: anchors.append(candidate)
        for di in phase_ids:
            model = grid_model(di, denser)
            for bi in anchors:
                cells += 1
                for bf, df in fractions:
                    b = float(blo[bi] + bf * (bhi[bi] - blo[bi]))
                    d = float(dlo[di] + df * (dhi[di] - dlo[di]))
                    bm, dm = mp.mpf(b), mp.mpf(d)
                    js = [mp.besselj(n, bm) for n in range(8)]
                    for h in range(1, 7):
                        z = (mp.exp(1j * dm) * js[h - 1] - (-1) ** (h + 1) *
                             mp.exp(-1j * dm) * js[h + 1]) / (2j)
                        mag, angle = float(abs(z) ** 2), float(mp.arg(z))
                        excess = abs(float(wrap(angle - model['phase_center'][bi, h - 1]))) - model['phase_radius'][bi, h - 1]
                        max_phase_excess = max(max_phase_excess, excess)
                        points += 1
                        if not (model['absB_squared_lo'][bi, h - 1] <= mag <= model['absB_squared_hi'][bi, h - 1]) or excess > 64 * EPS:
                            misses.append({'denser': denser, 'beta_index': bi, 'delta_index': di,
                                           'fractions': [bf, df], 'harmonic': h, 'truth_squared': mag,
                                           'phase_excess': excess})
    primitive = []
    for a, b, target in [((0., 0.), (0., np.inf), 0.),
                          ((-1., 1.), (0., np.inf), 0.),
                          ((-2., -1.), (3., 4.), -6.)]:
        lo, hi = mul(a, b)
        primitive.append(bool(lo <= target <= hi))
    sl, sh = square((-1., 1.)); primitive.append(bool(sl <= 0 and sh >= 1))
    for real, imag in [((-2., -1.), (-1e-8, 1e-8)), ((-1., 1.), (-1., 1.)),
                       ((0., 1.), (0., 1.))]:
        pc, pr = rectangle_phase(real, imag)
        primitive.extend(abs(float(wrap(math.atan2(y, x) - pc))) <= pr + 64 * EPS
                         for x in np.linspace(*real, 7) for y in np.linspace(*imag, 7)
                         if x != 0 or y != 0)
    lows = np.r_[-np.inf, rng.normal(size=127)]
    highs = lows + abs(rng.normal(size=128))
    highs[0] = np.inf
    index = IntervalIndex(lows, highs)
    for lo, hi in [(-np.inf, np.inf), (-1., 1.), (0., 0.), (3., 4.)]:
        expected = set(np.flatnonzero((lows <= hi) & (highs >= lo)))
        primitive.append(set(bit_indices(index.query(lo, hi))) == expected)
    return {'schema': 'press78.pm-envelope-v2-math.v1', 'cells': cells,
            'sample_points_per_cell': 7, 'harmonics': 6, 'complex_truth_checks': points,
            'mpmath_decimal_digits': 80, 'misses': misses,
            'maximum_phase_excess': max_phase_excess,
            'primitive_checks': len(primitive), 'primitive_passed': all(primitive),
            'passed': cells >= 1000 and not misses and all(primitive),
            'scope': 'Numerical checks of declared finite-cell enclosure; not a formal special-function proof.'}


def load_design(path):
    design = json.loads(path.read_text())
    if design['schema'] != 'press78.pm-envelope-v2-design.v1' or 'FROZEN' not in design['status']:
        raise ValueError('The exact reviewed frozen v2 design is required')
    old_path = ROOT / design['old_protocol']['path']
    if sha(old_path) != design['old_protocol']['sha256']:
        raise ValueError('Old protocol binding changed')
    old_design = json.loads(old_path.read_text())
    if design['external_prediction'] != old_design['external_prediction']:
        raise ValueError('The physical prediction was changed')
    if design['preserved_source_selection']['windows'] != old_design['windows']:
        raise ValueError('Source support changed')
    return design


def binding_inputs(design):
    result_path = ROOT / 'build/pm-envelope-controls-20261019/result.json'
    old_result = json.loads(result_path.read_text())
    if old_result['gates']['all'] or old_result['source_inference_attempted']:
        raise ValueError('The old failed experiment must remain intact')
    old_design = json.loads((ROOT / design['old_protocol']['path']).read_text())
    files = [Path(__file__), ROOT / 'Tools/measure_pm_envelope.py', result_path]
    for tool, row in old_design['implementation'].items():
        if sha(ROOT / tool) != row['sha256']:
            raise ValueError('Changed v1 tool: ' + tool)
    for row in old_result['controls']:
        if row['case']['kind'] != 'analytic':
            name = row['case']['id']
            files += [result_path.parent / (name + '.wav'), result_path.parent / (name + '-render.json')]
    return files, old_result


def bind(design_path, out):
    design = load_design(design_path)
    files, old_result = binding_inputs(design)
    import scipy
    import mpmath
    binding = {'schema': 'press78.pm-envelope-v2-execution-binding.v1',
               'frozen_design': artifact(design_path),
               'artifacts': [artifact(p) for p in files],
               'source_PCM_decoded': False, 'new_numeric_evaluation_started': False,
               'old_cases': len(old_result['controls']),
               'new_cases': len(design['controls']['prospective_clean_cases']) +
                            len(design['controls']['prospective_null_confusion_cases']),
               'dependencies': {'python': sys.version, 'numpy': np.__version__,
                                'scipy': scipy.__version__, 'mpmath': mpmath.__version__,
                                'platform': platform.platform()},
               'purpose': 'Exact reviewed design/code/old-media binding before any v2 numerical evaluation.'}
    output = fresh_build(out, directory=False)
    write(output, binding)
    print(json.dumps(artifact(output)), flush=True)


def load_binding(path, design_path):
    binding = json.loads(path.read_text())
    if binding['schema'] != 'press78.pm-envelope-v2-execution-binding.v1':
        raise ValueError('Exact execution binding required')
    if binding['frozen_design'] != artifact(design_path):
        raise ValueError('Design is not the bound design')
    for row in binding['artifacts']:
        check_artifact(row)
    return binding


def quantize(y):
    return np.clip(np.rint(y * 32768), -32768, 32767) / 32768


def replay_old(old_result):
    old = old_module()
    replay = []
    for row in old_result['controls']:
        case = row['case']
        if case['kind'] == 'analytic':
            signal, frequency, _, _ = old.analytic_signal(case)
        else:
            path = ROOT / 'build/pm-envelope-controls-20261019' / (case['id'] + '.wav')
            sr, raw = wavfile.read(path)
            if sr != RATE or raw.shape != (2 * RATE, 2) or not np.all(np.isfinite(raw)):
                raise ValueError('Reused native control format')
            signal = raw[:, 0].astype(float) if case.get('channel') == 'left' else raw.astype(float).mean(axis=1)
            frequency = row['fixed_frequency_hz']
        q = quantize(signal)
        actual = hashlib.sha256(np.asarray(q, dtype='<f8').tobytes()).hexdigest()
        if actual != row['quantized_waveform_float64_sha256']:
            raise ValueError('Old waveform replay changed: ' + case['id'])
        replay.append((case, q, frequency, latent_truth(case, case['kind'] != 'analytic')))
    return replay


def precision(summary, kind, quantity):
    value = summary.get(kind, {}).get(quantity) if summary.get(kind) else None
    threshold = 3. if quantity == 'A' else 4.
    return bool(value and value['finite'] and value['width'] <= threshold and
                not summary['endpoint_warning'])


def null_check(rows):
    by_id = {x['case']['id']: x for x in rows}
    checks = []
    for name in ('sine-no-beta', 'new-null-pure-sine'):
        summary = by_id[name]['summary']
        passed = not any(precision(summary, kind, 'beta') for kind in ('body', 'late'))
        checks.append({'id': name, 'criterion': 'No beta precision from an undefined pure-sine beta', 'passed': passed})
    for name in ('constant-beta', 'new-null-constant-beta'):
        row, summary = by_id[name], by_id[name]['summary']
        span = summary.get('anchor_beta_range')
        nonunique = bool(span and (span[1] / span[0] >= 4 or summary['endpoint_warning']))
        zero_covered = all(row['qualification'][kind]['beta']['coverage_gate'] for kind in ('body', 'late'))
        checks.append({'id': name, 'criterion': 'Nonunique absolute beta; true zero relative slope covered',
                       'passed': nonunique and zero_covered})
    for name in ('H1-null', 'new-null-anchor-H1'):
        summary = by_id[name]['summary']
        passed = summary['status'] == 'unobserved_bad_anchor' or not any(
            precision(summary, kind, q) for kind in ('body', 'late') for q in ('A', 'beta'))
        checks.append({'id': name, 'criterion': 'No substituted anchor or spurious null precision', 'passed': passed})
    return {'checks': checks, 'passed': all(x['passed'] for x in checks)}


def source_measurements(design, out):
    selected = design['preserved_source_selection']
    for name, row in selected['sources'].items():
        path = ROOT / name
        if path.stat().st_size != row['bytes'] or sha(path) != row['sha256']:
            raise ValueError('Changed source/provenance binding: ' + name)
    path = ROOT / 'build/isolated-source-search-20261019/synth_bass_1.wav'
    rate, raw = wavfile.read(path)
    if rate != RATE or raw.dtype != np.int16 or raw.ndim != 1:
        raise ValueError('Frozen source PCM format')
    signal = raw.astype(float) / 32768
    result = []
    for note in selected['prior_note_frequencies']:
        index = note['segment_index']
        windows = {w['kind']: w for w in selected['windows'] if w['segment_index'] == index}
        entry = windows['body']['audio_active_entry_seconds']
        eligible = tuple(windows[k]['metadata_eligible'] for k in ('body', 'late'))
        measured = extract(signal, note['phase_frequency_hz'], entry, eligible)
        write(out / f'source-{index:02d}-measurements.json', measured)
        summary = profile(measured, out, f'source-{index:02d}')
        intervals = []
        for kind in ('body', 'late'):
            intervals.append({'kind': kind, 'metadata': windows[kind],
                              'A': summary.get(kind, {}).get('A') if summary.get(kind) else None,
                              'beta': summary.get(kind, {}).get('beta') if summary.get(kind) else None,
                              'A_informative': precision(summary, kind, 'A'),
                              'beta_informative': precision(summary, kind, 'beta'),
                              'status': summary['status']})
        result.append({'segment_index': index,
                       'inferred_musical_midi': note['expected_musical_midi_under_authored_sequence'],
                       'fixed_frequency_hz': note['phase_frequency_hz'], 'intervals': intervals,
                       'summary': summary,
                       'interpretation': 'Conditional captured A and beta outer sets; effects/capture and MIDI gate unknown; no intrinsic operator-rate claim.'})
        print('SOURCE', index, summary['status'], flush=True)
    return result


def run(design_path, binding_path, output, allow_source=False):
    design = load_design(design_path)
    binding = load_binding(binding_path, design_path)
    out = fresh_build(output)
    started = time.monotonic()
    write(out / 'run-started.json', {'design': artifact(design_path), 'binding': artifact(binding_path),
                                    'source_requested': allow_source, 'source_PCM_decoded': False})
    _, old_result = binding_inputs(design)
    old_cases = replay_old(old_result)  # All56 identity checks precede ANY v2 extraction.
    write(out / 'old-waveform-replay.json', {'count': len(old_cases), 'all_hashes_identical': True,
                                            'original_result': artifact(ROOT / 'build/pm-envelope-controls-20261019/result.json')})
    math_result = math_check()
    write(out / 'mathematical-checks.json', math_result)
    print('MATH', math_result['passed'], math_result['complex_truth_checks'], flush=True)
    new_cases = []
    for case in design['controls']['prospective_clean_cases'] + design['controls']['prospective_null_confusion_cases']:
        signal, frequency = analytic_v2(case)
        truth = latent_truth(case)
        truth['beta_defined'] = case['initial_beta'] > 0
        new_cases.append((case, quantize(signal), frequency, truth))
    rows, measured_by_id, truth_by_id = [], {}, {}
    old_ids = {c['id'] for c in design['controls']['reused_cases']}
    clean_ids = {c['id'] for c in design['controls']['reused_cases'] if c['classification'] == 'recovery'} | {
        c['id'] for c in design['controls']['prospective_clean_cases']}
    informative_ids = {c['id'] for c in design['controls']['prospective_clean_cases'] if c['id'].startswith('new-informative-')}
    for case, signal, frequency, truth in old_cases + new_cases:
        name = case['id']
        if case.get('initial_beta') == 0: truth['beta_defined'] = False
        measured = extract(signal, frequency)
        write(out / (name + '-measurements.json'), measured)
        summary = profile(measured, out, name, truth=truth)
        qualification = quantify(summary, truth)
        pc = point_coverage(summary, truth)
        row = {'case': case, 'role': 'reused development/regression' if name in old_ids else 'prospective',
               'is_clean_coverage_case': name in clean_ids,
               'fixed_frequency_hz': frequency,
               'quantized_float64_sha256': hashlib.sha256(np.asarray(signal, dtype='<f8').tobytes()).hexdigest(),
               'summary': summary, 'qualification': qualification, 'point_coverage': pc,
               'carrier_interpretation': 'captured amplitude including any external gain; not intrinsic hardware A'}
        write(out / (name + '-result.json'), row)
        rows.append(row); measured_by_id[name] = measured; truth_by_id[name] = truth
        print('CONTROL', name, summary['status'], summary['not_excluded_cells'],
              'coverage', all(qualification[k][q]['coverage_gate'] for k in ('body', 'late') for q in ('A', 'beta')),
              'truebranch', summary['true_branch_retained'], flush=True)
    grids = []
    selected = sorted(informative_ids) + ['analytic-00', 'analytic-11', 'analytic-24', 'constant-beta']
    for name in selected:
        coarse = next(x['summary'] for x in rows if x['case']['id'] == name)
        dense = profile(measured_by_id[name], out, name + '-denser', True, truth_by_id[name])
        comparison = compare_grids(coarse, dense, name == 'constant-beta')
        dq = quantify(dense, truth_by_id[name]); dp = point_coverage(dense, truth_by_id[name])
        coverage = (all(dq[k][q]['coverage_gate'] for k in ('body', 'late') for q in ('A', 'beta')) and dp['passed'])
        grids.append({'id': name, 'summary': dense, 'comparison': comparison,
                      'qualification': dq, 'point_coverage': dp, 'coverage_passed': coverage,
                      'passed': comparison['passed'] and coverage})
        print('GRID', name, grids[-1]['passed'], flush=True)
    clean_rows = [r for r in rows if r['is_clean_coverage_case']]
    coverage_gate = all(r['point_coverage']['passed'] and all(
        r['qualification'][k][q]['coverage_gate'] for k in ('body', 'late') for q in ('A', 'beta')) for r in clean_rows)
    useful = []
    for row in rows:
        if row['case']['id'] in informative_ids:
            passed = all(row['qualification']['late'][q]['informative'] and
                         row['qualification']['late'][q]['unexpanded_truth_coverage'] and
                         row['qualification']['late'][q]['zero_decay_excluded'] for q in ('A', 'beta'))
            useful.append({'id': row['case']['id'], 'passed': passed})
    nulls = null_check(rows)
    gates = {'clean_case_count': len(clean_rows), 'all_clean_coverage': coverage_gate,
             'eight_informative_late_cases': len(useful) == 8 and all(x['passed'] for x in useful),
             'null_information': nulls['passed'], 'finite_grid_stability_and_coverage': all(g['passed'] for g in grids),
             'mathematical_enclosures': math_result['passed']}
    gates['all'] = all(gates[k] for k in ['all_clean_coverage', 'eight_informative_late_cases',
                                        'null_information', 'finite_grid_stability_and_coverage', 'mathematical_enclosures'])
    source = source_measurements(design, out) if gates['all'] and allow_source else None
    result = {'schema': 'press78.pm-envelope-v2-result.v1', 'design': artifact(design_path),
              'binding': artifact(binding_path), 'gates': gates, 'mathematical_checks': artifact(out / 'mathematical-checks.json'),
              'controls': rows, 'informative_checks': useful, 'null_checks': nulls, 'grid_checks': grids,
              'source_inference_attempted': source is not None, 'source_results': source,
              'external_prediction': design['external_prediction'], 'prediction_used_for_profile_selection': False,
              'conditional_scope': 'Empirical measurement disks and finite PM-family outer sets; discarded dependencies permit false admissions. No certified error bars, intrinsic envelope identification or dry-capture proof.',
              'processed_confound_ids': [r['case']['id'] for r in rows if not r['is_clean_coverage_case']],
              'elapsed_seconds': time.monotonic() - started,
              'no_production_changes': True, 'no_noise_path_added': True}
    write(out / 'result.json', result)
    print(json.dumps(gates), flush=True)
    if not gates['all']: print('STOP: v2 failed; no Bass source decoded', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('bind', 'run'):
        p = sub.add_parser(command)
        p.add_argument('--design', type=Path, required=True)
        p.add_argument('--out', type=Path, required=True)
        if command == 'run':
            p.add_argument('--binding', type=Path, required=True)
            p.add_argument('--source', action='store_true')
    args = parser.parse_args()
    if args.command == 'bind': bind(args.design.resolve(), args.out)
    else: run(args.design.resolve(), args.binding.resolve(), args.out, args.source)


if __name__ == '__main__':
    main()
