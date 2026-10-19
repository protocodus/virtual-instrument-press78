# Research command audio consumer, 19 October 2026

The verified normal Mode00 command frontend now has an isolated route into the existing Press78 DSP. This is a research integration, with one allocator and twelve fixed voice slots. It does not establish a bit-exact YM3420 renderer, change the shipping engine, or select an audible hardware correction.

The optimized and ASan/UBSan runs pass 1,290,419 assertions each, and an independent asymmetric-slot witness passes another 528 assertions. Four independently authored, isolated-note cases, one per waveform table, produce exactly equal floating-point output against the unchanged shipping engine. A fifth case intentionally differs: overlapping same-pitch releases stack in the shipping allocator, whereas the Mode00 command path reuses its cached fixed slot. That difference demonstrates a policy consequence of the command route; it is not evidence for the chip's phase, envelope or amplitude laws.

## Scope and sources

The [frozen design](../../Tools/prototypes/command-audio-consumer-20261019/design-frozen.json) was bound before consumer implementation, compilation, execution or new WAV files. It binds the unchanged shipping engine and the previously reviewed command helpers. Its SHA256 is `8980465c531f64b882ca95bb15444c16d43fdf823418d5d79445e935fdba506b`.

The [complete command frontend research](mode00-complete-command-2026-10-19.md) supplies exact ordered OPU words for its accepted ordinary Mode00 operations. Its original-CPU command validation remains separate from this synthetic audio integration. The extracted `FirmwareLevel.h` command math is reused; the failed amplitude/audio candidate from which it was extracted remains unadopted. No original firmware or recordings were decoded or rerun for this consumer experiment.

The actual [shipping engine](../../Source/DSP/Press78Engine.cpp) supplies Voice, Envelope, waveform helpers, feedback, LFO, resampling and output processing unchanged. The consumer uses the existing private `Press78SustainTestAccess` friend seam in a standalone research translation unit. It never routes its commands through `Engine.noteOn`, `noteOff`, `setPatch`, `allSoundOff`, or a second note allocator. The shipping `noteOn` API appears only in the unchanged comparison baseline.

This layer makes no new inference from a generic Yamaha patent or another chip. The official [PSS-780 owner's manual](https://usa.yamaha.com/files/download/other_assets/1/317511/PSS780E.PDF) and the retained original-program evidence are provenance for the preceding command frontend. They do not prove the inherited audible laws used here.

## One frontend, fixed slots, explicit epochs

[CommandAudioConsumer.h](../../Tools/prototypes/command-audio-consumer-20261019/CommandAudioConsumer.h) owns one committed `Mode00CompleteCommands`. Every ordinary operation previews that owner on a temporary copy, preflights the entire ordered plan against a staged register image, then applies it and commits the prospective frontend only on success. The temporary copy is discarded on rejection and is never an independently advancing allocator.

The engine's existing twelve Voice objects are fixed physical slots. The consumer never creates steal tails. The raw operator bytes, selected feedback/PMS/pitch bytes, per-field validity, paired key state and last accepted plan retain their original values/order. All words of one accepted plan occur at one caller epoch: no audio advances between them and no serial bus interval is invented. Thus the intermediate carrier RR15 remains in the trace even when an immediately following key-service call gives it no audible duration.

The caller supplies key-service and vibrato-service invocations separately. Audio samples do not decrement the frontend's vibrato delay. Its delay counts invocations, with no guessed millisecond cadence. A normal integration calls this consumer's event methods; feeding `applyRaw` from a second independently advancing frontend would violate the ownership design.

`applyRaw` is a deliberately narrower research fixture boundary. It validates register-domain support and mapped-note ranges, but trusts caller-supplied original mapped notes. Those notes are not independently authenticated against another cache. `Plan.slot` and `Plan.edge` are retained trace annotations; ordered writes and supplied notes alone drive this raw boundary. Their values are not interpreted as allocation commands. Ordinary event methods supply notes directly from the prospective sole frontend owner.

## Register interpretation and remaining hypotheses

The supported register subset is the complete normal frontend subset of OPU `0200–02ff`: `0208` paired key commands, `0218–021d` PMS/AMS, `0220–0225` feedback/normal mode, `0228/0230/0238` pitch groups, and the six operator groups `0240/0260/0280/02a0/02c0/02e0`, including carrier and odd-slot displacements. Unsupported addresses, holes, reserved normal-mode bits, individual-operator key combinations, plans over 204 words, non-OK plans, incomplete key-on prerequisites and invalid mapped notes reject before any authoritative mutation. Peripheral `0327` remains excluded.

A genuine raw off-to-on key edge calls the existing `Voice.configure`; a repeated on-to-on key word retains phase, feedback and envelope state. Key-off enters the existing release path without deactivating the voice or clearing output history. Live parameter words call the existing coefficient update while preserving phases, feedback samples, envelope attenuation/stage/finished flags and voice ticks. TL127 follows the current gain endpoint, without a panic or output-memory reset.

TL low seven bits are already compiled for original key-level scaling and volume. Therefore native LKS is neutral and native velocity is one. The current TL-to-amplitude law and TL>=99 mute endpoint remain hypotheses. Native Sustain is false: each commanded RR nibble is used directly, rather than selecting SRR a second time. Native vibrato delay is zero and native Vibrato is enabled; the frontend's actual PMS word provides the one delay gate. AMS and operator AM enable are retained.

The pitch bridge decodes FNUM and block from the actual three ordered pitch words. Its frequency is the shipping empirical hypothesis `floor(FNUM * 2^(block-3)) * 5500000 / (6 * 2^24)`, followed by the existing multiplier/detune equation. Those constants and the 48 kHz native synthesis cadence are inherited modeling choices, not new measurements of the OPU. Original mapped note supplies the existing native RKS formula. The chip receives FNUM/block; this test does not identify a silicon keycode or prove that MIDI-note RKS law.

Initialization requires an explicit empty, silent frontend snapshot, zero pending/keyed/delay state, allowed stable controls and the explicit `StoreReverbBitWithoutAudioEffect` policy. This is not an original hardware boot. Operator and pitch fields begin unknown and require a preload before key-on. Reverb's raw TL high bit is retained and exposed as unsupported audio; it creates no new effect or release law. Comparison renders keep Reverb off. Host pitch and clock modulation are disabled to avoid a second pitch stage; modulation and output controls otherwise reuse the shipping implementation.

Other inherited uncertainties remain: waveform ROM/arithmetic, phase reset/retrigger, native feedback delay/cadence, envelope rate/endpoint laws, downstream DAC transfer, live-register transients, supply sensitivity, Reverb and physical scheduling/bus timing. This integration does not resolve them.

## Synthetic checks and short comparison material

[consumer_test.cpp](../../Tools/prototypes/command-audio-consumer-20261019/consumer_test.cpp) distinguishes exact command/state checks from inherited audio equivalence. It uses independently authored working patches, no factory bank or recording data. It checks exact note-on/key-service/off words, intermediate RR15, unknown-register rejection, all twelve fixed slots, state-preserving TL127/restore/wave/RR/PMS/CC64 writes, invocation-only VDT, ignored-audio Reverb storage, program output-history continuity, malformed-plan atomicity including identical subsequent audio, and sample-chunk invariance. Measured command/application and process regions call neither `new` nor `new[]`; initialization, fixtures and file I/O are outside that measurement. This observation is not a general allocation proof.

The optimized and sanitized executions use C++17 strict warnings, with ASan/UBSan and `ASAN_OPTIONS=detect_leaks=0`. LeakSanitizer is not claimed. The initial builds and tests have no failures; receipts preserve their exact source boundaries. A later runner hardening checks all nine expected frozen input sizes/hashes before compilation. Its valid-input check passes, and an intentionally corrupted hash in a separate constructed protocol copy rejects before compilation; that expected negative test is retained separately. The original protocol and first optimized/sanitized receipts remain unchanged. No prior failed audio adoption gate was changed or bypassed.

Five two-second stereo Float32 WAV pairs were exported once under the ignored [frozen-01](../../build/command-audio-consumer-20261019/frozen-01/) directory, with `A.wav`/`B.wav` names and a separate [key](../../build/command-audio-consumer-20261019/frozen-01/key.md). Independent file verification confirms IEEE Float32 format, stereo, 48 kHz, 96,000 frames, finite samples and the declared exact/different cases. A is always the unchanged shipping baseline; B is this command route. Cases 01–04 use each of the four tables with matching neutral controls and nonoverlapping releases. Their output must be byte-exact. Case 05 uses a long enough release to expose same-pitch fixed-slot reuse. Same controls and no post-render gain, EQ, phase or time fit are applied. Since overlap level is the subject of that case, its RMS and peak remain unmatched and are reported directly. No listening preference or production promotion is selected.

The in-memory case-05 result differs in 80,608 of 96,000 stereo frames. A has RMS `0.017854740811329033`, peak `0.064063265919685364`; B has RMS `0.014663732820739987`, peak `0.036796011030673981`. These are synthetic model outputs, not hardware benchmark scores.

Reproduce synthetic verification without writing WAVs using Python 3.9+ and Clang:

```sh
python3 Tools/prototypes/command-audio-consumer-20261019/run_validation.py \
  --output build/command-audio-consumer-20261019/new-validation
```

The output directory must be new. This command rejects changed frozen engine/helper inputs before compilation, retains compile/test failures, binds sources before execution, and leaves any previously frozen WAV material untouched. Add `--verify-inputs-only` to check the frozen bindings without compiling or running DSP.

## Status

The consumer passes optimized/sanitized checks and independent source review. The independent witness covers all twelve slots with asymmetric operator fields, all selectors, twelve non-table FNUM/block values reaching actual Voice steps, a full 204-word plan, paired-key atomic rejection after a valid prefix, and continued native dynamics through carrier TL127. The one-time WAV export is complete and frozen. The adjacent [machine-readable report](command-audio-consumer-2026-10-19.json) binds the sources, receipts and WAV hashes. There is no production DSP, default preset, host, UI, original recording benchmark or audible hardware-fidelity promotion in this change.
