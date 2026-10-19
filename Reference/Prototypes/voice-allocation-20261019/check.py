"""Check the research adapter against retained original-program command outputs.

Uses only the Python standard library and public functional fixtures. Does not
execute firmware or the shipping DSP, and makes no hardware-audio claim.
"""
from pathlib import Path
import hashlib
import json
from firmware_allocator import FirmwareAllocator


def main():
    fixture = Path(__file__).with_name('command_fixture.json')
    data = json.loads(fixture.read_text())
    checks = 0
    events = 0
    for case in data['cases']:
        model = FirmwareAllocator(case['mode'], **case['initial'])
        for row in case['events']:
            e = row['event']
            pitch, keys = model.process(e['kind'], e['note'], e['channel'], e['count'],
                                        program=case['program'])
            actual = {'pitch': pitch, 'keys': keys, 'ranks': model.ranks,
                      'notes': model.notes, 'received_notes': model.received_notes,
                      'received_channels': model.received_channels,
                      'pending': model.pending}
            for field, expected in row['expected'].items():
                assert actual[field] == expected, (case['model'], case['mode'],
                    case['scenario'], row['source_event_index'], field,
                    actual[field], expected)
                checks += 1
            events += 1
    print(f'{len(data["cases"])} original-program fixtures, {events} events, '
          f'{checks} exact assertions passed')
    print('Fixture SHA256:', hashlib.sha256(fixture.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
