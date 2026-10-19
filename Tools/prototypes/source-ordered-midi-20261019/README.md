# Conditional source-ordered MIDI fixtures

This is an offline research prototype, outside production builds. It compiles the retained candidate SMF into two explicit same-tick track-merge scenarios. Neither scenario is an observed MIDI wire order. It does not replace historical fixtures or failed audio comparisons.

`freeze.json` was written before implementation. It fixes the raw source, old independent auditor, retained note/event metadata, inferred program timeline, factory payload source, eight historical event files, four unchanged timing maps, filter, ordering rules and validation scope. `implementation-before-export.json` binds the Python sources before any new full fixture is written. The compiler verifies the frozen input hashes before and after export.

Public synthetic tests need only Python 3.9 or later:

```sh
python3 Tools/prototypes/source-ordered-midi-20261019/test_compiler.py
```

Reproducing the retained-source experiment additionally requires the local files named in `freeze.json`, with their exact hashes. Source MIDI, full source-event ledgers, complete event fixtures and factory payloads are not included here. An output directory must be a new descendant of the ignored `build/source-ordered-midi-20261019` directory:

```sh
python3 Tools/prototypes/source-ordered-midi-20261019/compiler.py \
  --output build/source-ordered-midi-20261019/new-run
python3 Tools/prototypes/source-ordered-midi-20261019/verify_independent.py \
  --output build/source-ordered-midi-20261019/new-run \
  --receipt build/source-ordered-midi-20261019/new-validation.json
```

The validator does not import the compiler. It reparses the raw SMF with the separately authored, hash-bound old auditor, compares the old decoded artifacts and original retained notes, independently calculates each frame and event order, then reconstructs the text exports. A failed export or validation has its own receipt; existing outputs are never overwritten.

## Event contract

Each map produces `ascending_track/events.json` and `descending_track/events.json`, plus corresponding `events.txt`. JSON is the authoritative provenance ledger: it retains source tick, track, original message ordinal, source ID, raw status, channel, velocity and exact source seconds. `tick_frames` maps each distinct source tick once. The original raw message/byte ledger is `source-events.json` in the ignored run directory.

Text is a **channel-aware**, whitespace-separated research grammar:

```text
<frame> on <midi-note> <velocity> <zero-based-source-channel>
<frame> off <midi-note> <zero-based-source-channel>
<frame> patch <66-lowercase-hex-digits>
```

Frames are nonnegative integers at 48,000 Hz. Note numbers retain MIDI numbering; accepted pitches are 36–96 inclusive. Channel is the original zero-based MIDI channel, not a voice slot, receiver mask or allocation instruction. A note-on with velocity zero is emitted as `off`; JSON retains its original status and velocity. `patch` carries the existing 33-byte factory payload from the separately inferred timeline. It is not a program-change message present in the source SMF.

Consumers must parse **all fields**, preserve file order at equal frames and explicitly choose a scenario. A consumer that reads the older channel-less grammar, pitch-sorts chords, sorts OFF before ON, deduplicates same-pitch messages, or strips channel identity is incompatible. The frozen channel-aware `HardwareSequencePressure.cpp` snapshot reads these field counts, but no consumer was executed here and its routing/allocator semantics are not validated by grammar compatibility. Do not feed these files to a historical benchmark as an unannounced replacement.

The order is frame, then inferred patches first in timeline order, then source notes by original tick, declared ascending or descending track index, and original within-track ordinal. If distinct ticks collapse onto one frame, their tick order remains intact. There is no global note-off-before-note-on rule. Both endpoints use the single tick map; no note-off is computed from onset plus a rounded gate. Tempo integration and note-frame calculation use exact rational arithmetic and nearest/ties-to-even rounding. Existing map coefficients retain their exact binary64 values, rather than being silently reinterpreted as decimal rationals. Inferred program frames deliberately retain the historical floating expression and patch-first-at-equal-frame convention.

PPQN SMF format 0/1 is supported. Malformed chunks, running status, data bytes, VLQs and end-of-track markers fail closed. Identical same-tick tempos are accepted; conflicting tempos are rejected rather than choosing a track as authority. Non-note channel messages and SysEx are parsed for provenance but rejected for export because this fixture has no declared playback contract for them.

The reviewed parser also rejects meta types128–255 while preserving eight-bit opaque payloads. The initial17 tests missed this boundary; the corrected suite has19 tests. `meta-type-correction-frozen.json` records the observed defect and pre-edit bindings. `historical-first-run/` preserves the original compiler, tests and publication as archival snapshots, not relocated runners; their relative paths refer to their original locations. The original source export and validation remain unchanged. The corrected parser reproduces all eight fixtures in memory without writing replacement files.

The retained source preserves all 193 same-channel contiguous retriggers as OFF-before-ON, excludes both edges of the same 18 low notes, and retains the genuine cross-channel MIDI62 overlap. **The MIDI51 boundary at tick58368 differs by scenario:** ascending track gives OFF-before-ON; descending gives ON-before-OFF. Under a diagnostic shared pitch bitmap this yields one versus two held duplicates, respectively. These are conditional edge diagnostics, not inferred receiver behavior or sound-quality results.

See [the research report](../../../Docs/research/source-ordered-midi-2026-10-19.md) for hashes, counts and limits.
