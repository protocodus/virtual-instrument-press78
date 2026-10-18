# Audible-event alignment audit - 18 October 2026

The original affine MIDI mapping is early relative to the observed audible onsets in all 18 fixed cases examined here. In the final Sine Wave 99 passage, measured 50% onset transitions occur approximately40-63 ms after the frozen MIDI times; the final release first falls 1 dB below its projected held level approximately45-48 ms after the frozen note-off. This is strong evidence that an event-relative plot must retain tens of milliseconds of delivery/alignment uncertainty. It does **not** recover the actual MIDI-interface timestamps or establish one exact offset, affine-scale correction or envelope delay.

No benchmark alignment, old scores, DSP, presets, package or host state was changed. No synthesized attack or release was used as a timing template. The [JSON ledger](midi-alignment-audit-20261018.json) retains every selected case, failed short-window measurements, the frozen protocol, posthoc diagnostics, source hashes and plots.

## Fixed observation protocol

The source is the already acquired [PSS-780 preset tour](https://www.youtube.com/watch?v=ONfIvtDOog0), its known Eugenia MIDI events, the existing raw 33-byte factory voices and the frozen program timeline. The mapping remains:

`audio seconds = 0.8906462238832541 + 0.9998070138348876 * MIDI seconds`.

Before reading audio, the protocol selected patches 5 Toy Piano, 18 Celesta, 88 Glockenspiel and 99 Sine Wave, MIDI notes 72 or higher, at least 0.10 s after their inferred program boundary, with at least 0.25 s since the previous same-pitch MIDI note-off. Both operators have raw AR63 in these patches. The three comparison voices use sine carriers, integer carrier multiples and weak high-ratio modulation; Sine Wave mutes its modulator. Patch 99 is the cleanest test. AR63 is documented as immediate in Yamaha's exact-model manual, but RKS behavior, prior notes, effects and the capture chain remain uncertainties in other patches.

There are 18 selected notes at 16 unique onset times. Simultaneous notes are not independent deliveries. All cases were retained; none was replaced after hearing or plotting its result. The arithmetic stereo mid channel was demodulated at the nominal carrier frequency using centered Hann windows of 12, 24 and 48 ms. This is frequency-selective amplitude measurement, with no native engine render, audio correlation, pitch fit, onset-alignment optimization or spectral score.

Median amplitudes over frozen-onset [-120,-70] ms and [+70,+110] ms define the pre/post step. The first persistent 10%, 50%, 90% crossings are searched over [-80,+140] ms. The primary observation is the 24 ms /50% crossing. Nonpositive steps, missing crossings and after/before contrast below 2 fail. The centered window has temporal support on both sides; crossing times are observations of a filtered amplitude step, not the first nonzero DAC sample.

## Observed onset residuals

Positive means the audible transition occurs later than the frozen mapped event.

| Voice | Notes / unique onset groups | Primary median | Primary range |
|---|---:|---:|---:|
| Toy Piano 5 | 3 /3 | +23.22 ms | +22.21 to +25.16 ms |
| Celesta 18 | 2 /2 | +33.76 ms | +27.42 to +40.10 ms |
| Glockenspiel 88 | 4 /3 | +45.71 ms | +37.32 to +55.73 ms |
| Sine Wave 99 | 9 /8 | +53.96 ms | +39.83 to +63.39 ms |

All18 primary measurements pass their declared contrast test. Four 12 ms Sine measurements fail it because ongoing neighboring tones leak into the short window; their false early crossings remain in the JSON. They must not be averaged into a delivery-time estimate. Across accepted 50% observations at different window lengths, the largest range for any selected note is2.94 ms.

Representative Sine Wave observations:

| MIDI note | Frozen onset | Primary residual |
|---:|---:|---:|
|77|175.783172 s|+39.83 ms|
|72|176.665354 s|+41.34 ms|
|77|177.768081 s|+53.96 ms|
|75|179.091353 s|+63.39 ms|
|75|180.855717 s|+60.99 ms|
|79|181.737898 s|+62.44 ms|
|87|181.737898 s|+60.57 ms|

The final two notes share one source onset; their 1.88 ms difference shows the limits of interpreting filtered partial transitions as exact event timestamps. The Sine onset group residual grows by 21.67 ms between its first and last selected groups, over approximately5.95 s. A constant local offset therefore does not explain every observed onset within millisecond precision. Sender scheduling, playback articulation, capture timing, effects and frequency-selective measurement remain possible contributors. No interpretation is uniquely established.

A **posthoc** numerical method check uses abstract unit sine steps at 523, 698 and 1244 Hz with eight starting phases and a persistent tone two semitones lower, at amplitudes 0, 0.25, 1. The24 ms half-crossing error is at most 4.85 ms over these conditions; 48 ms reduces it below 0.39 ms. This is a method sanity check, not an instrument/capture model or a guarantee under arbitrary polyphony. It cannot explain the full positive 22-63 ms pattern.

## Final release: observed departure, not delivered note-off

This audit evaluates the last source gate with the continuous affine mapping, giving 182.178989328624 s. The benchmark constructs its event frame by separately rounding the onset and gate, giving 182.178979166667 s at 48 kHz. Those conventions differ by about 10.2 microseconds; they are not identical frame conventions. This negligible difference does not explain the millisecond residuals below. The first fixed diagnostic fits a continuous held/release two-slope line to demodulated log amplitude over [-120,+150] ms, trying data breakpoints without using an RR model. It returns approximately+40 ms for MIDI 79 and +32 ms for 87 across the Hann lengths. The plots show why that single-break estimate is not an accurate gate detector: both captures have a later flattening tail, and the 87 fit is biased earlier while trying to represent that second bend with one line. This failure remains visible; a low residual or stable window result alone does not validate the change point as note-off.

A disclosed **posthoc** sensitivity check projects each partial's held dB trend fitted over frozen-off [-120,0] ms, then measures persistent departures below it. With the 24 ms window:

| Final note |0.5 dB departure|1 dB departure|3 dB departure|6 dB departure|
|---:|---:|---:|---:|---:|
|79|+44.99 ms|+47.79 ms|+57.26 ms|+70.45 ms|
|87|+42.21 ms|+45.21 ms|+53.32 ms|+63.53 ms|

The 1 dB departure across all windows is +45.97 to +47.79 ms for 79 and +42.86 to +45.49 ms for 87. Window smoothing, output/capture dynamics and the finite physical release slope affect these times. They prove a substantial late **audible amplitude departure**, not a 50 ms hidden OPU release-stage timer. The measured onset and release departures also do not support treating the MIDI-file gate as an independently verified physical gate duration.

## Why no new global mapping is adopted

The observations support revising the confidence attached to the frozen alignment. They do not yet identify one best affine replacement. There are only four patches at four narrow regions of the performance, with no similarly controlled mid-performance set. Different raw key scaling, carrier frequency, modulation and capture behavior are partly confounded with absolute time. The 16 unique event groups are clustered and cannot be treated as 16 independent clock measurements.

A descriptive, posthoc Theil-Sen slope of unique onset residuals is approximately+208 ppm relative to the old mapping. Its formal confidence interval is not a physical clock interval: the independent/exchangeable-error assumption is unsupported here. The selected Sine groups alone vary too quickly and nonuniformly for that global trend to explain them. That diagnostic is preserved rather than used to change the mapping, tune a model or improve a score.

Optical LED transitions from the existing timeline only identify visible program changes, at video-frame resolution. They do not show delivered note-on/off edges, and the audible program policy is inferred. They are not a substitute for a MIDI log. The 32-frame model latency trim is 0.667 ms at 48 kHz; it is model bookkeeping, not a measurement of the sender, interface or recording delay.

For release-law research, retain explicit uncertainty around mapped gate edges and measure local plateau/decay behavior from the recording itself. A stronger global mapping needs a fixed dense set of instant-attack events spanning the full performance, with separating cross-patch checks or actual sender/MIDI timestamps. It must be validated independently before replacing the old score protocol; no model-specific local alignment should be introduced.

All scripts, audio-source references, full measurements and plots remain under ignored `build/midi-alignment-audit-20261018`. Source recording audio was read in place and was not copied into shipping assets.
