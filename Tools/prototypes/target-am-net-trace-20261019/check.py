#!/usr/bin/env python3
"""Check a bounded AM-board trace attempt without inventing a circuit model.

Protocol: bind the previously acquired photos, manufacturer pinout scans and
three prior ledgers; exclude each frozen region from the old 26-point
exploratory fit; report prediction error and a manual-contact sensitivity
scenario. These are reused, already inspected hypotheses, NOT independent
held-out landmarks. No result promotes the old transform to a numbered net.
No electrical constants are estimated, no audio is rendered, and no production
files are read or changed. Photographic crops stay in the ignored build folder.
"""

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project(h, points):
    p = np.c_[points, np.ones(len(points))] @ h.T
    return p[:, :2] / p[:, 2:]


def jacobian(h, point):
    x, y = point
    q = h @ np.array([x, y, 1.0])
    return np.array([
        [(h[0, 0] * q[2] - q[0] * h[2, 0]) / q[2] ** 2,
         (h[0, 1] * q[2] - q[0] * h[2, 1]) / q[2] ** 2],
        [(h[1, 0] * q[2] - q[1] * h[2, 0]) / q[2] ** 2,
         (h[1, 1] * q[2] - q[1] * h[2, 1]) / q[2] ** 2],
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    frozen = json.loads((here / 'input.json').read_text())
    checked = []
    for item in frozen['inputs']:
        path = Path(item['path'])
        assert path.stat().st_size == item['bytes'], path
        assert sha(path) == item['sha256'], path
        checked.append(item)

    prior = json.loads(Path(checked[3]['path']).read_text())
    copper = json.loads(Path(checked[4]['path']).read_text())
    assert prior['status'] == 'NOT_ACCEPTED_FOR_PIN_OR_NET_MAPPING'
    assert copper['accepted_numbered_target_nets'] == 0
    correspondences = prior['best_exploratory_trial']['correspondences']
    source = np.array([p['source'] for p in correspondences], dtype=float)
    target = np.array([p['copper'] for p in correspondences], dtype=float)
    assert source.shape == (26, 2)
    # The two four-pad near rows used in the already explored hypothesis.
    pitches = np.concatenate([
        np.linalg.norm(np.diff(target[8:12], axis=0), axis=1),
        np.linalg.norm(np.diff(target[12:16], axis=0), axis=1),
    ])
    min_pitch = float(np.min(pitches))
    trials = []
    for trial in frozen['grouped_exclusions']:
        excluded = np.array(trial['excluded_indices'], dtype=int)
        keep = np.ones(26, dtype=bool)
        keep[excluded] = False
        h, _ = cv2.findHomography(source[keep], target[keep], method=0)
        predicted = project(h, source)
        errors = np.linalg.norm(predicted - target, axis=1)
        norms = np.array([
            np.linalg.svd(jacobian(h, p), compute_uv=False)[0]
            for p in source[excluded]
        ])
        uncertainty = frozen['manual_uncertainty_scenario']
        sensitivity = (errors[excluded] + norms *
                       uncertainty['component_contact_radius_px'] +
                       uncertainty['copper_pad_center_radius_px'])
        trials.append({
            'id': trial['id'], 'accepted': False,
            'independent_holdout': False,
            'H': h.tolist(), 'excluded_indices': excluded.tolist(),
            'training_max_error_px': float(np.max(errors[keep])),
            'excluded_errors_px': errors[excluded].tolist(),
            'excluded_max_error_px': float(np.max(errors[excluded])),
            'local_maximum_jacobian_singular_values': norms.tolist(),
            'manual_sensitivity_sums_px': sensitivity.tolist(),
            'maximum_manual_sensitivity_sum_px': float(np.max(sensitivity)),
            'sum_exceeds_half_minimum_pitch': bool(np.any(sensitivity > min_pitch / 2)),
            'sum_exceeds_minimum_pitch': bool(np.any(sensitivity > min_pitch)),
            'qualification': 'Sensitivity scenario, not an empirical confidence or error bound.',
        })

    args.out.mkdir(parents=True, exist_ok=True)
    crops = []
    for item in frozen['inspections']:
        image = Image.open(checked[item['source_index']]['path']).crop(item['crop'])
        scale = item['enlarge']
        if scale != 1:
            image = image.resize((image.width * scale, image.height * scale))
        path = args.out / item['output']
        image.save(path)
        crops.append({'path': str(path.resolve()), 'bytes': path.stat().st_size,
                      'sha256': sha(path), 'source_crop': item})

    # Manufacturer labels are constraints only. The photo-to-pad identity is
    # deliberately not derived from a familiar electrical topology.
    pinouts = {
        'MN3206': {'1': 'GND', '2': 'CP1', '3': 'IN', '4': 'VGG',
                   '5': 'VDD', '6': 'CP2', '7': 'OUT1', '8': 'OUT2'},
        'MN3102': {'1': 'VDD', '2': 'CP1', '3': 'GND', '4': 'CP2',
                   '5': 'OX3', '6': 'OX2', '7': 'OX1', '8': 'VGG(out)'},
    }
    for hypothesis in frozen['conditional_hypotheses']:
        edge_id = hypothesis['visible_group'].replace('group', 'edge', 1)
        edge = next(x for x in copper['original_anonymous_edges']
                    if x['id'] == edge_id)
        assert [p['xy'] for p in hypothesis['conditional_pins']] == edge['endpoints']
        for pin in hypothesis['conditional_pins']:
            assert pinouts[pin['part']][str(pin['pin'])] == pin['name']

    result = {
        'schema': 'press78.target-am-net-trace-result.v1',
        'date': '2026-10-19',
        'status': 'BOUNDED_ATTEMPT_NO_ACCEPTED_NAMED_NET',
        'accepted_numbered_target_nets': 0,
        'accepted_component_value_to_pin_associations': 0,
        'new_independent_distant_landmarks': 0,
        'newly_acquired_photos_or_datasheets': 0,
        'prior_correspondences_reused': 26,
        'minimum_proposed_near_row_pitch_px': min_pitch,
        'near_row_pitches_px': pitches.tolist(),
        'input': {'path': str((here / 'input.json').resolve()),
                  'sha256': sha(here / 'input.json')},
        'checker': {'path': str(Path(__file__).resolve()),
                    'sha256': sha(Path(__file__))},
        'checked_inputs': checked,
        'grouped_exclusion_checks': trials,
        'manufacturer_pinouts_from_bound_primary_scans': pinouts,
        'conditional_hypotheses': frozen['conditional_hypotheses'],
        'inspection_artifacts': crops,
        'outcome': 'No fresh independently identifiable distant board-plane landmark was recovered. Exclusion fits are exploratory and cannot satisfy the requested independent error bound. Conditional pin/topology consistency does not validate package-to-pad assignment.',
        'model_changes_justified': False,
        'production_changes': False,
        'software': {'opencv': cv2.__version__, 'numpy': np.__version__},
    }
    (args.out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({
        'status': result['status'], 'bound_inputs': len(checked),
        'minimum_proposed_pad_pitch_px': min_pitch,
        'excluded_max_errors_px': [x['excluded_max_error_px'] for x in trials],
        'maximum_manual_sensitivity_sums_px': [x['maximum_manual_sensitivity_sum_px'] for x in trials],
        'accepted_numbered_target_nets': 0,
    }))


if __name__ == '__main__':
    main()
