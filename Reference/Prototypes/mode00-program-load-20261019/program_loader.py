"""Firmware-free normal Mode00 program-load command/state research adapter.

No ROM, factory bank, DSP, physical-key scanner or elapsed-time model is present.
The caller resolves the factory/panel identifier and supplies the resulting
shared working-patch fields. Raw commands do not specify an audible response.
"""
from dataclasses import dataclass
from firmware_allocator import FirmwareAllocator


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an integer in [{low}, {high}]')
    return value


@dataclass(frozen=True)
class WorkingPatch:
    """Caller-owned, already-resolved 32-byte shared patch, not a factory bank.

    Byte23 must contain the resolved program effect flags copied into the shared
    working area by the original loader. It is not inferred from byte21 or from
    a panel number. Unused fields are retained without a guessed interpretation.
    """
    fields: tuple

    def __post_init__(self):
        values = tuple(self.fields)
        if len(values) != 32:
            raise ValueError('shared working patch requires 32 bytes')
        for value in values:
            _integer(value, 0, 255, 'patch byte')
        object.__setattr__(self, 'fields', values)

    def release_words(self, slot, sustain):
        """Old D1L high nibble plus selected RR/SRR low nibble; not an EG law."""
        _integer(slot, 0, 11, 'slot')
        delta = slot // 2 + 16 * (slot % 2)
        result = []
        for operator in range(2):
            base = self.fields[12 + operator]
            rate = self.fields[19 + operator] if sustain else base
            result.append([0x2e0 + delta + 8 * operator,
                           (base & 0xf0) | (rate & 0x0f)])
        return result

    def reload_words(self, slot):
        """The fourteen ordered operator/control writes for one normal slot."""
        _integer(slot, 0, 11, 'slot')
        delta = slot // 2 + 16 * (slot % 2)
        pair = slot // 2
        odd_bit = 0x80 if slot % 2 else 0
        result = [[0x260 + delta, 127], [0x268 + delta, 127],
                  [0x220 + pair, (self.fields[14] & 0x38) | 0x40 | odd_bit]]
        for field, address in ((0, 0x240), (6, 0x280), (8, 0x2a0),
                               (10, 0x2c0), (12, 0x2e0)):
            result.extend([[address + delta, self.fields[field]],
                           [address + delta + 8, self.fields[field + 1]]])
        result.append([0x218 + pair, (self.fields[15] & 0x73) | odd_bit])
        return result


class ProgramLoader:
    """Normal12-slot Mode00 adapter, with a single shared serial-key namespace.

    An existing FirmwareAllocator supplies cached notes/ranks/pending/key state.
    This does not import the native synth's immediate-keyon or voice lifetimes.
    The initialization snapshot is explicit; no full original boot is modeled.
    """
    def __init__(self, target, allocator, working_patch, *, program, effects=0):
        if target not in ('780', '680'):
            raise ValueError('target must be 780 or 680')
        if not isinstance(allocator, FirmwareAllocator) or allocator.mode != 0:
            raise ValueError('a Mode00 FirmwareAllocator is required')
        if not isinstance(working_patch, WorkingPatch):
            raise ValueError('resolved WorkingPatch is required')
        self.target = target
        self.allocator = allocator
        self.patch = working_patch
        self.program = _integer(program, 0, 255, 'internal program metadata')
        self.effects = _integer(effects, 0, 255, 'effect state')
        self._validate_scope()
        self._cache_controls()

    def _validate_scope(self):
        a = self.allocator
        if a.enabled_channels != 1:
            raise ValueError('this adapter accepts the declared channel0-only serial fixture')
        for values in (a.ranks, a.notes, a.cached, a.received_notes,
                       a.received_channels, a.pending, a.keyed):
            if len(values) != 12:
                raise ValueError('exactly twelve normal slots are required')
        if a.cached != [255] * 12:
            raise ValueError('only shared working-patch cache tags FF are supported')
        for value in a.ranks:
            _integer(value, 0, 255, 'rank byte')
        for value in a.notes:
            if value != 0:
                _integer(value, 36, 96, 'cached normal serial pitch')
        for value in a.pending:
            _integer(value, 0, 1, 'normal pending counter')
        for value in a.held_keys:
            _integer(value, 36, 96, 'normal held serial pitch')

    def _cache_controls(self):
        self.cached_byte21 = [self.patch.fields[21] & 0x7f] * 12
        self.cached_byte15 = [self.patch.fields[15] & 0x73] * 12
        self.cached_byte22 = [self.patch.fields[22]] * 12

    def serial(self, kind, note):
        """Selected pitch slots and paired key writes, not the full note-on IO.

        The valid serial note range36..96 is explicit. Unsupported events/ranges
        are rejected rather than silently claiming other original parts/modes.
        """
        if kind not in ('on', 'off'):
            raise ValueError('serial event must be on or off')
        _integer(note, 36, 96, 'normal serial pitch')
        self._validate_scope()
        return self.allocator.process(kind, note, channel=0)

    def service(self, count=1):
        """Pending state and paired key writes only; count is not elapsed time.

        Other original service writes, including raw carrier-RR restoration,
        remain outside this reused allocation-command view.
        """
        _integer(count, 0, 65535, 'service invocations')
        self._validate_scope()
        return self.allocator.process('service', count=count)

    def load(self, working_patch, *, program):
        """Return complete normal OPU program-reload writes, in original order.

        Target780 clears serial falling edges in descending musical-key order.
        This is not a descending slot loop: the ordinary highest matching cache
        lookup determines each slot. Target680 preserves input/allocator state.
        Full operator reloads then run0..11 on both targets, even for samepatch.
        """
        if not isinstance(working_patch, WorkingPatch):
            raise ValueError('resolved WorkingPatch is required')
        _integer(program, 0, 255, 'internal program metadata')
        self._validate_scope()
        writes = []
        if self.target == '780':
            for note in sorted(self.allocator.held_keys, reverse=True):
                matches = [i for i, value in enumerate(self.allocator.notes)
                           if value == note]
                _, keys = self.allocator.process('off', note, channel=0)
                if keys:
                    writes.extend(self.patch.release_words(max(matches), bool(self.effects & 2)))
                    writes.extend(keys)
        self.patch = working_patch
        self.program = program
        flags = working_patch.fields[23]
        self.effects = (self.effects & ~3) | (1 if flags & 128 else 0) | (2 if flags & 64 else 0)
        self.allocator.cached[:] = [255] * 12
        self._cache_controls()
        for slot in range(12):
            writes.extend(self.patch.reload_words(slot))
        return writes
