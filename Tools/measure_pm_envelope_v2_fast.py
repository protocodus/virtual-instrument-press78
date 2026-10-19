#!/usr/bin/env python3
"""Performance-only v2 variant: skip finite, provably full-circle phase tests.

All extraction, enclosures, cases, gates, bounds and source policy come from the
unchanged frozen v2 implementation. This wrapper replaces only its profile()
with an exact copy containing one vacuous-predicate skip. Full execution requires
an independently reviewable six-completed-case exact equivalence receipt.
"""
from pathlib import Path
import importlib.util
import sys

_spec = importlib.util.spec_from_file_location('press78_pm_v2_frozen', Path(__file__).with_name('measure_pm_envelope_v2.py'))
_frozen = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _frozen
_spec.loader.exec_module(_frozen)
# Reuse the identical helper objects and caches; preserve this wrapper's path.
for _name, _value in vars(_frozen).items():
    if not _name.startswith('__'):
        globals()[_name] = _value
_frozen_binding_inputs = _frozen.binding_inputs

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
                        # Identical acceptance for finite angles and a full circle.
                        # NaN/inf keep the frozen predicate and its rejection behavior.
                        if np.all(radii >= np.pi) and np.all(np.isfinite(centers)):
                            continue
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


def binding_inputs(design):
    files, original = _frozen_binding_inputs(design)
    receipt = ROOT/'build/pm-envelope-v2-performance-20261019/equivalence-result.json'
    proof = json.loads(receipt.read_text())
    if (not proof['all_six_equal'] or len(proof['cases']) != 6 or
            proof['fast_tool']['sha256'] != sha(Path(__file__)) or
            proof['original_tool']['sha256'] != sha(Path(__file__).with_name('measure_pm_envelope_v2.py'))):
        raise ValueError('Mandatory six-case performance equivalence gate failed')
    return files + [Path(__file__), receipt], original


_frozen.profile = profile
_frozen.binding_inputs = binding_inputs
if __name__ == '__main__':
    _frozen.main()
