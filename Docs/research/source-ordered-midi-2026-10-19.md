# Conditional source-ordered MIDI compiler — 19 October 2026

The new compiler preserves source-message order and maps each source tick to one sample frame. All193 same-channel contiguous retriggers therefore remain same-frame OFF-before-ON across the four existing timing maps. This is a **new conditional research fixture**, not a repair of the historical benchmark or a reconstruction of the unrecorded sender's MIDI wire timing. No audio was rendered, no timing or gain was fitted, and all historical inputs and failures remain unchanged.

**The two track-merge scenarios differ at MIDI51, tick58368.** Ascending-track order produces OFF-before-ON. Descending-track order produces ON-before-OFF. A diagnostic shared pitch bitmap consequently sees one held duplicate in the ascending scenario and two in the descending scenario. The extra descending duplicate is an intertrack ordering assumption, not an interval overlap or a recovered delivery fact. Both scenarios retain the genuine cross-channel MIDI62 overlap at tick40704: channel1 ends at40896, channel0 at41184. Neither merge scenario is established as the actual transmitted order, and acceptance of both channels by the recorded instrument remains conditional.

The [machine-readable ledger](source-ordered-midi-2026-10-19.json) binds the [public code and synthetic tests](../../Tools/prototypes/source-ordered-midi-20261019/README.md), protocol, source, independent validation and eight new ignored event fixtures. The original media, full event ledgers and factory payloads remain outside published files.

## Frozen inputs and conventions

The design was saved before compiler implementation or export in `Tools/prototypes/source-ordered-midi-20261019/freeze.json`, SHA256 `9fc2d7ba82b09f1d259c91c76a204355f9be3499cb14502471a57f5793f8ee42`. Its27 inputs include the original source, previous auditor and decoded metadata, the existing inferred timeline, the factory payload source, the historical exporter and all eight old event files. Every input hash matched before and after the experiment. Code hashes were recorded separately before export; output directories and receipts refuse overwrite.

The retained Mutopia Eugenia candidate is15,128bytes, SHA256 `7ab6f4551b8116590d52dd0566c3f5a7fad89097eb1b64ddf97b60fba47167cf`. It is format1, three tracks,384ticks/quarter, with3,576 total messages and1,779 notes. The two identical initial tempos are882,352microseconds/quarter; rational integration gives exactly `22665417/125000`seconds, or181.323336seconds. The [prior source audit](midi-event-order-audit-2026-10-19.md) explains why these retained bytes are a plausible candidate but not proof of the actual transmitted2017 sequence.

The unchanged maps remain:

| Map | Offset, seconds | Scale |
|---|---:|---:|
| Unchanged |0.8906462238832541|0.9998070138348876|
| Old scale / median offset |0.9327535031570672|0.9998070138348876|
| Nominal scale / median intercept |0.9129181334157996|1.0|
| Equal-patch robust affine |0.9158456466155656|0.9999670078976708|

Tempo integration is exact rational arithmetic. Each distinct source tick is evaluated once with the exact binary64 values of those existing map coefficients, then rounded nearest/ties-to-even. On and off messages at the same source tick share the same frame. Off frames are never formed by adding a rounded gate to a rounded onset. Both merge scenarios preserve within-track ordinal; they never reorder chord notes by pitch or impose a global OFF-before-ON priority. Distinct ticks that collapse onto one frame retain their original tick order.

The existing100 program-timeline entries are separately inferred, absent from the SMF. Their existing floating-point mapping expression is retained, and inferred patches sort before notes at equal frame. This is an explicit fixture convention, not evidence that a program command preceded a MIDI message on a wire. Conflicting same-tick tempos and unsupported non-note MIDI fail closed instead of silently introducing a new ordering or playback policy.

## Source and validation results

Mode00 scope retains pitches36–96 inclusive on both original channels. This keeps1,761 notes and excludes18 low notes: pitch29×2,34×13 and35×3, all channel1. Both endpoints of every excluded note are filtered. Each of the eight fixtures contains3,522 retained note edges and100 inferred patch entries,3,622events total.

| Diagnostic, identical across four maps | Ascending track | Descending track |
|---|---:|---:|
| Same-channel contiguous retriggers, same-frame OFF-before-ON |193|193|
| Within-track source-order inversions |0|0|
| Same-channel held duplicate-ons |0|0|
| Global-pitch held duplicate-ons |1|2|
| Global-pitch unheld offs |1|2|
| Keys left held |0|0|

Global-pitch counts are Boolean MIDI-edge diagnostics that ignore program-reset behavior. They are not a simulation of the original allocator and do not establish how many audible notes are suppressed. The MIDI62 overlap explains one duplicate in both scenarios; the MIDI51 same-tick boundary explains the second in descending order. There are no same-channel source overlaps, and filtering does not remove either cross-channel case.

All17 initial synthetic tests passed. They cover original chord order, running status and velocity-zero offs, exact tempo changes, duplicate/conflicting tempos, positive and negative rounding ties, endpoint rounding, collapsed-frame tick order, explicit intertrack alternatives, patch-first ties, inclusive note-range filtering, retained cross-channel collisions, malformed input rejection and non-overwriting output boundaries. Eleven malformed SMF cases and unsupported non-note messages are intentionally rejected. These initial checks missed the meta-type validation gap described below.

The independent validator passed150,557 checks. It does not import the new compiler: it invokes the frozen, separately authored old auditor on the raw SMF bytes, compares every message identity/byte span/status/payload against the new source ledger, compares the retained original note metadata, independently calculates rational frames and both merge orders, reconstructs all eight text exports, and rechecks all27 historical input hashes. Its first-run sources and successful results remain preserved; they do not certify parser cases that were not tested. Expected rejection cases remain in the synthetic tests.

## Review correction: seven-bit meta-event types

Independent review found that the first parser accepted a meta-event type of128. The [SMF specification transcription, section2.3](https://midimusic.github.io/tech/midispec.html) requires the type byte to be below128, while opaque payload bytes retain all eight bits. Its acknowledgement identifies the International MIDI Association text, updated by David Back in1999; it is not an official-certified copy. The [official specification index](https://midi.org/standard-midi-files) was accessible, but its linked PDF contents were not inspected through the tool. The correction ledger preserves those access limits.

The invalid acceptance was reproduced before editing. Original compiler/tests and both first report files are archived unchanged under `historical-first-run/`; a separate `meta-type-correction-frozen.json` binds them and the observed witness before the fix. The parser now rejects high-bit types. Two added tests cover every invalid type128–255 and valid opaque payloads containing high-bit bytes, bringing the synthetic suite to19 passing tests. An in-memory comparison confirms the source ledger and all eight compiled fixtures are identical to preserved `run-01`; none of its19 files was changed or regenerated. The original27 inputs still match. This is a parser-boundary correction, not a new source-order experiment or an independent audio result.

## Consumption and limits

The ignored exports are under `build/source-ordered-midi-20261019/run-01`. Their JSON ledgers retain source tick, track, message ordinal, channel and raw status. Text uses the explicit channel-aware grammar `frame on note velocity channel`, `frame off note channel`, or `frame patch hex33bytes`. A consumer must retain channel fields and equal-frame line order. Channel-less parsers, global OFF-first sorting and pitch sorting are incompatible. The frozen channel-aware sequence snapshot reads these field counts, but it was not run and its downstream routing semantics were not revalidated here. A new experiment must name its scenario and consumer contract before using these fixtures.

This work does not recover sender scheduling, serial-byte spacing, receipt times, channel masks, MIDI transformations, gain, output latency, envelope state or voice assignment. It does not select a preferred timing map or track merge. No production code, historical exporter, event fixture, score, preset, audio, UI, host or PR was changed. The earlier negative audio gates remain negative; eliminating the known fixture artifacts is not evidence of better audio agreement. A future audio experiment needs a separate frozen protocol and must retain the historical baseline.
