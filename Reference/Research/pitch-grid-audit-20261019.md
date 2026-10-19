# Captured Sine99 pitch ratios — 19 October 2026

The simultaneous MIDI 67/75 interval is about **0.48 cents narrower than equal temperament** in this PSS-780 recording. It repeats across both original long-note epochs, the Opus and AAC encodes, four estimators that pass the frozen control gates, and every fixed arithmetic-mid half-window. The existing native b11 render and stationary equal-tempered controls do not reproduce that discrepancy. A common tuning or recorder timebase shift changes both pitches together and cannot alone explain their interval ratio.

This is a captured pitch-ratio feature, **not an identified hardware frequency grid**. The anomaly was already known when this experiment was designed. Both encodes share one upload master; actual analog Chorus need not cancel perfectly in the arithmetic mid. Unknown output/capture processing, Reverb, prior voices and frequency-dependent effects remain possible causes. No oscillator clock, FNUM law, arithmetic width, DAC rate or per-note tuning correction is recovered or adopted.

No DSP, presets, alignment, previous scores, historical artifacts, package or host state was changed. No new media was acquired or artificial noise added. The [JSON ledger](pitch-grid-audit-20261019.json) contains every observation, the frozen protocols, control failures, arithmetic checks and provenance.

## Frozen primary experiment

The source is the retained [PSS-780 tour](https://www.youtube.com/watch?v=ONfIvtDOog0). This pass reads its historical 48 kHz PCM16 decode, the previously acquired float Opus 251 and AAC 140 decodes, and the existing b11 selected full-performance WAV. The AAC read drops exactly 627 leading frames from the separately frozen codec audit; the b11 read drops only its declared 32-frame engine latency. There is no new audio alignment, gain normalization, parameter fit, native build or render.

The historical `v5_clock_reference.py`, `clock-protocol.json` and `clock-report.json` remain unchanged. All **19 original** metadata-selected Sine99 windows are retained: MIDI 60–87, gate at least 0.4 s, onset at least 0.6 s after preset selection. Each window starts 0.15 s after the mapped onset and ends 0.08 s before its mapped off. Gates at least 0.8 s form the original primary group. These rules are retained from the old experiment, not newly optimized for the observed pitches.

The two primary simultaneous pairs share exactly the same window for their two pitches:

| Epoch | Events / pitches | Source window, seconds | Duration |
|---|---|---:|---:|
|1|1760/1761; MIDI 67/75|179.241353314675–180.334625892082|1.093272577407 s|
|2|1770/1771; MIDI 67/75|181.005716751217–181.657898469489|0.652181718271 s|

The first and second halves of each primary window were declared before measuring. They add eight note windows, yielding **27 note windows per source/channel**. They are nested sensitivity observations, not independent samples or a new holdout. No interval was moved or selected after seeing a result.

The protocol was frozen before the new frequency estimates with SHA256 `88bae82db039165170a335b4bab0e511eeaa0395e185990e2fc2f0db4cec1108`.

Five estimators run on every window and mid/left/right channel:

- The original Hann spectral peak: at least 16× zero padding, a ±75-cent nominal search and bounded sinusoidal-energy refinement within two FFT bins of the selected peak.
- The original 12 Hz phase method: 0.5 s of actual context on each side, fourth-order zero-phase low-pass complex demodulation, unwrapped phase sampled at 1 kHz, and an amplitude-squared weighted slope. Samples below 0.2 times median demodulated amplitude are excluded from that slope.
- The same phase procedure with fixed 6 and 24 Hz cutoffs.
- The same bounded spectral method with a Blackman taper.

All estimates and diagnostics are retained, including estimators that fail a control. The original PCM16 implementation reproduces **all 57 historical window/channel observations exactly** for both original estimators, without executing the old script's artifact-writing entry point.

## Controls and acceptance rules

Three analytical stationary controls cover every fixed window: an isolated equal-tempered target at amplitude 0.1; fifteen simultaneous equal-tempered tones at amplitude 0.02 each; and the same multitone grid shifted uniformly down 2 cents. The tone set is MIDI 39,46,51,53,56,58,59,62,63,67,68,70,75,79,87, with deterministic phases. Tones are continuous through the window and its context, with no gates, effect or added noise. These test peak/phase-estimator bias and cancellation of common mistuning, not the original instrument's output path.

Estimator eligibility depends only on controls: every original primary interval must have absolute bias at most 0.05 cents in all three stationary controls **and in native b11 mid**. For an eligible estimator, the captured-feature check requires both original epochs in both float encodes to have mid interval error below −0.2 cents. Codec agreement separately requires the primary Hann and 12 Hz phase AAC-minus-Opus interval differences to stay within 0.05 cents. These thresholds were frozen; none was relaxed after measurement.

Interval error is `cents(MIDI75) − cents(MIDI67)` relative to the nominal 800-cent interval. The descriptive common offset is their mean. These are not estimates of an internal master clock.

| Estimator | Max stationary primary bias, cents | Max native-mid primary bias | Control gate | Captured original-mid interval range |
|---|---:|---:|---|---:|
|Hann spectral|0.001079|0.001454|Pass|−0.495819 to −0.449426|
|Phase 6 Hz|0.000247|0.003538|Pass|−0.490244 to −0.460603|
|Phase 12 Hz|0.000501|0.000471|Pass|−0.489705 to −0.464514|
|Phase 24 Hz|**0.050040**|0.000413|**Fail**|−0.489222 to −0.463235|
|Blackman spectral|0.000577|0.002180|Pass|−0.497688 to −0.445718|

The 24 Hz phase control misses the 0.05-cent threshold by approximately 0.000040 cents. It remains in the ledger and plot but is excluded from accepted evidence; rounding does not make it eligible. All four eligible estimators pass the frozen captured-feature check. The result contains 405 note/source/channel rows, 2,025 frequency estimates and 450 original/nested pair-estimator rows. None is invalid at its nominal search boundary.

## Common mistuning versus the simultaneous interval

Representative original-window 12 Hz phase results in arithmetic mid:

| Source | Epoch | MIDI 67 offset, cents | MIDI 75 offset | Interval error | Common offset |
|---|---:|---:|---:|---:|---:|
|Opus 251 float|1|−1.480627|−1.969144|−0.488516|−1.724885|
|AAC 140 float|1|−1.480209|−1.969913|−0.489705|−1.725061|
|Native b11|1|+0.000340|−0.000131|−0.000471|+0.000105|
|Opus 251 float|2|−1.483694|−1.949685|−0.465992|−1.716690|
|AAC 140 float|2|−1.487628|−1.952142|−0.464514|−1.719885|
|Native b11|2|+0.000314|+0.000673|+0.000359|+0.000493|

The capture's common offset is about −1.72 cents; MIDI 75 is a further approximately 0.48 cents lower relative to MIDI 67. A uniform sample-rate or tuning multiplier cancels exactly from this simultaneous interval. The stationary uniformly −2-cent control confirms that cancellation for these estimators. This rejects common mistuning **alone**, rather than identifying the source of the remaining difference.

AAC-minus-Opus interval differences are −0.002648 and −0.008032 cents for Hann across epochs 1/2, and −0.001188 and +0.001478 cents for 12 Hz phase. Thus the fixed codec-agreement check passes. This makes a difference peculiar to one of these two output encoders less likely; it cannot exclude processing already present in their common upload master.

All 19 original windows are kept as descriptive checks. In Opus mid under 12 Hz phase, pitch medians range from about −1.410 cents for MIDI 62 to −1.977 for MIDI 63, with one to four observations per pitch. These were taken at different times, durations and voice histories. They are not enough to fit a universal note table or to separate pitch from time and effect phase.

## Window and channel sensitivity

The fixed first/second halves retain the negative mid interval:

| Source | Epoch 1 first / second half, cents | Epoch 2 first / second half |
|---|---:|---:|
|Opus 251; phase 12 Hz|−0.47259 / −0.49488|−0.50859 / −0.47248|
|AAC 140; phase 12 Hz|−0.46299 / −0.49868|−0.50034 / −0.45293|

Individual channels are less stable. In the original full windows, the Opus left interval errors are −0.72006 and −0.38027 cents, while right gives −0.43645 and −0.33818. More seriously, the **first half of epoch 2 in right becomes positive**: +0.13141 cents in Opus and +0.11804 in AAC. Left halves can reach roughly −3.7 cents. These failures rule out a claim of invariance across every channel/window combination.

The native render also shows substantial signed single-channel interval error despite an essentially equal-tempered mid. Its original left values are −0.39552 and +0.64803 cents, and some native half-windows deviate still further. This provides a direct control that phase modulation and windowing of a Chorus output can resemble pitch error. The actual recording's analog wet path need not have identical gain, phase or cancellation in mid; native mid cancellation does not prove that the captured mid is the dry oscillator. The current render is also not a complete model of the hardware's performance Reverb and unknown capture chain.

## Separately frozen exploratory full-period endpoint control

After completing the primary study, a separate extension tested the parent's proposed separation of periodic Chorus phase from a pitch ratio. Its protocol was frozen before extraction, SHA256 `d2e1402e7db2e9819b12bc91c1818356332f39c43b125b1065fac0a8d7d473b2`. It does not change the primary criteria or add a new acceptance gate.

The extension uses only the first long primary pair, beginning at its declared start 179.241353314675 s, for exactly `1 / 0.9546467517767424 = 1.0475078851301263 s`, ending at 180.288861199805 s. That period is the fixed RecordedChorus model assumption supplied for this control, not a newly fitted frequency or a recovered exact hardware period.

At fixed 6/12 Hz demodulation cutoffs, it compares unwrapped phase **endpoints**, rather than an OLS slope that weights interior effect phases. The existing whole-window Hann estimate supplies only the complex-demodulation center. Phase is retained at 48 kHz and interpolated at the exact declared endpoint times; no new frequency/time fit is performed. The same codec/latency trims apply. All mid/left/right results are retained with amplitude diagnostics.

| Source | Cutoff | Mid interval error, cents | Left | Right |
|---|---:|---:|---:|---:|
|Opus 251|6 Hz|−0.479341|−0.463134|−0.498178|
|Opus 251|12 Hz|−0.483513|−0.455688|−0.493824|
|AAC 140|6 Hz|−0.485863|−0.489326|−0.496034|
|AAC 140|12 Hz|−0.483246|−0.470256|−0.483641|
|Native b11|6 Hz|−0.002240|−0.003437|−0.009415|
|Native b11|12 Hz|−0.000842|+0.001272|−0.000705|

This reduces the large single-channel spread while retaining a captured discrepancy around −0.48 cents in every channel. Across the 36 note/filter/channel observations, the minimum demodulated amplitude is −9.007 dB relative to its interval median; no interval portion falls below 0.2 times that median. Thus an observed near-zero demodulated amplitude does not explain these particular endpoint results.

A full period cancels a **strictly periodic** phase perturbation only if the assumed period and its stability apply to the actual captured wet path. Amplitude changes, nonperiodic modulation, filter/context effects, Reverb and shared-master processing can still contribute. The extension strengthens the captured-ratio observation but remains posthoc and cannot localize it to the hardware oscillator.

## Verification, limits and next evidence

A separate arithmetic/provenance script recomputes all 450 interval/common-offset rows exactly from the matched note estimates, rechecks eligibility and codec rules, and confirms all source hashes. It reproduces all 57 historical PCM16 observations exactly for both original estimators. The extension has its own arithmetic/provenance check for 36 note and 18 pair rows; all frequency, cents and pair calculations agree exactly. These receipts independently check arithmetic and provenance, **not independent signal extraction**.

Ignored artifacts under `build/pitch-grid-audit-20261019` contain both frozen protocols, analysis and verification scripts, complete numerical results, the original primary phase curves and two inspected plots. The primary result SHA256 is `91598316304b9f87ed2eed14a6ba769d1fd50648a89bf7996484e73b04e37f8e`; the separate endpoint result is `b0cb16033c61b41b9d81ce1fef5d8fca60f16748aa0fa29ee2654d5e2e5dd3fa`. The public JSON embeds these results and preserves the artifact manifest. No media file is distributed by this audit.

The useful new constraint is a small, repeated simultaneous interval compression that a common tuning shift and the tested estimator biases cannot explain. Its origin remains unresolved. A direct output capture of independently authored pure-carrier notes, with Chorus/Reverb independently switched off and on, long voice-clearing gaps, and several non-octave simultaneous pairs would distinguish an oscillator grid from the effects/capture path. Until such evidence exists, keep the current tuning law explicit and avoid encoding these two known pairs into a per-note correction table.
