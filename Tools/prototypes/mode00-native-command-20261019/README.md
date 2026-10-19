# Native Mode00 program command frontend

`Mode00ProgramCommands.h` is a standalone C++17 research component. It composes
an unchanged copy of the native candidate's `Mode00Allocator`; it never includes
or calls the audio engine. There is no firmware, factory voice bank, recording,
oscillator, envelope, timebase or output circuit in this directory.

The frontend owns one normal twelve-slot logical state. `restore()` accepts an
explicit snapshot only when the full pool, source 0 namespace, normal note range
36–96, shared `$FF` cache tags and pending counters 0/1 are supported. CV/source 1,
smaller pools and other service-counter branches are rejected before mutation.
The empty constructor is a logical starting state, not an emulated keyboard boot.

`noteOn()` and `noteOff()` return the existing allocator's edge, selected slot and
paired key commands. `noteOn()` leaves keyon pending; `service()` advances an
explicit invocation count. These methods do not build full original note/service
IO and assign no elapsed period. In particular, carrier-RR restoration and pitch
and level payloads are not implemented by their partial command view.
Ordinary note-off RR writes are also excluded from that allocation-only event
result. The auxiliary cache getters describe fields copied during a reload;
they do not model their later vibrato-service/main-loop evolution.

`selectProgram()` returns the complete tested normal program-load OPU plan. The
caller supplies an already-resolved 32-byte shared working patch, including the
factory-effect flags at byte 23, plus an internal program identifier. No panel
number translation or factory payload is embedded here.

- PSS-780 processes cleared serial keys in descending musical-pitch order. It
  selects the highest matching cached-pitch slot, emits that slot's old RR/SRR
  words and paired keyoff, and performs ordinary rank/pending updates. Uncached
  stolen inputs clear without creating slots.
- PSS-680 preserves the declared key, pending and rank state.
- Both then emit 168 reload writes across all twelve slots, including 24 TL127
  writes and no replacement actual note-level values. Cached pitches and `$FF`
  tags survive. Identical-data reselection still emits the reload.

The plan has fixed capacity 204 writes: at most 12 release triples plus 168 reload
writes. The implementation does not call the helper's ascending `allNotesOff()`
loop, the engine's future-only `setPatch()`, or its output-clearing
`allSoundOff()`. Calling one of those is not an equivalent implementation of this
command sequence.

Synthetic checks need only a C++17 compiler and the standard library:

```sh
mkdir -p build/native-command-check
clang++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Werror \
  -I Tools/prototypes/mode00-native-command-20261019 \
  Tools/prototypes/mode00-native-command-20261019/SyntheticTests.cpp \
  -o build/native-command-check/synthetic
build/native-command-check/synthetic
```

Both optimized and ASan/UBSan runs passed 81,361 synthetic assertions. The
separately retained local replay passes 1,344 rows and 18,696 exact fields per
build. It covers 60 original cases twice: sequential replay and direct restoration
of each original pre-load state, totaling 120 plans and 20,844 program-load words.
These are reused development observations, not new hardware measurements.

On the tested 64-bit native platform, the frontend is 280 bytes, its snapshot 232,
and the returned plan 856. The stream probe observed zero `new`/`new[]` calls while
frontend operations were instrumented. This is not a complete allocator audit,
malloc/aligned-allocation audit, native Reason validation or resource measurement
of an integrated instrument. The synthetic binary has no allocation hooks; the
scoped receipt corrects the initial runner's placeholder zeros for those rows.

The accompanying `CommandProbe.cpp` accepts generic text fixtures; the original
factory-derived inputs and its expanded output logs remain ignored. The design,
binding and scoped receipt retain their original workspace paths as historical
provenance. No fixture payload or original executable program is exported.

A future DSP backend must consume these register commands with independently
justified key, level, phase and envelope behavior. The frontend must not become a
second independently advancing allocator next to the current engine: integration
would need one authoritative state owner. Chip timing, audible silence or
retimbre, physical-key scanning, accompaniment/rhythm, Mode99 and CV policies are
outside this component. Nothing here changes production or generates audio.

The [research report](../../../Docs/research/mode00-native-command-bridge-2026-10-19.md) and
[manifest](manifest.json) bind the source, local tests and independent review.
