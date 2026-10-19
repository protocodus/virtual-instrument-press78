# Broader Sine99 pitch-pattern test — 19 October 2026

The broader test is **inconclusive under its frozen gates**. It does not establish a stable note-class/octave pattern beyond the [known long MIDI 67/75 interval feature](pitch-grid-audit-20261019.md). None of eight new G/D♯ contrasts has the required combination of control-passing estimators and AAC/Opus agreement; the apparent-octave test also lacks its required estimator coverage. This is a limit on these measurements, not evidence that the hardware has no frequency grid.

Two additional repeated intervals survive narrower per-estimator checks and remain useful conditional constraints. Neither identifies an oscillator law or justifies a pitch lookup, FNUM width or per-note correction. The previously committed pitch-grid audit remains unchanged.

This pass changes no production DSP, preset, alignment, previous score, historical artifact, package or host state. It acquires no media and adds no artificial noise. The [JSON ledger](pitch-pattern-audit-20261019.json) retains the frozen selection, every result and failed estimate, controls, codec discrepancies and provenance. The reusable [analysis tool](../../Tools/audit_pitch_pattern.py) reproduces the experiment into a new output directory.

## Selection and calibration frozen before new estimates

The retained [PSS-780 tour](https://www.youtube.com/watch?v=ONfIvtDOog0) has 56 source-MIDI notes in the final Sine99 section, beginning at mapped time 175.562626441590 s. All 1,779 MIDI events are available for note history. The original affine mapping is used only to select times; it is not corrected or fitted here. This is reused polyphonic/effect audio, not a fresh hardware holdout.

Metadata-only selection takes every Sine99 event with onset at least program start +0.6 s and gate at least 0.20 s. Its protected interval is onset +0.10 s to off −0.06 s, with a minimum duration of 0.05 s. The eight early program-guard exclusions are retained. Equal protected windows are deduplicated. Every selected note held throughout an entire window is measured there, permitting simultaneous contrasts without a local timing fit.

The result is **48 selected note events, 26 shared windows, 82 note/window observations and 105 simultaneous pairs**. Of those events, 29 had not previously received a frequency measurement; the selection adds 14 distinct pitches absent from the old 19-window set. Protected windows range down to about 60.5 ms. Those short windows remain subject to explicit baseline-bias gates rather than being assumed precise.

All old 19 events stay marked as previously measured. Their frequencies are not treated as new holdout evidence when reused in a new shared window. The only fixed pitch-pattern calibration is the already known G-minus-D♯ contrast: the median of the negative original two long 67/75 Opus-mid phase12 interval errors, **+0.477254026064 cents**. No other note-class table is fitted.

The main extension asks whether that same contrast appears at other octaves. It has eight primary anchor contrasts: new G43/G55 against D♯63; new D♯39/D♯51 against G67; and final D♯39 against G79. A primary anchor window must be created by one of the pair's own events. Other nested windows are retained as sensitivity observations. There are also 19 primary same-class octave contrasts. These are spectral components in a mixture, not automatically identified individual voices.

The protocol SHA256 is `d7c45ea6c1ef07e47dae4eaf48ac8c5b2323b080c213086985a626a4e799dcf8`; it was frozen before extracting any new frequencies.

## Estimators, controls and declared gates

All four methods run on every observation in left, right and arithmetic mid:

- Hann spectral peak with the prior ±75-cent nominal search, at least 16× zero padding and bounded energy refinement.
- Fixed 6 Hz and 12 Hz fourth-order zero-phase complex demodulation, with 0.5 s actual context on each side and amplitude-squared weighted unwrapped-phase slopes at 1 kHz. The Hann estimate supplies only the demodulation center.
- A joint local least-squares phase method, `joint120`: fixed 120 ms Hann windows, 2 ms hops, simultaneous nominal sine/cosine bases for all 22 Sine99 pitches plus DC. Hann weights both basis and signal; a precomputed pseudoinverse estimates their coefficients. The target complex coefficient is demodulated at its nominal frequency and its phase slope estimated. There is no basis-frequency or synthesis-parameter fit.

Both phase families exclude amplitudes below 0.2 times their interval median and require at least 16 retained phase samples. Search-boundary and other failures remain in the result. The joint basis condition number is 3.09584, so its nominal separation is not numerically singular. Joint fitting reduces contamination from *different* basis frequencies; it cannot separate a higher fundamental from an exactly coincident lower harmonic or distinguish old and new same-pitch voices.

The sources are the original PCM16 decode, existing float Opus 251 and AAC 140 decodes, and the existing selected b11 full-performance WAV. AAC drops the prior frozen 627-frame encoding lag; native b11 drops its declared 32-frame latency. There is no new alignment, normalization or render. Both codecs derive from one upload master and are not independent hardware recordings.

Four analytical controls are generated without noise or effects: isolated equal-tempered target tones; a stationary 22-tone equal-tempered ensemble; that ensemble uniformly shifted down 2 cents; and a gated ensemble following all 56 Sine99 note events with fixed phase resets and rectangular gates. The gated control tests leakage/history sensitivity, not a recovered hardware envelope. Stationary phase rules are deterministic. Native b11 mid separately tests the actual composition through the current engine/effect implementation.

For each pair and estimator, **every analytical control and native b11 mid must have absolute interval bias ≤0.10 cents**. Accepted captured contrasts additionally require AAC-minus-Opus interval disagreement ≤0.05 cents. These are conservative fixed gates; a failing stress control does not prove the corresponding captured estimate wrong. Gates were not relaxed when they excluded the desired comparisons.

A primary window needs Hann plus at least one phase/joint estimator that passes those gates. Every qualifying estimate in both encodes must give positive G−D♯ contrast >0.20 cents and agree with the fixed +0.477254-cent prediction within 0.15 cents. Overall support requires at least three nonoverlapping evaluated anchor windows, at least two new MIDI pitches and no evaluated-window failure. The octave test similarly requires qualified estimator families, all apparent octave errors within 0.15 cents, and coverage of three pitch classes and three nonoverlapping windows. Old same-pitch releases and possible integer harmonics are independently flagged rather than silently discarded.

## Screening outcome

There are 1,312 media/control note rows, 5,248 estimator outputs, 6,720 pair/source/channel/estimator rows and 420 pair/estimator gate decisions. **117 estimator outputs are invalid** and remain in the ledger.

| Estimator | All-pair control passes, of 105 | All-pair control + codec passes | New G/D♯ control passes, of 8 | New G/D♯ control + codec passes |
|---|---:|---:|---:|---:|
|Hann|17|11|2|0|
|Phase 6 Hz|42|23|4|0|
|Phase 12 Hz|27|15|2|0|
|Joint120|71|25|8|0|

There are 157 control-passing and 110 codec-passing pair/estimator cells overall, with 74 passing both. However, all 16 control-passing cells belonging to the eight primary G/D♯ contrasts fail codec agreement. Thus **zero primary G/D♯ windows are evaluable under the declared family rule**. The original long-pair codec agreement does not transfer automatically to these shorter, lower or mixed-history components.

The table below shows joint120 because all eight of its primary comparisons pass the analytical/native bias controls. These are disqualified captured measurements, not accepted evidence for a tuning law:

| MIDI pair / shared-window start | G−D♯, Opus cents | AAC cents | Absolute codec difference |
|---|---:|---:|---:|
|43/63; 176.545 s|+0.547372|+0.342105|0.205266|
|55/63; 176.545 s|+0.494721|+0.439427|**0.055294**|
|39/67; 179.191 s|+1.542757|+1.200993|0.341763|
|51/67; 179.191 s|+0.547202|+0.481063|0.066139|
|39/67; 180.074 s|+1.017143|+1.091993|0.074851|
|39/67; 180.956 s|+1.224233|+1.038509|0.185723|
|51/67; 180.956 s|+0.311517|+0.414400|0.102883|
|39/79; 181.838 s|+0.725749|+0.818688|0.092939|

The 55/63 discrepancy narrowly misses the 0.05-cent codec gate; it is not rounded into eligibility. Opus estimates for 43/63 and 55/63 are close to the known prediction under several methods, but their control/codec failures prevent accepting that apparent agreement. Larger and time-dependent MIDI39 deviations cannot be adopted as low-octave tuning corrections either.

## Apparent octaves and conditional repeated intervals

The octave extension has 29 control-passing estimator cells, but only three also pass codec agreement. At one anchor window, 56→68 gives +0.05951 cents in Opus and +0.03757 in AAC under joint120. At that same window, 58→70 gives −0.02602/−0.05717 cents under phase6 and −0.02538/−0.03755 under joint120. These small apparent octave errors are consistent with replication in that mixture, but there is no qualified Hann family. **Zero octave windows meet the frozen evaluation rule**, so there is no broader octave result to accept.

Higher members of these pairs can also contain lower-note harmonics. Even perfect apparent octave replication would not uniquely identify separate oscillator voices or their core tuning. A two-second harmonic lookback and a separate two-second same-pitch release-clear flag preserve this ambiguity. The only release-clear primary G/D♯ window, the early G43/G55 versus D♯63 window, still fails the required gates; the later comparisons also contain old-voice concerns.

Two exact MIDI-pair repetitions survive the narrower per-estimator control and codec gates. Their full ranges satisfy the predeclared 0.20-cent descriptive repeat threshold:

| Pair / qualified method | Opus errors at epochs 1/2, cents | AAC errors at epochs 1/2 | Opus / AAC repeat range |
|---|---:|---:|---:|
|56→62; phase6|+0.309310 / +0.296524|+0.305053 / +0.340954|0.012786 / 0.035901|
|68→72; joint120|−0.288758 / −0.456277|−0.311062 / −0.439137|0.167519 / 0.128075|

The 56/62 windows start at 177.868080737268 and 178.750262455539 s; the 68/72 windows start at 177.647535307700 and 178.529717025971 s. The respective windows are nonoverlapping. Each pair has **only one qualified estimator family**, and the 68/72 windows are especially short. These are conditional captured-frequency constraints for future independently chosen hypotheses, not independent demonstrations of a note-class table. No arbitrary lookup is fitted to them.

## MIDI34 identification failure

The expected MIDI34 fundamental is 58.270470 Hz. In both declared windows, Hann hits the **lower edge of the frozen ±75-cent band** in every captured channel for PCM16, Opus and AAC. Its derived 6/12 Hz estimates are therefore marked invalid. These account for 54 invalid captured estimator outputs; the remaining 63 invalid outputs arise in analytical ensemble controls. Native b11 has valid Hann estimates in the same MIDI34 windows.

This establishes only a failure to identify the expected captured component within that band. There was **no wider-band search or silent pitch reassignment**. Simultaneous MIDI46 is an octave above 34, so its approximately 116.54 Hz component cannot by itself distinguish a genuine 46 voice from a 34 harmonic or octave-folded output. Received-note range, true-voice range, routing, transposition and folding require independent documentary or controlled-recording evidence before changing the engine. The frozen failed observation is retained for that separate investigation.

## Reproduction and limits

The reusable tool verifies frozen source hashes and refuses a nonempty output directory:

```sh
OPENBLAS_NUM_THREADS=1 python3 Tools/audit_pitch_pattern.py \
  --protocol build/pitch-pattern-audit-20261019/protocol-frozen.json \
  --out build/pitch-pattern-reproduction-new
```

Its completed reproduction gives bit-identical frequencies, interval/common-offset metrics, eligibility and support decisions. Seven minimum-amplitude diagnostics differ by at most 2.91e-15 dB; the receipt discloses that rounding instead of claiming total bit identity. An independent arithmetic/metadata/provenance checker reconstructs selection and all 420 gate decisions, recomputes all pair metrics exactly and verifies all source hashes. This is independent arithmetic plus reproduction of the same estimator implementation, not an independently implemented signal estimator.

The first extraction completed all rows but could not serialize absent codec differences as NaN. Its script and log are preserved. Only absent-difference representation changed to `null` with false qualification before rerunning the unchanged protocol. No window, threshold or hypothesis was revised. The initial overly strict reproduction check is likewise preserved with its disclosed amplitude-roundoff correction.

Ignored artifacts live under `build/pitch-pattern-audit-20261019`, including both attempts, the immutable protocol/result, tool reproduction, verification receipt and two inspected figures. The result SHA256 is `114a6eec5e0bbb49451a806f10962e2ee9dcf3cd760f538b7cd7fb189a099175`. The public JSON embeds the result and binds the artifact hashes; no recording is distributed.

The experiment narrows what these references can support. The earlier long 67/75 discrepancy remains a useful captured ratio, while the broader low/short-note material is too control- or codec-sensitive to identify a stable global pitch pattern at the declared precision. Reverb, residual analog Chorus in mid, old voices, harmonic ambiguity and shared-master processing remain unresolved. A hardware frequency hypothesis should face the retained conditional intervals and failures; it should not be manufactured from them. Direct effects-off, isolated long notes across octaves remain the discriminating evidence.
