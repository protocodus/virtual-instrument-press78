"""Public-data-only checks; synthetic bytes below are not a factory voice."""
from copy import deepcopy
from firmware_allocator import FirmwareAllocator
from program_loader import ProgramLoader, WorkingPatch


def patch(seed=17):
    return WorkingPatch(tuple((seed + 37 * i) % 256 for i in range(32)))


def loader(target='780', effects=0, value=None):
    return ProgramLoader(target, FirmwareAllocator(0, cached_programs=[255] * 12),
                         value or patch(), program=7, effects=effects)


def main():
    checks = 0

    def eq(actual, expected):
        nonlocal checks
        assert actual == expected, (actual, expected)
        checks += 1

    def reject(fn):
        nonlocal checks
        try:
            fn()
        except ValueError:
            checks += 1
        else:
            raise AssertionError('unsupported input accepted')

    # Every possible control byte and both operator positions: masks are
    # independently expressed as selected bit sets, not another adapter call.
    for value in range(256):
        fields = [0] * 32
        fields[14] = fields[15] = value
        p = WorkingPatch(fields)
        for slot in range(12):
            words = p.reload_words(slot)
            eq(len(words), 14)
            eq(words[2], [544 + slot // 2,
                64 + 128 * (slot % 2) + sum(value & (1 << bit) for bit in (3, 4, 5))])
            eq(words[-1], [536 + slot // 2,
                128 * (slot % 2) + sum(value & (1 << bit) for bit in (0, 1, 4, 5, 6))])
            eq([word[1] for word in words[:2]], [127, 127])

    # Synthetic authored data: nonzero high nibbles distinguish old RR/SRR.
    fields = [0] * 32
    fields[12], fields[13], fields[19], fields[20] = 0xa2, 0x34, 0xf1, 0xe5
    old = WorkingPatch(fields)
    for target in ('780', '680'):
        m = loader(target, effects=6, value=old)
        for note in (48, 96, 60):
            m.serial('on', note)
            m.service()
        before = deepcopy(m.allocator.__dict__)
        fresh = [0] * 32
        fresh[23] = 128
        words = m.load(WorkingPatch(fresh), program=29)
        eq(len(words), 177 if target == '780' else 168)
        eq(m.effects, 5)  # New Vibrato on/Sustain off; old Reverb preserved.
        eq(m.allocator.notes, before['notes'])
        eq(m.allocator.cached, [255] * 12)
        if target == '780':
            eq(words[:9], [[752, 161], [760, 53], [520, 24],
                            [737, 161], [745, 53], [520, 1],
                            [736, 161], [744, 53], [520, 0]])
            eq(m.allocator.ranks, [126, 124, 125] + [0] * 9)
            eq(m.allocator.held_keys, set())
        else:
            eq(m.allocator.__dict__, before)
        # Same-data reselection remains a full reload, never an optimization.
        again = m.load(WorkingPatch(fresh), program=29)
        eq(len(again), 168)
        eq(sum(word[1] == 127 for word in again), 24)

    # Pending cancellation/preservation is explicit service-invocation behavior.
    for target in ('780', '680'):
        m = loader(target)
        m.serial('on', 60)
        m.load(patch(93), program=88)
        pitch, keys = m.service()
        eq(pitch, [])
        eq(keys, [] if target == '780' else [[520, 24]])
        pitch, _ = m.serial('on', 60)
        eq(pitch, [0] if target == '780' else [])

    # Thirteen held keys do not create a thirteenth normal slot on clear.
    m = loader()
    for note in range(48, 61):
        m.serial('on', note)
        m.service()
    eq(len(m.allocator.held_keys), 13)
    eq(len(m.load(patch(), program=7)), 204)
    eq(m.allocator.held_keys, set())

    # Unsupported parts/modes and malformed fields are rejected atomically.
    reject(lambda: WorkingPatch([0] * 31))
    reject(lambda: WorkingPatch([256] + [0] * 31))
    reject(lambda: WorkingPatch([False] + [0] * 31))
    reject(lambda: loader('other'))
    reject(lambda: ProgramLoader('780', FirmwareAllocator(99), patch(), program=0))
    reject(lambda: ProgramLoader('780', FirmwareAllocator(0), patch(), program=0))
    for note in (0, 35, 97, 127, 60.0, True):
        reject(lambda note=note: loader().serial('on', note))
    reject(lambda: loader().serial('control', 60))
    reject(lambda: loader().service(-1))
    reject(lambda: loader().service(1.5))
    m = loader()
    m.serial('on', 60)
    before = deepcopy(m.allocator.__dict__)
    reject(lambda: m.load(patch(99), program=256))
    eq(m.allocator.__dict__, before)
    m.allocator.enabled_channels = 3
    reject(lambda: m.load(patch(), program=0))
    m = loader()
    m.allocator.pending[0] = 7
    reject(lambda: m.load(patch(), program=0))
    print(f'{checks} synthetic command/state assertions passed; no factory data or audio')
    return checks


if __name__ == '__main__':
    main()
