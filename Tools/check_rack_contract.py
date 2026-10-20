"""Check generated Rack identity, presets and parameter/localization coverage.

The frozen research decoder is the independent oracle for factory parameters.
This is a source contract check; SDK build and host creation are separate gates.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from modern_bank import load_modern, load_rack_startup, preset_relative_path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('device', type=Path)
    args = parser.parse_args()
    device = args.device.resolve()
    schema = json.loads((ROOT/'Assets/controls.json').read_text())
    rows = {row['id']: row for row in schema['controls']}
    assert len(rows) == len(schema['controls']) == 73
    hidden={name for name,row in rows.items() if row.get('hidden')}
    assert hidden == {'noiseRms','noiseModel','sustainMode','velocityCurve','keyLevelModel','allocationModel','chorusCircuit'}
    visible=set(rows)-hidden
    assert all(rows[name]['default']==0 for name in hidden)
    # Old songs lack this property and must keep their original tuning.
    assert rows['pitchModel']['default']==0
    assert schema['startup_profile']['values']['pitchModel']==1
    assert rows['sustainMode']['default']==0 and rows['sustainMode']['startup_default']==1
    assert schema['startup_profile']['values']['sustainMode']==1
    assert rows['velocityCurve']['default']==0 and rows['velocityCurve']['startup_default']==1
    assert schema['startup_profile']['values']['velocityCurve']==1
    assert rows['keyLevelModel']['default']==0 and rows['keyLevelModel']['startup_default']==1
    assert schema['startup_profile']['values']['keyLevelModel']==1
    assert rows['allocationModel']['default']==0 and rows['allocationModel']['startup_default']==1
    assert schema['startup_profile']['values']['allocationModel']==1
    assert rows['chorusCircuit']['default']==0 and rows['chorusCircuit']['startup_default']==1
    assert schema['startup_profile']['values']['chorusCircuit']==1
    assert rows['bendRange']['default']==2 and rows['bendRange']['startup_default']==1
    assert schema['startup_profile']['values']['bendRange']==1
    info = (device/'info.lua').read_text()
    startup=load_rack_startup()
    assert schema['rack_startup']==startup
    for field, expected in [('product_id', schema['product']), ('version_number', schema['version']),
                            ('default_patch', startup['default_patch'])]:
        assignments=re.findall(rf'^[ \t]*{field}[ \t]*=',info,re.MULTILINE)
        values=re.findall(rf'^[ \t]*{field}[ \t]*=[ \t]*"([^"\n]*)"[ \t]*(?:--[^\n]*)?$',info,re.MULTILINE)
        assert len(assignments)==len(values)==1 and values[0]==expected, (field,values,expected)
    assert schema['product'].split('.')[-1] == 'Press78'
    mother = (device/'motherboard_def.lua').read_text()
    cpp = (device/'Parameters.h').read_text()
    apply = (device/'ApplyParameters.inc').read_text()
    for key in rows:
        assert re.search(rf'\b{key}\s*=\s*jbox.number', mother), key
        assert f'k_{key}' in cpp, key
        if key in {'noiseRms','noiseModel'}:
            assert f'controls.{key} = 0;' in apply, key
        else:
            assert f'physical(k_{key})' in apply or key in ('bendRange', 'modWheelDepth'), key
    groups=mother.split('ui_groups = {',1)[1]
    grouped=re.findall(r'"/custom_properties/([^"]+)"',groups)
    assert len(grouped) == len(visible) and set(grouped) == visible
    remote=mother.split('remote_implementation_chart = {',1)[1].split('midi_implementation_chart =',1)[0]
    assert set(re.findall(r'\["/custom_properties/([^"]+)"\]',remote)) == visible
    # All panel parameters need explicit, stable host automation mappings.
    registry = json.loads((ROOT/'Assets/rack-automation.json').read_text())
    assert registry['product'] == schema['product']
    automation = re.findall(r'\[(\d+)\]\s*=\s*"/custom_properties/([^\"]+)"',
                            mother.split('midi_implementation_chart =',1)[1].split('ui_groups =',1)[0])
    ids = {name: int(number) for number, name in automation}
    assert len(automation) == len(ids) == len(rows)
    assert ids == registry['ids'] and set(ids) == set(rows)
    assert len(set(ids.values())) == len(ids)
    assert ids['masterGain'] == 7 and ids['toneCutoffHz'] == 74
    assert ids['pitchModel'] == 319 and ids['sustainMode'] == 320 and ids['velocityCurve'] == 323
    assert ids['keyLevelModel'] == 324 and ids['allocationModel'] == 325
    assert ids['chorusCircuit'] == 326
    assert all(number in (7,74) or 256 <= number <= 10039 for number in ids.values())
    locale = (device/'Resources/English/texts.lua').read_text()
    keys = set(re.findall(r'\["([^"]+)"\]\s*=', locale))
    lua_paths = [device/'motherboard_def.lua'] + list((device/'GUI2D').glob('*.lua')) + list((device/'GUI/Output').glob('*.lua'))
    used = set()
    for path in lua_paths:
        used.update(re.findall(r'jbox.ui_text\("([^"]+)"\)', path.read_text()))
    assert not used-keys, f'Missing localization: {used-keys}'

    # Execute only the unchanged pure decoder function, avoiding the reference
    # renderer's NumPy/SciPy dependency for this metadata-only check.
    source = ROOT/'Tools/reference/src/pss780.py'
    tree = ast.parse(source.read_text())
    decoder = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'read_sysex')
    namespace = {}
    exec(compile(ast.Module(body=[decoder], type_ignores=[]), str(source), 'exec'), namespace)
    bank = json.loads((ROOT/'Assets/FactoryBank/press78-factory.json').read_text())
    expected = {'Init': {'pitchModel': 1, 'sustainMode': 1, 'bendRange': 1, 'velocityCurve': 1, 'keyLevelModel': 1, 'allocationModel': 1, 'chorusCircuit': 1}}
    aliases = {'lks_hi': 'lksHi', 'lks_lo': 'lksLo', 'am_enable': 'amEnable'}
    for voice in bank['voices']:
        patch = namespace['read_sysex'](bytes.fromhex(voice['sysex_hex']))
        values = {}
        for op, prefix in [('modulator', 'mod'), ('carrier', 'car')]:
            values.update({prefix+'_'+aliases.get(key, key): value for key, value in patch[op].items()})
        for key in ('feedback', 'pms', 'ams', 'vibrato_delay', 'vibrato', 'sustain'):
            values['vibratoDelay' if key == 'vibrato_delay' else key] = int(patch[key])
        values.update(pitchModel=1,sustainMode=1,bendRange=1,velocityCurve=1,keyLevelModel=1,allocationModel=1,chorusCircuit=1,chorusMode=1,chorusRateHz=0.9546467517767424,
                      chorusDepthMs=math.hypot(0.0495126833338911,0.4943632948117077))
        assert voice['name'].startswith('PSS ')
        expected[voice['name'].replace('/', '-')] = values
    modern = load_modern()
    for voice in modern:
        expected[voice['name']] = voice['parameters']
    paths = sorted((device/'Resources/Public').rglob('*.repatch'))
    assert len(paths) == 151
    assert {p.stem for p in paths} == set(expected)
    assert {p.relative_to(device/'Resources/Public').as_posix() for p in paths if p.parts[-3]=='Modern'} == {preset_relative_path(v).as_posix() for v in modern}
    startup_path=device/'Resources'/startup['default_patch'].lstrip('/')
    assert startup_path in paths and startup_path.stem==startup['name']
    for path in paths:
        # Python accepts declarations which the Recon SXML reader rejects.
        assert path.read_bytes().startswith(b'<?xml version="1.0"?>\n'), (path.name, 'SDK5 patch XML declaration')
        tree = ET.parse(path)
        props = tree.find('Properties')
        assert props.attrib == {'deviceProductID': schema['product'], 'deviceVersion': schema['version']}
        obj = props.find('Object')
        assert obj.attrib == {'name': 'custom_properties'}
        values = {v.attrib['property']: float(v.text) for v in obj}
        assert len(obj) == len(values) == len(rows) and set(values) == set(rows)
        for key, value in values.items():
            row = rows[key]
            assert math.isfinite(value)
            if row['integer']:
                assert value == round(value) and 0 <= value <= row['max']-row['min']
                physical = value+row['min']
            else:
                assert 0 <= value <= 1
                physical = row['min']+value*(row['max']-row['min'])
            target = expected[path.stem].get(key, row['default'])
            assert abs(physical-target) < 1e-9, (path.name, key, physical, target)
    result = dict(passed=True, controls=len(rows), visible_controls=len(visible), hidden_compatibility_properties=sorted(hidden), performance_inputs=3, patches=len(paths),
                  rack_startup=startup,
                  automation_mappings=len(ids),
                  localization_references=len(used), scope='Generated source contracts; no host execution',
                  sha256={str(p.relative_to(device)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [device/'info.lua', device/'motherboard_def.lua', device/'Parameters.h', device/'ApplyParameters.inc', *paths]})
    out = device/'Tests/results/rack-contract.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2)+'\n')
    print(f'PASS: {len(rows)} controls, {len(paths)} patches, {len(used)} localized keys')


if __name__ == '__main__':
    main()
