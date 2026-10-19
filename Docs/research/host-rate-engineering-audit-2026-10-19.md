# Host-rate engineering audit — 19 October 2026

The b13 instrument inspected in this audit has a fixed modeled FM tick rate, but **its output tone is not invariant across host sample rates**. The analog approximation, creative low-pass, fractional chorus delay and nonlinear output stages run at the host rate. This is separate from whether any of those stages accurately represents the PSS-780. The initial audit changed no production code or default and scored no source recording. A separately authorized wrapper now implements the compatibility approach described below; the underlying FM engine remains unchanged.

## Observed discrepancies

`Source/DSP/Press78Engine.cpp:251` prepares the analog model at the host rate. `Source/DSP/AnalogOutput.h:11` correctly retargets the frozen six-section transfer through a bilinear transform. That transformation preserves the underlying continuous circuit equation under its frequency mapping; it does not preserve magnitude at the same physical frequency when the sample rate changes. The existing native/MNA receipts verify the implementation, not cross-rate tonal equality.

The default tone stage adds another difference: `Press78Engine.cpp:311` computes a matched-exponential one-pole coefficient, and lines 543–547 cascade two such poles. A parameter value of 14 kHz does not have the same high-frequency digital response at every host rate. The 10 Hz DC blocker at lines573–576 contributes a much smaller unnormalized high-band gain difference.

The following new calculation evaluates only the steady-state **analog × tone 14k × DC 10** linear product, with no chorus, source resampler, drive or limiter. Entries are dB relative to its 48 kHz implementation:

| Frequency |44.1 kHz host|96 kHz host|192 kHz host|
|---|---:|---:|---:|
|4 kHz|+0.014|−0.078|−0.103|
|8 kHz|−0.043|+0.042|+0.018|
|12 kHz|−0.407|+0.936|+1.019|
|16 kHz|−1.722|+3.549|+3.890|
|18 kHz|−3.484|+6.197|+6.735|

These are differences at individual frequencies, not whole-music loudness changes. For context, this product is already about −27.79 dB at 18 kHz in the 48 kHz implementation. At 20 kHz, 96 kHz is 10.79 dB above 48 kHz, but both paths attenuate that band substantially. The calculation deliberately excludes frequencies at or above 0.45 of each host rate.

The existing [4× analog receipt](../../Tests/results/analog-oversampled.json) independently supports the diagnosis. At 48 kHz/12 kHz, the current component differs from the continuous sibling-network solution by −2.576 dB; the 4× version reduces this to −0.127 dB. Its prior reused-recording benchmark rejection does not invalidate that numerical improvement or identify the actual PSS-780 circuit. Conversely, better integration of an unverified sibling circuit does not justify changing the instrument's 48 kHz sound automatically.

The chorus delay is measured in seconds, and its LFO advances in host seconds correctly (`Press78Engine.cpp:557–571`). Its **linear interpolation** is host-dependent, however. The worst half-sample fractional delay loses 0.301 dB at 4 kHz/48 kHz, versus 0.075 dB at 96 kHz; at 12 kHz those losses are 3.010 and 0.688 dB. These are interpolation bounds, not a measured complete chorus response. Existing [Python/native parity](../../Tests/results/recorded-chorus-parity.json) proves agreement with the same per-rate algorithm. It does not prove one continuous transfer across rates, and the recorded profile was identified only over 100–4000 Hz. The allowed delay range is safe: even the conservative recorded 8 ms-depth bound is 3968.18 samples at 192 kHz, below the 4094-sample engine clamp; Studio's maximum is 3840 samples. No buffer overflow or accidental clamp was found.

The source converter has an intentional rate-dependent bandwidth (`Press78Engine.cpp:455–471,511`). Nominal 48 kHz integer samples bypass the FIR. Below 48 kHz the cutoff is `0.94 × hostRate/48000`. A separately frozen coefficient-only analysis gives approximately −1.408 dB at 20 kHz and −9.108 dB at 21 kHz for a 44.1 kHz host, versus exact unity on the nominal 48 kHz path. At 18 kHz its error is only +0.00054 dB. This is an anti-alias transition, not a hardware low-pass measurement. The coefficient analysis was not independently repeated as a new native audio render.

Finally, the drive and final soft limiter operate at host rate (`Press78Engine.cpp:549–554,581`). When active, the generated harmonics and their folding therefore also depend on host rate. This is a code-level consequence; no new nonlinear sweep was run. Drive is off in Real, and limiter activity depends on signal level. Nothing here supports adding artificial noise or a guessed DAC quantizer.

## A separate event-timing defect

The public note method mutates a voice immediately (`Press78Engine.cpp:350`), while `process()` subsequently generates every pending internal tick through the current host position (`:590–593`). At downsampling rates, some pending ticks precede that host-frame event. The new read-only native probe observes:

| Host / event at 0.1 s |First tick carrying the new note|First tick at or after the event|Difference|
|---|---:|---:|---:|
|44.1 kHz / frame 4410|4799|4800|20.833 µs early|
|48 kHz / frame 4800|4800|4800|zero|
|96 kHz / frame 9600|4800|4800|zero|
|8 kHz / frame 800|4795|4800|104.167 µs early|

Ten of 28 frozen cases backdate at least one internal tick. This is a state-time finding, not an assertion about the exact onset of the delayed, filtered output. Upsampling can defer *computation* of a tick until another host frame without changing that tick's time coordinate; those cases are retained separately. The nominal 48 kHz cases are exact.

A narrow correction would advance pending ticks strictly before an event using the old state, then apply the event at the first eligible tick. It must cover note-off, relevant controller/live-patch changes and same-frame ordering, with an explicit floating-boundary policy. Merely changing note-on is insufficient. Nominal 48 kHz would remain unchanged, but 48 kHz with clock offset/drift can change, as can voice allocation and idle policy handovers. This needs its own compatibility decision and tests; it has not been patched here.

## Proposed causal pipeline

The smallest coherent cross-rate target that preserves the established sound is a **fixed 48 kHz output reference**, not an equalizer fitted to the recording:

`variable common FM clock → existing raw FM reconstruction onto fixed 48 kHz physical time → existing 48 kHz analog/tone/drive/chorus/DC/gain/limiter → final stereo host converter`

At a 48 kHz host, keep the existing path and exact bypass of the new final converter. At other rates, both the output coefficients and chorus interpolation would then behave like the existing 48 kHz instrument, with only the declared host-conversion bandwidth differing. Analog poles and chorus LFO must stay in physical seconds; putting those stages directly into the clock-varied `synthesizeTick()` would incorrectly make the master-clock control change the analog circuit and output chorus.

The isolated [fixed-output-bus prototype](../../Tools/prototypes/fixed-output-bus-20261019/README.md) now implements and tests this architecture. It preserves all eight frozen 48 kHz complete-performance WAV hashes. The rate-scaled Kaiser converter uses 193–1153 taps, with 2.188 ms added delay at 44.1 kHz, 2 ms at 96/192 kHz and 12 ms at 8 kHz; exact 48 kHz adds no new delay. The final prospective normal-host passband covers 20 kHz. It retains the old engine's internal fractional-clock event behavior while correctly mapping host events onto the physical48 kHz grid.

The guarded instance occupies 193,816 bytes, plus 393,220 bytes of shared immutable coefficient data. A separate final hard guard preserves the ±1 software limit when enabled; limiter-off finite output remains unchanged. Raw interpolation overshoot and extreme-fixture clipping counts are reported explicitly. Local CPU, allocation and sanitizer checks pass their research gates; native Reason/AOT/Windows deployment and host latency integration remain separate requirements. The subsequently promoted public wrapper passes standalone production/prototype equivalence; its metadata-only 24 kHz ceiling correction and original failed receipt are retained. The [source-bound receipt](../../Tools/prototypes/fixed-output-bus-20261019/results.json) retains failed early timestamp and table-precision attempts, their corrections, all original test limits and independent numerical checks.

A future *physical-circuit* quality path could instead use a fixed high integration rate, such as 192 kHz, plus appropriate reconstruction and decimation. It would better approximate the documented sibling network independently of host rate, but it changes 48 kHz tone and remains a surrogate. Keep that research separate from the compatibility target. Improving chorus interpolation or oversampling creative nonlinearities likewise requires a separately versioned response; neither should silently replace the frozen recorded transfer.

Before any adoption, require exact 48 kHz legacy fixtures; deterministic event/CC/automation behavior; common-band amplitude and phase comparisons across hosts; converter image/alias controls; stereo midpoint and clock-domain checks; correct latency; and native memory/CPU/allocation limits. These are engineering gates. The uncertain MIDI/effect/circuit recording comparisons cannot substitute for them.

## Evidence and limits

The first frozen plan SHA256 is `9f9459a56fbaca81fcdd5f2b670c26fc71f28d9a02f4453dfa9be7c3838b8ec7`. It produced 41 linear-response rows and 28 read-only native event cases. A later explicit addendum, frozen before SRC calculations, produced 24 coefficient-response rows. All initial-audit outputs and source hashes are retained under ignored `build/host-rate-audit-20261019`; that initial phase changed no production source. The later wrapper promotion is documented separately above. The [JSON ledger](host-rate-engineering-audit-2026-10-19.json) contains the full rows, existing receipt excerpts, code locations, assumptions and compatibility risks.
