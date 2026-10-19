# RKS0 release slopes across the final Sine chord - 19 October 2026

The higher MIDI 87 component decays faster than MIDI 79 in every fixed comparison of the arithmetic-mid and stereo-pair curves: 18 slow-tail cells and 12 early-release cells. The longer slow-tail interval retains the difference across 20/40/60 ms tapers. This challenges a strictly pitch-independent **audible** release at raw RKS0 in this capture. It does **not** recover the YM3420's RKS law or prove the difference belongs to its core envelope generator. Reverb, Chorus, overlapping notes, harmonic ambiguity and the capture chain remain material.

No DSP, presets, alignment, prior scores, package or host state was changed. The finalized global-event-mapping report and tool remain byte-identical. The [JSON ledger](rks0-release-slopes-2026-10-19.json) preserves all 240 fits, every contrast, separate channels, diagnostics, hashes and fixed protocols.

## Frozen measurement

The source is the same [PSS-780 tour](https://www.youtube.com/watch?v=ONfIvtDOog0), read from the original retained 48 kHz PCM16 file. The factory Sine Wave 99 dump has carrier RKS0, AR63, D1R1, D1L0, D2R0, RR8 and SRR5; its modulator TL127 mutes modulation. The documented capture inspection has Reverb and Chorus on, with Vibrato and Sustain off. Raw voice flags and physical performance effects are distinct evidence; neither proves the unknown Reverb implementation.

The final source-MIDI off is sample 8744591, or 182.178979166667 s under the frozen rounded event convention. Actual delivery is uncertain. All observations retain that same reference, with no local correction.

Before fitting, the following windows were frozen exactly as requested, in seconds after that off:

- Early: [0.05,0.10] and [0.05,0.12].
- Slow: [0.30,0.60],[0.60,1.00] and[0.30,1.10].

The protocol SHA256 is `56760185e95728abf482e9a31d16870d5de09e33632c5141534c0f33505bb4cb`.

The estimator reproduces the finalized forensic method: simultaneous sine/cosine least squares at nominal frequencies for MIDI 39,46,58,59,67,75,79,87 plus DC, with Hann applied to both basis and signal. Tapers are 20/40/60 ms, with 2 ms hops. There is no frequency, phase, timing, RKS or synthesis-parameter search. Ordinary least-squares regression of measured amplitude dBFS against time supplies each descriptive slope, R² and residual error. Overlapping windows are not independent observations, so their regression statistics are not physical confidence intervals.

Left, right and arithmetic mid are measured separately. A fourth curve uses the per-partial amplitude `sqrt((left²+right²)/2)`. This stereo-pair measure avoids cancellation in the arithmetic mid and reduces simple redistribution between channels. It does not recover the dry operator or remove every Chorus/capture gain change.

## Fixed-window results

Representative 40 ms stereo-pair slopes, in dB/s:

| Window after mapped off | MIDI 39 | MIDI 75 | MIDI 79 | MIDI 87 |
|---|---:|---:|---:|---:|
|0.05-0.10 s|-195.022|-231.745|-233.546|-288.011|
|0.05-0.12 s|-195.583|-230.628|-228.547|-268.534|
|0.30-0.60 s|-14.185|-15.848|-16.337|-18.056|
|0.60-1.00 s|-13.370|-13.251|-13.134|-17.930|
|0.30-1.10 s|-13.838|-14.038|-14.285|-17.844|

MIDI 87 is steeper than 79 in **all 18** slow combinations of three windows, three tapers and two composite channels. The 87-minus79 slope difference ranges from -4.834 to -0.561 dB/s. It also retains that sign in **all 12** early combinations, with differences -61.110 to -38.349 dB/s. No unfavorable cell was removed.

For the longer 0.30-1.10 s interval, stereo-pair slopes across 20/40/60 ms are:

| Partial |20 ms|40 ms|60 ms|
|---|---:|---:|---:|
|39|-13.793|-13.838|-13.858|
|75|-14.031|-14.038|-14.043|
|79|-14.290|-14.285|-14.293|
|87|-17.819|-17.844|-17.880|

The 40 ms mid slopes over the same longer interval are -13.969, -14.162, -14.556 and -17.830 dB/s. Thus 87's faster slow decline survives a longer interval and either composite, rather than depending only on one small early window. The 40 ms pair difference 87-versus79 is 3.559 dB/s; their corresponding R² values are 0.9969 and 0.9935.

Early slopes depend on window and taper: 87's 40 ms pair fit changes from -288.0 to -268.5 dB/s when extending the end from 0.10 to 0.12 s. That interval includes a transition toward the slower branch and is not an isolated recovered constant-rate segment. These measurements must not be converted directly into a replacement RR mapping.

## Chorus and channel dependence

Individual channels give a much less stable story. Across the nine slow window/taper cells, 87 is steeper than 79 in 9/9 left-channel cells but **0/9 right-channel cells**. Right-channel 87-minus79 slope differences are +8.246 to +39.060 dB/s, the opposite sign. For example, the 40 ms long-window right-channel slopes are approximately -27.970 dB/s for 79 and -13.348 for 87.

The observed left/right amplitude ratio varies by approximately 27 dB for 79 and 32 dB for 87 over the 40 ms long-window analysis. This makes a single channel's fitted decay a poor proxy for an operator envelope. In contrast, the mid-minus-pair level difference spans about 0.51 and 0.55 dB there, with slopes -0.271 and +0.014 dB/s for 79 and 87. Mid cancellation alone therefore does not explain the retained 3.3-3.6 dB/s composite pitch contrast. Both composites nevertheless still contain a moving output effect and unknown capture processing.

A fixed scalar gain at each frequency changes level, not a sustained log-amplitude slope. Time-varying Chorus, dynamics, Reverb or other frequency-dependent processing can change the slope; no direct-output/effects-off reference separates those mechanisms here.

## Cycles, floor and overlap

The 20 ms fit contains only 1.56 cycles of MIDI 39; 40/60 ms contain 3.11/4.67 cycles. Weighted-basis condition numbers are 10.10, 4.17 and 2.87. Bass instantaneous levels ripple substantially with the shortest taper: its stereo-pair R² over 0.30-0.60 s is 0.394 at 20 ms, improving to 0.970 at 60 ms. Its longer-window slope is more stable, but it is a weaker short-window constraint than the higher components.

For 79/87 in all slow composite fits, the minimum observed R² is 0.9548 and the lowest measured level remains about 36 dB above the same-frequency empirical post-extinction reference at off+2.2 to +2.8 s. That reference is an observed floor, not a stationary-noise model or evidence of DAC resolution. Partial signal RMS versus the total weighted fit residual has a minimum median ratio of about 5.3 dB. The residual also contains unmodeled sidebands, frequency drift and other signal, so this is a descriptive quality ratio, not isolated-noise SNR.

MIDI 87 is exactly an octave above 75 and may contain 75's second harmonic. MIDI 75 can likewise contain an eighth harmonic of 39. In the fixed 40 ms stereo-pair slow interval,87/75 is about -3.75 dB. Over the predeclared off+1.45 to +1.60 s gap, after 87's observed extinction but before 75's, that ratio is approximately -37.32 dB; in the arithmetic mid it changes from about -4.19 to -43.09 dB. A fixed proportional contribution from 75 alone would not produce that separate loss. This does not bound an amplitude-dependent nonlinear harmonic or unknown processing during the earlier tail, and it does not identify each spectral component as one voice.

The source-MIDI history adds another limit. 75 is retriggered at the final chord while its preceding 75 ends at that same onset; 39's previous same-pitch note-off is approximately 0.441 s before the final chord. Their earlier release voices may overlap. 79 and 87 have cleaner same-pitch histories, which is why 87-versus79 was the frozen primary contrast. Same-pitch histories, harmonic relationships and the raw patch are retained explicitly in the JSON.

## Supported next step

The recording requires more than one pitch-independent audible decay slope at raw RKS0. It remains unclear whether that comes from minimum hardware key scaling, performance Reverb, voice history, the output effect or capture dynamics. A static multiplier of every envelope rate cannot explain the measured cross-pitch differences by itself, but this experiment does not establish any alternative rate law.

A discriminating capture should hold the same independently authored pure-carrier patch and gates while varying pitch, then toggle Reverb and Chorus independently. Avoid octave-related simultaneous notes and provide long gaps to remove old voices. Until then, preserve the current law as an explicit assumption and keep this pitch dependence visible when evaluating fixed envelope hypotheses.

## Verification and artifacts

All 36 old forensic slope rows reproduce within 7.2e-15 dB/s, confirming identical extraction. An independent direct-OLS calculation recomputes all 240 new slopes within 1.2e-13 dB/s; stereo-pair identities and mid-coefficient linearity also pass. Original source hashes and the finalized global-mapping sentinels are unchanged.

Ignored artifacts are under `build/rks0-release-slopes-20261019`: frozen protocol, analysis/verification scripts, complete curves and results, MIDI history, quality receipt and two plots. The result SHA256 is `3bb1a23229b2550357175eb167c4983732b56e7be04b133e7f7f9b459646cd1e`. No source recording or new audio demo is distributed by this measurement-only pass.
