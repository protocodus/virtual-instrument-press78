"""Functional PSS-680/780 normal-voice command allocator research prototype.

Independently expressed behavior, not copied firmware. No ROM, oscillator,
envelope, sample time, audio, rhythm or accompaniment engine is implemented.
Mode00 input is the serial-to-keyboard scan path, Mode99 the received-note path.
Initialization snapshots are supplied by the research fixture, not full boot.
"""


class FirmwareAllocator:
    def __init__(self, mode, *, ranks=None, notes=None, cached_programs=None,
                 received_notes=None, received_channels=None, enabled_channels=1):
        self.mode = mode
        self.ranks = list(ranks if ranks is not None else [0] * 12)
        self.notes = list(notes if notes is not None else [0] * 12)
        self.cached = list(cached_programs if cached_programs is not None else [0] * 12)
        self.received_notes = list(received_notes if received_notes is not None else [0] * 12)
        self.received_channels = list(received_channels if received_channels is not None else [0] * 12)
        self.pending = [0] * 12
        self.keyed = [False] * 12
        self.held_keys = set()
        self.enabled_channels = enabled_channels

    def _age(self):
        self.ranks = [x if x in (0, 128) else x - 1 for x in self.ranks]

    def _key_command(self, slot):
        pair = slot // 2
        value = pair | (24 if self.keyed[2 * pair] else 0)
        value |= 96 if self.keyed[2 * pair + 1] else 0
        return [0x208, value]

    def _off_slot(self, slot):
        self.ranks[slot] = 127
        self._age()
        self.pending[slot] = 0
        self.keyed[slot] = False
        return self._key_command(slot)

    def _choose_general(self):
        valid = [i for i in range(12) if self.ranks[i] < 255]
        return min(valid, key=lambda i: (self.ranks[i], i)) if valid else None

    def _choose_cached(self, program):
        valid = [i for i in range(12) if self.cached[i] == program and self.ranks[i] < 128]
        return min(valid, key=lambda i: (self.ranks[i], i)) if valid else None

    def process(self, kind, note=None, channel=0, count=0, program=99):
        """Return proposed pitch slots and key-command writes for one event.

        All slots are normal voice-kind0 here. Other original parts, drum MIDI
        channel15, program-change commands and physical keyboard scanning are
        outside this adapter. Service count is an invocation count, not time.
        """
        keys = []
        pitches = []
        if kind == 'service':
            for _ in range(count):
                for i in range(12):
                    if self.pending[i]:
                        self.pending[i] -= 1
                        if not self.pending[i]:
                            self.keyed[i] = True
                            keys.append(self._key_command(i))
            return pitches, keys
        if not (self.enabled_channels & (1 << channel)):
            return pitches, keys
        if self.mode == 0:
            # A repeated set/clear of the received-key bitmap has no edge.
            if (kind == 'on') == (note in self.held_keys):
                return pitches, keys
            if kind == 'on':
                self.held_keys.add(note)
            else:
                self.held_keys.discard(note)
            same = [i for i in range(12) if self.notes[i] == note]
            slot = max(same) if same else None
            if kind == 'off':
                if slot is not None:
                    keys.append(self._off_slot(slot))
                return pitches, keys
            if slot is None:
                slot = self._choose_general()
            if slot is None:
                return pitches, keys
            # The ordinary Mode00 path always sends selected-slot keyoff.
            keys.append(self._off_slot(slot))
        else:
            if kind == 'off':
                same = [i for i in range(12) if self.received_channels[i] == channel
                        and self.received_notes[i] == note]
                if same:
                    slot = max(same)
                    self.received_notes[slot] = 0
                    keys.append(self._off_slot(slot))
                return pitches, keys
            slot = self._choose_cached(program)
            if slot is None:
                slot = self._choose_general()
            if slot is None:
                return pitches, keys
            if self.ranks[slot] & 128:
                self.received_notes[slot] = 0
                keys.append(self._off_slot(slot))
            self.cached[slot] = program
            self.received_channels[slot] = channel
            self.received_notes[slot] = note
        self.notes[slot] = note
        self.pending[slot] = 1
        self.ranks[slot] = 255
        self._age()
        pitches.append(slot)
        return pitches, keys
