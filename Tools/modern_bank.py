"""Canonical, original Press78 modern factory sound definitions (physical units)."""
from collections import Counter
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FRAGMENTS = ('modern-low-end.json', 'modern-played.json', 'modern-atmospheres.json')
CATEGORY_COUNTS = {'Bass': 12, 'Donk': 8, 'Pluck': 12, 'Lead': 8, 'Pad': 6, 'FX': 4}

def preset_relative_path(voice):
    return Path('Modern') / voice['category'] / (voice['name'] + '.repatch')

def load_rack_startup(voices=None):
    """Resolve the Rack default patch without duplicating its sound parameters.

    This selects an existing factory sound for new Reason devices only; control
    defaults remain the compatibility values used by old songs and the plug-in.
    """
    config = json.loads((ROOT / 'Assets/FactoryBank/rack-startup.json').read_text())
    if set(config) != {'schema', 'preset_id'} or config['schema'] != 'press78.rack-startup.v1':
        raise ValueError('Unexpected Rack startup selection schema')
    matches = [v for v in (load_modern() if voices is None else voices)
               if v['id'] == config['preset_id']]
    if len(matches) != 1:
        raise ValueError('Rack startup must select exactly one modern factory sound')
    voice = matches[0]
    return {'preset_id': voice['id'], 'name': voice['name'],
            'default_patch': '/Public/' + preset_relative_path(voice).as_posix()}

def load_modern():
    schema = json.loads((ROOT / 'Assets/controls.json').read_text())
    specs = {row['id']: row for row in schema['controls']}
    voices = []
    for name in FRAGMENTS:
        doc = json.loads((ROOT / 'Assets/FactoryBank' / name).read_text())
        if doc['schema'] != 'press78.modern-fragment.v1':
            raise ValueError('Unexpected modern bank schema: ' + name)
        voices.extend(doc['voices'])
    if Counter(v['category'] for v in voices) != CATEGORY_COUNTS:
        raise ValueError('Modern bank must contain exactly the intended 50 sounds')
    names, ids, patches = set(), set(), set()
    for voice in voices:
        name, identity, p = voice['name'], voice['id'], voice['parameters']
        if not re.fullmatch(r'[A-Z]+ - [A-Za-z0-9 +_-]+', name) or len(name) > 30:
            raise ValueError('Unsafe or long patch name: ' + name)
        if name.casefold() in names or identity in ids:
            raise ValueError('Duplicate patch identity: ' + name)
        names.add(name.casefold()); ids.add(identity)
        if set(p) != set(specs):
            raise ValueError(f'Patch must explicitly define all {len(specs)} controls: ' + name)
        for key, value in p.items():
            row = specs[key]
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError('Nonfinite parameter: ' + name + '/' + key)
            if not row['min'] <= value <= row['max'] or (row['integer'] and value != round(value)):
                raise ValueError('Out-of-range physical value: ' + name + '/' + key)
        for key, value in {'noiseRms': 0, 'noiseModel': 0, 'pitchModel': 1, 'sustainMode': 1, 'velocityCurve': 1, 'keyLevelModel': 1, 'allocationModel': 1, 'chorusCircuit': 1,
                           'outputCircuit': 1, 'outputLimit': 1}.items():
            if p[key] != value:
                raise ValueError('Modern character/noise policy mismatch: ' + name + '/' + key)
        if p['velocitySensitivity'] <= 0 or p['modWheelDepth'] <= 0:
            raise ValueError('Missing performance response: ' + name)
        if set(voice['performance']) != {'velocity', 'mod_wheel', 'pitch_bend'}:
            raise ValueError('Missing playing guidance: ' + name)
        low, high = voice['recommended_notes']
        if not 0 <= low < high <= 127 or not voice['description'].strip():
            raise ValueError('Missing range or description: ' + name)
        signature = tuple(p[key] for key in sorted(p))
        if signature in patches:
            raise ValueError('Duplicate sound parameters: ' + name)
        patches.add(signature)
    return voices

def main():
    voices = load_modern()
    print(json.dumps({'passed': True, 'presets': len(voices),
                      'categories': dict(Counter(v['category'] for v in voices)),
                      'all_parameters_explicit': len(voices[0]['parameters']), 'added_noise': False}))

if __name__ == '__main__':
    main()
