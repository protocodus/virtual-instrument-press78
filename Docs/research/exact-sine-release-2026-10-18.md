# Exact PSS-780 final Sine Wave release — 18 October 2026

The last Sine Wave chord in the existing [PSS-780 tour](https://www.youtube.com/watch?v=ONfIvtDOog0) has a clear two-stage tonal tail: a fast fall followed by a much slower fall near 18–20 dB below its held level. This is stronger evidence for a missing release behavior than the earlier polyphonic Human Voice 1 measurement. It is still **calibration on the reused recording**, not an independent dry hardware test or a recovered OPU algorithm. No production DSP was changed.

The [complete measurement](exact-sine-release-2026-10-18.json) contains all 48 frequency/channel/window combinations, 192 fixed-window regressions, 48 descriptive bend fits, exact event frames and six source hashes. Run:

```sh
python3 Tools/analyze_final_sine_release.py \
  --reference-root /path/to/pss780-experiment \
  --artifact-dir build/exact-sine-release-new
```

Use a new ignored artifact directory; the tool refuses to replace a completed measurement. It writes a standalone plot and sampled traces there. The original recording is not copied or distributed.

## Known patch and performance

Factory program 99 has a muted modulator (TL127), sine carrier/ratio 1, AR63, RKS0, D1L0, D2R0 and RR8. Its voice Vibrato and Sustain flags are off. The existing video audit reports the separate physical Reverb and Chorus effects on. The raw voice dump does not contain that Reverb performance state; see [the earlier documentation review](reverb-release-evidence.md).

The final chord contains MIDI 75, 79, 87 and 39, all velocity 127. Using the existing affine alignment and the benchmark's rounding convention, its onset is frame 8,723,419 (181.737895833 s), and its note-off is frame 8,744,591 (182.178979167 s). No subsequent MIDI notes occur. Earlier note tails and capture processing can still contribute. The alignment is an inference from the complete recording, with local uncertainty around 50 ms; these are not measured hardware gate times.

## Fixed measurement

A complex lock-in uses each note's fixed equal-tempered frequency, a Hann window and both recorded channels. There is no frequency, timing, pitch, gain or engine-parameter fit. The main amplitude is the root mean square of the two channel magnitudes; mid, left and right are also retained separately. Each curve is expressed relative to its own median held level from −100 to −30 ms before the inferred note-off. Hann widths are 12, 20 and 30 ms, with respective half-width support of 6, 10 and 15 ms. Regression samples are spaced 1 ms apart.

The fixed fit intervals after inferred note-off are 50–120, 120–200, 200–350 and 350–500 ms. At 20 ms Hann width:

| Observable | Early 50–120 ms | R² | Late 200–350 ms | R² |
|---|---:|---:|---:|---:|
| MIDI 79, stereo magnitude | −228.718 dB/s | 0.99874 | −14.574 dB/s | 0.94095 |
| MIDI 75, stereo magnitude | −231.321 dB/s | 0.99971 | −13.589 dB/s | 0.84743 |

For MIDI 79, changing Hann width over the declared range gives early slopes −228.52 to −228.72 dB/s and late slopes −14.57 to −14.63 dB/s. The mid signal shows the same qualitative bend, with roughly −230 dB/s early and −14 dB/s late. Individual channel envelopes vary substantially with the chorus; they must not be presented as four independent envelope measurements or fitted separately to manufacture agreement.

MIDI 79 is a useful primary observable, **not an isolated stem**. Bass MIDI 39's tenth harmonic is about 6.17 Hz below it, and a previous MIDI 67's second harmonic coincides with it. The pure-carrier patch makes strong high harmonics unlikely in the ideal source, but analog/capture nonlinearity and previous tails are unmeasured. MIDI 75 supplies corroborating evidence in the same chord/capture. MIDI 87 is an octave above 75 and can share its second harmonic; MIDI 39 has few cycles in the short analysis windows. Both remain diagnostic rows rather than decisive independent checks.

## Descriptive bend and competing explanations

A separate, explicitly searched two-line regression describes the recorded curve. It fits 50–400 ms with a continuous bend searched from 90–180 ms in 0.5 ms steps. For the 20 ms MIDI 79 stereo-magnitude curve, the best bend is 124.5 ms after the inferred gate, at −18.36 dB relative to its pre-off level. The fitted slopes are −227.85 and −15.53 dB/s. MIDI 75 bends at 127 ms and −18.67 dB. These are descriptive calibration results; the bend time moves with gate-alignment error, and the level is not proof of a chip's internal threshold domain.

The existing RR8/RKS0 equation predicts 724.077 dB/s, much faster than the early captured slope. Multiplying its duration by three predicts 241.359 dB/s; applying the same duration law to raw RR4 predicts 15.085 dB/s. Both are close to the measured stages, with about 5% residual for the primary curve. They were not tuned to remove that residual. Other rate mappings, quantized schedules and capture processing remain possible.

The new early RR8 measurement also resembles the −230 to −233 dB/s RR8 release in the separate [controlled PSS-480 demonstration](recording-holdout-audit-2026-10-18.md). That sibling observation has its own capture/Reverb/gating ambiguity. Agreement at one rate does not identify the full RR, D1/D2, RKS or attack law.

Yamaha's TX81Z documentation supplied an earlier −18 dB envelope-Reverb analogy. The original PSS-780 owner's account separately attributes Reverb to envelope modification. The newly observed bend makes that mechanism more plausible. A simple constant-ratio downward compressor on a single linear-dB release would not by itself create this early-fast/late-slow bend; dynamic gain, upward processing, external reverb, overlapping partials or an internal nonlinear envelope still need separating evidence. No matched Reverb-off/on capture exists here.

## Consequence for the engine

The [frozen Reverb-cap experiment](reverb-envelope-benchmark-2026-10-18.md) tests the bounded threefold/RR4/18 dB hypothesis without changing factory bytes, the shipped engine or the recording alignment. It improves all three metrics over the extended final Sine chord, but has broad preset regressions and unresolved voice-pressure/endpoint effects. This supports further work on a distinct Reverb release state; it does not justify shipping one global timing multiplier or claiming Human Voice 1's release is solved.

The fixed-window results, event alignment, raw-patch identity, source hashes and formulas were independently reproduced. That verifies the analysis implementation. It does not upgrade the capture to a controlled experiment or establish a chip specification.
