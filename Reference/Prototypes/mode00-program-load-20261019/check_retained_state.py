"""Reproduce retained normal-slot state/key outputs without firmware or voices."""
from pathlib import Path
import hashlib
import json
from check import loader
from program_loader import WorkingPatch


def main():
    here = Path(__file__).resolve().parent
    fixture = json.loads((here / 'state_fixture.json').read_text())
    checks = 0
    for case in fixture['cases']:
        model = loader(case['target'])
        for event in case['events']:
            if event['kind'] == 'service':
                model.service()
            else:
                model.serial(event['kind'], event['note'])
        # Fresh synthetic sound fields; no original factory data is required.
        words = model.load(WorkingPatch([(71 + 19 * i) % 256 for i in range(32)]), program=29)
        a = model.allocator
        actual = dict(load_write_count=len(words),
            selection_keys=[word for word in words if word[0] == 520],
            ranks=a.ranks, notes=a.notes, pending=a.pending,
            cached=a.cached, held=sorted(a.held_keys))
        for key, expected in case['expected'].items():
            assert actual[key] == expected, (case['target'], case['scenario'], key)
            checks += 1
        for expected in case['post_services']:
            _, keys = model.service()
            assert keys == expected['keys'], (case['target'], case['scenario'], 'service keys')
            assert a.pending == expected['pending'], (case['target'], case['scenario'], 'pending')
            checks += 2
    print(f'{len(fixture["cases"])} retained original state cases, {checks} exact assertions passed')
    print('Fixture SHA256:', hashlib.sha256((here / 'state_fixture.json').read_bytes()).hexdigest())
    return checks


if __name__ == '__main__':
    main()
