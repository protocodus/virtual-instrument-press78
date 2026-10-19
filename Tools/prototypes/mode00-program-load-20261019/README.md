# Mode00 program-load command adapter

This firmware-free research prototype reconstructs the tested normal twelve-slot
program-load commands and associated serial-key state. It is separate from the
shipping instrument and produces no audio. The [research note](../../../Docs/research/mode00-program-command-adapter-2026-10-19.md)
explains the original executions, ordering counterexample and limits.

`ProgramLoader` wraps the unchanged `FirmwareAllocator` from the earlier
[allocation prototype](../voice-allocation-20261019/README.md). Its caller supplies
a resolved `WorkingPatch` of 32 bytes and an internal program identifier. There is
no factory bank or panel-number translation here. Byte 23 must already contain the
factory-effect flags that the original loader placed in the shared working patch;
reading a raw bank entry without that resolution is not the same input.

For PSS-780, `load()` processes cleared serial keys in descending musical-pitch
order, uses the ordinary highest matching cached-note slot, sends its old RR/SRR
and paired key command, and updates ranks and pending state. A stolen held input
without a matching cached pitch clears without creating another slot. PSS-680
preserves input/rank/pending/key state. Both then emit the full 168 ordered reload
writes for slots 0–11, including 24 TL127 writes, even when reselecting the same data.
Neither path supplies replacement actual note levels in that reload sequence.

The public API deliberately separates complete program-reload writes from the
narrower serial/service allocation view. `serial()` returns selected pitch slots
and paired key writes only; it does not build pitch-word or level payloads.
`service()` advances pending invocation counters and returns paired key writes;
other service IO, including carrier-RR restoration, is excluded. A service count
is not a measured duration. These distinctions prevent a command test from
claiming complete firmware or chip timing.

Run with Python 3 and its standard library from the repository root:

```sh
python3 Tools/prototypes/mode00-program-load-20261019/check.py
python3 Tools/prototypes/mode00-program-load-20261019/check_retained_state.py
```

The first script checks 12,332 arithmetic/state assertions with newly authored
synthetic patch fields. The second compares 12 retained original-program cases
and 132 state/key assertions, substituting synthetic sound fields so it needs no
factory payload. The separate local [validation receipt](validation.json) records
exact agreement with all 10,422 program-load words in 60 original cases, plus the
surrounding 1,104 serial/service events. Its expanded original traces and
factory-derived inputs remain ignored; the public subset is not a replacement
for that complete local check. [The manifest](manifest.json) binds both scopes.

Only normal kind-0 Mode00 slots with shared `$FF` cache tags and the declared
channel 0 serial input are supported. Notes 36–96 are accepted; other ranges,
modes and cache kinds are rejected. Physical key polling, accompaniment,
rhythm, MIDI/CV ownership extensions, full boot, chip oscillator/phase/envelope
response, audible retimbre or silence, and output-circuit memory are unmodeled.
The adapter includes no ROM, factory voice bank, recording or production DSP.
