# Complete normal Mode00 command frontend

`Mode00CompleteCommands.h` is a research-only C++17 frontend. It emits complete
ordered OPU `$0200–$02FF` plans for its explicitly accepted operations. It has no
oscillator, amplitude/envelope transfer, audio output, original firmware,
physical boot or timed scheduler. Production DSP and every previous failed
audio adoption gate remain unchanged.

One unchanged `Mode00ProgramCommands` member owns allocation, input edges,
program metadata, shared patch/cache and global effects. The new component adds
explicit stable controller inputs and twelve independent vibrato-delay counters.
It does not run another allocator beside that owner.

The constructor is uninitialised. `restore()` requires the full normal
twelve-slot/source-0/shared-FF domain, pending counters 0/1, valid documented
seven-bit TLs, effect bits 0–7 and supported controller ranges. Rejection leaves
all authoritative state untouched. There is no inferred startup volume or boot
state. Volume table index 0 is retained for the explicitly constructed original
fixtures; ordinary physical panel values are 1–9.

The accepted command operations are:

- `noteOn(note, velocity)` / `noteOff(note)`: full release/key, calculated level,
  packed pitch and temporary carrier-RR sequence. Raw velocity 0 dispatches off;
  other valid Mode00 velocities produce the same key input.
- `serviceKeyOn()`: one original key-service invocation, including PMS/AMS and
  delay setup, raw carrier-RR restoration and paired key-on.
- `serviceVibrato()`: one separate vibrato-delay invocation; it can finish after
  note-off. Neither method assigns a duration.
- `sustainController(value)`: raw CC64 state replacement and all 24 normal-cache
  release-word refreshes, including a repeated value.
- `selectProgram(patch, program)`: the already verified target-specific complete
  program plan, retaining active delay counters and the one owner's effect state.

Stable pitch inputs are raw bend MSB 0–127, signed bend span ±1…±12 and fine
steps −16…+16 in 1/32 semitones. These inputs are not a live MIDI pitch-message
parser, pending-bend service, volume-button handler or portamento model. No live
Vibrato/Reverb button API is claimed. Their real post-control state is supplied
explicitly by a snapshot. Mode99, CV, accompaniment and physical keyboard scans
are excluded. Original `$0327` peripheral/MIDI-output writes are counted but are
outside the stated OPU domain.

The fixed 204-word plan capacity follows from structural per-call maxima:
ordinary on 9, off 3, key service 36, vibrato service 12, CC64 24, program 204.
Service APIs accept a single invocation. The fixture driver may concatenate
several complete single-invocation plans externally; this is not a larger
bounded component plan or a timing claim.

## Numerical helper provenance

`FirmwareLevel.h` is byte-identical to the independently authored reachable
command lookup exported in the existing
[key-level candidate patch](../key-level-20261019/candidate.patch). Its SHA256 is
`e2c5ad02b54aeaf03b1e7c88092af78903ea5b808b54eae2b2cefa8cda057283`;
the [original manifest](../key-level-20261019/manifest.json) records the same
3,679 bytes. The generator mentioned in its first comment is preserved inside
that patch as `Tools/generate_firmware_level.py`; it is not an active root tool
in this checkout. The helper was extracted unchanged from that public artifact.

Only integer command math is reused. The failed candidate's engine changes,
command-to-amplitude law, 0.75dB assumption, early-mute policy and audio result
are **not** adopted. Pitch plans call only the existing
`firmware_pitch::commands()` helper; its separate empirical frequency function
is not called.

## Reproduction and retained outcomes

The public synthetic checks require only a C++17 compiler:

```sh
mkdir -p build/mode00-complete-command-check
clang++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Werror \
  Tools/prototypes/mode00-complete-command-20261019/SyntheticTests.cpp \
  -o build/mode00-complete-command-check/synthetic
build/mode00-complete-command-check/synthetic
```

The local original-program/stream check uses only already retained hash-bound
ROMs and traces; it requires the previously installed py65 environment. Do not
rerun it merely to refresh a receipt. `collect_controls.py` refuses to overwrite
observations; `run.py` refuses to overwrite validation directories. Local
original-derived fixtures and expanded output logs stay ignored.

```sh
python3 Tools/prototypes/mode00-complete-command-20261019/run.py \
  build/mode00-complete-command-new-check \
  build/mode00-complete-command-20261019/prospective \
  build/mode00-complete-command-20261019/prospective-delay-corrected
```

The [frozen design](design-frozen.json) predates implementation and collection.
The initial larger design is retained as `design-before-bounded-matrix.json`;
it was reduced before execution to an orthogonal 320-case composition matrix
and 24 delay controls. The [fixture amendment](fixture-amendment.json) preserves
and explains the original wrongly parameterised 24 controls, initial-state
import mistakes and unsupported LeakSanitizer launch option. These are not
silently discarded successes. All 24 original unsupported snapshots are now
tested for atomic rejection; a separately frozen, corrected 24-case collection
tests the intended VDT domain. The 320 main cases were not rerun.

`retained-failures/` holds the exact earlier test/collector/importer sources;
these are historical source snapshots, not standalone reproduction entry points.
The final terminology-only header comment correction is preserved in
`retained-executions/`. All binding stages remain, including an explicitly
corrected chronology sentence whose two actual header hashes already agreed.
The original warning-as-error, all 336 first conformance mismatches and platform
sanitizer startup failures remain bound by the public report.

Optimized and ASan/UBSan builds each pass 16,288 rows, 241,336 exact fields,
87,048 complete OPU words and 322,802 synthetic assertions. The stream output
bytes agree across builds. The instrumentation observes zero `new`/`new[]`
calls around component operations; it is not an audit of every allocation
mechanism or a host-performance measurement. LeakSanitizer is unavailable on
this platform and is not claimed.

The full [report](../../../Docs/research/mode00-complete-command-2026-10-19.md)
and [receipt](../../../Docs/research/mode00-complete-command-2026-10-19.json)
separate functional command correctness from the still-unidentified OPU phase,
feedback pipeline, envelope, level/DAC transfer and physical service cadence.
