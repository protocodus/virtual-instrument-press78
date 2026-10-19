# Normal-voice allocator research prototype

This functional prototype reconstructs verified PSS-680/780 normal-voice command selection. It is **not connected to the shipping synth** and generates no audio. See the [source investigation](../../Research/opu-allocation-command-path-20261019.md) for scope, ROM identities, protocols, exact command tests and limitations.

`firmware_allocator.py` independently expresses the tested Mode 00 serial-to-keyboard and Mode 99 received-note paths using fixed twelve-slot state. It models same-pitch cache reuse, input-edge coalescing, program-cache preference, highest-slot note-off, pending keyon and eight-bit rank saturation. Service counts are invocations, not seconds. Initial rank/cache snapshots are supplied explicitly; this is not a complete boot implementation.

Only normal kind-0 voices and the declared serial sequences are represented. Rhythm channel 15, accompaniment reservations, actual program-change commands, physical keyboard scanning, MIDI/CV ownership adaptations and the chip's oscillator/envelope behavior are outside the adapter. The requested program identifies a cache key; the class does not load factory sound data. There is no original firmware, factory payload or recording in this directory.

`command_fixture.json` retains numerical outputs for independently authored event sequences executed on the original programs. Fourteen PSS-780 Sine99 development cases cover full-pool replacement, same-note reuse, duplicate messages and pending-key cancellation; two independently executed PSS-780/PSS-680 cases cover enabled channels 0/1. These are functional expected outputs, not bytes of executable code. The fixture's provenance hashes bind the complete ignored observations.

From the repository root:

```sh
python3 Reference/Prototypes/voice-allocation-20261019/check.py
```

The standard-library check compares16 cases, 526 events and 3,682 fields exactly. The broader local original-program experiments separately pass 106,496 primitive assertions and 154,224 full-adapter development comparisons. Passing this reference check establishes consistency with the retained command fixtures. It does not establish sound quality, hardware timing, chip phase behavior, full-boot equivalence or production adoption.
