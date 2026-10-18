# FM fidelity audit - 18 October 2026

The engine now stops applying a D1 decrement when the envelope has already reached D1L. The next substantial hardware-identification task is to compare the four oscillator waveforms with a newly located, isolated **PSS-680 carrier-only recording**. No newly recovered source establishes the OPU's numerical envelope law, native synthesis update divider, fine-detune scale, or arithmetic widths. This audit does not support replacing those unknowns with OPL2 defaults or calling the current engine bit exact.

The audit baseline is upstream revision `82eed55541e6bf3064c43051b267e430381521fa`. The bounded D1 correction was subsequently implemented in `Source/DSP/Press78Engine.cpp` and covered in `Tests/test_dsp.cpp`; the frozen Python reference was preserved. The [JSON record](fm-fidelity-audit-20261018.json) contains the baseline and corrected source hashes, native probe output, evidence classifications and validation results. Artificial/additive noise remains absent and must not be reintroduced by a fidelity change.

## Newly acquired primary source and recording leads

The exact-model [Yamaha-hosted PSS-780 manual](https://usa.yamaha.com/files/download/other_assets/1/317511/PSS780E.PDF) was downloaded successfully with ordinary certificate-verified `curl` (the browsing service returned HTTP403 for this PDF). Its SHA256 is `e1382c76aa9f6351fb3de191228b3209def0cf4ceba54ca6a20406c1e2db0adb`; 51 pages, 3,911,928 bytes. Relevant pages were rendered and inspected from that file, rather than relying on a third-party OCR transcription. Printed p28 is PDF31, p29 is PDF32, p41 is PDF44 and p42 is PDF45.

The [PSS-780 service supplement cover](https://www.manualslib.com/manual/4045165/Yamaha-Portasound-Pss-780.html) identifies the PSS-680 as the base service documentation. That is stronger justification for examining that sibling than the unrelated OPL2/FM sound of other inexpensive Yamaha keyboards. It still does not prove identical firmware or every analog component.

A useful new controlled source is Kevin's [PSS-680 Arduino experiment, part1](https://diyelectromusic.com/2023/08/02/arduino-pss-680-synth-editor-part-1/) and its [waveform-cycling video](https://www.youtube.com/watch?v=KAHq65dWzG4). The author describes starting with the pure SINE WAVE voice, no feedback or modulation, then changing **only carrier SIN TBL** through0,1,2,3. The write cycle includes a memory dump followed by program selection, so the first sound around a change can still belong to the preceding state. This is a genuinely new acquisition lead relative to the archived polyphonic PSS-780 benchmark, and was passed to the recording audit for independent analysis. No waveform metric from this video is claimed here before decoding and checking the actual recording.

[Part2](https://diyelectromusic.com/2023/08/05/arduino-pss-680-synth-editor-part-2/) has a [second demonstration](https://www.youtube.com/watch?v=aRfAQvwq8lc), but changes several synthesis controls and is a weaker identification fixture. The author explicitly regards the detune result as inconclusive. It cannot establish the current1.5cents/DT1-step law.

## Manufacturer constraints versus implemented laws

The exact manual documents two operators with feedback, integer frequency multiples1..15 and the exceptional0=half multiple (p28); AR63 immediate attack and zero carrier decay holding while keyed (p28); four named sine-table forms, sign/magnitude DT1, DT2=+600cents, separate RR/SRR, RKS and C3-centered LKS (p41). Reverb and Sustain are separate performance states (p9/p42). None of these pages supplies a numerical envelope-rate, fine-detune, LKS or feedback transfer table.

Consequently the current constants remain distinct modeling choices:48kHz synthesis;0.75dB/TL;1.5cents/DT1;relative-to-MIDI60 fractional RKS; exponential attack; smooth linear-dB decays; RR→4*RR+2;96dB stop;6.1Hz sine LFO;10ms/VDT; floating-point phase/sine; and two-sample feedback averaging. These are discoverable, testable assumptions, not all recovered hardware quirks.

The original [MAME driver source](https://github.com/mamedev/mame/blob/master/src/mame/yamaha/ympsr16.cpp) remains explicitly incomplete and without sound. Its CPU divider is labelled guessed in the code. Neither its5.5MHz/4 CPU configuration nor an OPL-derived5.5MHz/144 calculation proves the FM sampling clock. The [OPK investigator's own account](https://www.dtech.lv/techarticles_yamaha_opk.html) also warns against a universal-family shortcut: some OPK envelopes/LFO behavior is implemented by repeated software register writes. OPK's8 channels and its approximately37.29kHz drum sample rate do not identify OPU's12-channel FM schedule.

The [PSS-580 owner's investigation](https://stereoninjamusic.weebly.com/yamaha-pss-580-specifications.html) provides a fixed triangle-LFO report and waveform images. Those remain useful sibling observations, with incompletely recorded conditions. The same page labels its bit-depth estimate as a guess. A triangle/global-LFO candidate needs a pitch-contour comparison before being made the default; arbitrary lookup quantization or random phase cannot be justified by that estimate.

## Baseline native envelope probe and implemented correction

A fresh probe compiled the current `Press78Engine.cpp` and observed its existing private envelope state without changing source or DSP. For AR63/D1L0/D2R0/RKS0 at MIDI60, the first output is1.0. The next output depends on D1R and then holds permanently:

| D1R | Held amplitude | Extra attenuation |
|---:|---:|---:|
|0|1.000000000|0dB|
|1|0.999994295|0.000049550dB|
|24|0.999693036|0.002666667dB|
|35|0.997936813|0.017939124dB|
|63|0.767696586|2.296207811dB|

The implementation explicitly preserves the old Python model's single D1 step. In this behavioral envelope, D1L is already at its target before that step. Changing a nominally zero-height stage therefore changes the held loudness and FM index, most noticeably for custom edited voices. The correction tests whether the target is already reached **before** adding D1, then advances D2 normally. It does not add OPU rate tables, clamp rules or counters. Nonzero D1 intervals retain their existing rates and ordering.

At MIDI60,96 factory carriers and36 modulators have a zero-height D1 with nonzero D1R. The largest carrier decrement is0.017939dB (program79); largest modulator decrement0.006342dB (program90). Human Voice1 and Musical Saw carriers each lose only0.00004955dB; Musical Saw's modulator loses0.00266667dB. Bowed Bass has no zero-height D1. Thus this fix cannot explain the large existing target-recording mismatch. It is an endpoint consistency correction and should be described that way, pending controlled OPU tick-order evidence.

The following contracts now cover the bounded edit:

- With D1L0/D2R0, changing D1R0..63 must not change the postattack plateau.
- With D1L0 and nonzero D2R, D2 must begin immediately after attack under the chosen model's sample ordering.
- With nonzero D1L, hold/release, all four waveforms and existing sample/block invariance must remain covered.
- A separate before/after comparison rendered all100 factory voices at MIDI36/60/84, velocity100,1second gate,2seconds total,48kHz, gain1, with circuit, tone, limiter, chorus, DC block and clock variation disabled. It reports actual differences rather than asserting hardware improvement from a software invariant.

The300 fixed-protocol renders have60 bit-identical cases. The largest change is program79 at MIDI84: relative RMS difference0.00345657 (0.346%), RMS level+0.0299716dB, maximum absolute sample difference0.000353701. At MIDI60, Bowed Bass is bit identical; Human Voice1 has relative RMS difference0.00000566215 (0.000566%) and Musical Saw0.0000394871 (0.00395%). These are software deltas against the previous engine, not error scores against hardware. Native and address/undefined-behavior-sanitized CTest each passed3/3; the DSP executable passed44 contracts in both builds. Running the new tests against the unchanged baseline engine fails exactly the two endpoint/instant-D2 contracts, demonstrating that those regressions detect the original defect.

Corrected DSP SHA256: `1d44d28a0794003e908dfee9f265f8b182fa90436b49bbcd94abc665a847bcfd`; test SHA256: `dca93b7f7eec9ced8dd85df7c9bd16890cb8fe673c5bd1fd89cd58ed7b8d5752`. Existing frozen-Python parity results describe the baseline model. New native audio intentionally diverges at the documented D1 endpoint, and those old parity results must not be represented as bit-exact evidence for this corrected engine.

A second probe confirms why replacing RKS also needs real observations: rawAR63/RKS3 takes34/20/12/1 internal ticks to complete at MIDI24/36/48/60, because the guessed pivot law makes effectiveAR lower below C3. The manual's example uses SINE WAVE with RKS0, so it does not disprove that behavior by itself. The result defines a separating future fixture, rather than licensing an arbitrary new key-scaling law.

## Substantial waveform and modulation comparison

For the new carrier-only video, retain the decoded stream and acquisition metadata separately from product assets. Inspect each state change, key/gate and effect state. Identify shape0 from a stable sustained note, then compare shapes1..3 at the same pitch and electrical path. Fit one fixed output/capture response where justified; do not normalize individual harmonics or fit a different response per shape. Compare harmonic complex ratios and zero-crossing periodicity. This can distinguish signed squared sine from a literal nonnegative sine square, half-wave polarity/period and a different zero-crossing law while reducing the influence of unknown level and capture gain. A lossy video cannot recover the exact lookup-ROM width or DAC bits from its residual floor.

For vibrato, freeze rate, depth and phase hypotheses and compare sine versus triangle, per-note versus continuous global phase on the already-used PSS-780 material. Report phase-contour error separately from magnitude/spectral-envelope error. Note-reset phase and delay-ramp behavior require different tests; simply choosing the lowest aggregate audio error does not identify either. Human Voice1's missing Reverb-dependent release remains a higher-impact unresolved state than the zero-D1 artifact, as already established in [the release evidence](reverb-release-evidence.md).

No new source supports healthy-age random ROM/register corruption, additive noise, an exact native DAC bit depth, or a specific OPL2/OPZ arithmetic pipeline. A premium implementation should expose measurable synthesis behavior and preserve a clear evidence boundary while replacing these approximations with identified laws one at a time.
