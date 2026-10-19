# Program-selection paths and recording association — 19 October 2026

**Normal PSS-780 numeric panel selection reaches the same factory loader as the tested MIDI Program Change path.** Twelve new original-CPU witnesses demonstrate this for Bowed Bass 65, Human Voice1 93, Musical Saw 97 and Sine 99, with empty, pending and held-note software states. This closes the concern that the earlier loading evidence might apply only to serial `C0` messages. It does not identify how the video selected presets or recover actual command arrival times.

The [JSON ledger](program-selection-association-20261019.json) binds the prospective protocol, original program identity, all 12 caller witnesses, 297 fixed source frames, 400 metadata rows and preserved pre-observation failures. Original firmware, expanded traces, source images and videos remain ignored. No audio, source timing fit, event-file correction, production change or new noise path is involved.

## Actual panel caller

The fixture starts through the original Sine 99 loader in Mode00 with neutral controllers, receive mask 1, initially disabled Reverb, melody-volume index9 and the existing mirrored-RAM/read-only-ROM bus. Pending means a received MIDI 60 on without key service; held adds one explicit key-service invocation. These are software states, not measured audible envelopes or physical key holds.

The fixture then invokes the actual decoded panel handlers: a VOICE-selector edge through `$ED12` (`$2014` bit7 with previous `$2015` clear), its release, and two numeric-key press/release edges through `$DB81`. Digits 0–4 use bits0–4 of `$200C`; digits5–9 use `$200E`. Previous-edge bytes are explicit. No direct destination-factory call substitutes for this input sequence. This models decoded input bytes, not electrical switch scanning or a complete boot.

For every target and state, the second digit follows `$DB81` → `$DB6E` or `$DB74` → `$DB36` → `$DACA` → `$DAE0`, whose observed jump reaches `$D936`. The original input-clearing helpers `$BE14/$BE3F` and slot loader `$C6EE` are visited; `$C6C3` is visited 12 times. Every complete OPU address/value sequence and relevant final state matches the already frozen direct-factory witness for the same target/state.

| Prior software state | Second-digit OPU writes | Other VOICE/digit/release stages |
|---|---:|---:|
| Empty |168|0|
| Pending MIDI 60 |171|0|
| Held MIDI 60 |171|0|

The 168-write suffix rewrites all 12 normal slots, including 24 level-code127 commands. Pending/held cases first emit the existing two release words and one key command. The matched state includes ranks, cached pitches, pending counters, shared-patch tags and working patch. This establishes command-path equivalence for these cases, including selecting Sine 99 again; it does not establish YM3420 live parameter response, oscillator phase, envelope restart, silence or output-memory clearing.

All cases contain at most one received note. No general descending-slot release policy is inferred. The earlier mixed fixture's ascending pitches and ascending slots are confounded; the separate permutation study owns that question.

## What the video establishes

The existing [PSS-780 tour](https://www.youtube.com/watch?v=ONfIvtDOog0) supplies 99 visible LCD transitions plus an initial preset 00 state. Program 0 in the fixture is inferred initialization, not an observed transition or captured Program Change message.

Before extraction, the protocol fixed three frames for **every** noninitial transition, using the existing LCD time: approximately−0.10s, the center frame, and+0.10s. No boundary was refined and no clearer replacement selected. All 297 full source frames were retained, totaling 185,833,483bytes under the declared 200MB frame limit. All 11 contact sheets were inspected.

No hand/control contact is visible in these sampled frames. That is a sparse visual observation, not proof of MIDI `C0`, absence of manual action between frames, an unedited recording or exact receiver state. LCD digits were not numerically rescored here: partial/multiplexed center glyphs remain in the retained frames rather than being forced into new preset identities. The old timeline and its uncertainty remain unchanged. The prior [mode/effect audit](recording-mode-effects-audit-20261019.md) separately establishes sampled c.00 displays.

The original MIDI has no Program Change messages. Neither its note channels nor these images identify actual selection transport. The new caller proof means that both the tested serial route and ordinary numeric panel route can enter the relevant PSS-780 loader; it does not prove which route produced this video.

## Gates at inferred selections

The fixed source association now retains all 100 inferred program rows under all four existing timing scenarios. It uses the hash-bound raw tick notes and [tick-once reference events](midi-reference-export-20261019.md). These are conditional source-file gate candidates: actual sender identity, receiver masks, arrival times and program/note ordering are unrecorded.

At every one of the 99 noninitial inferred bar boundaries, source notes end and other source notes start. Eight boundaries also have at least one gate strictly crossing the bar: presets 5,9,13,17,39,43,47,51. Thus placing a program command before versus after boundary note messages is materially different bookkeeping. The video does not recover that serial order.

For the focus selections:

| Inferred destination | Old source notes ending at bar | Source notes starting at bar | Gates strictly crossing bar |
|---|---:|---:|---:|
| Bowed Bass 65 |5|4|0|
| Human Voice1 93 |5|3|0|
| Musical Saw 97 |5|4|0|
| Sine 99 |4|4|0|

The fixed preceding250 ms interval contains a source note-off at 70 of 99 boundaries. These are **recent source offs**, not evidence of audible release tails or completed envelopes. The focus boundaries have no offs strictly inside that preceding interval; their listed offs coincide with the inferred boundary instead.

The old LCD±0.05s bracket is also retained without adjustment. Source gates cover the whole bracket at 54 transitions under the unchanged timing map and 16 under each other map. Every transition has some gate intersecting its bracket. This map sensitivity is an explicit limitation on associating the visible display with a particular delivered held-note state, not a basis for choosing an alignment. No audible held/releasing classification follows.

## Physical-key and attempt limits

The panel witnesses start physical debounce-history arrays `$24D5..$2500` at zero. Those arrays receive no writes during the observed UI sequence, while the tested virtual received-key state is cleared by the loader. This is a bounded write-set observation. It does not establish the behavior of a physically held key, later hardware polling or matrix-to-slot reassignment. A validated matrix-input fixture would be needed for those claims.

The first metadata helper failed syntax compilation before any new observation. Its original directory, source and protocol remain preserved; a fresh v2 corrects syntax with identical selections and rules. The default Python then lacked `py65` before constructing any CPU case. That failure is retained; the existing research virtual environment, interpreter binary and 29 module-source hashes were bound before the unchanged observer's single complete 12-case run. No package was installed, no failed CPU case was repaired and no source rule changed after observation.

All12 CPU cases completed without execution/comparison errors, and every bound preexisting input hash still matches. The [earlier program-load study](opu-mode00-program-load-20261019.md), frozen exporters and failed hardware comparisons are unchanged. This evidence supports a future explicitly scoped program-loading fixture; it does not authorize an audible patch-load law or default promotion.
