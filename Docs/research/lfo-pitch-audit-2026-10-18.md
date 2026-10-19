# PSS-780 vibrato pitch audit — 18 October 2026

The inspected recording supports a roughly **5.24 Hz triangle LFO**, with substantially deeper Musical Saw pitch modulation than Press78's current 6.1 Hz sine and PMS depth table. This is quantitative evidence from pitch trajectories, separate from the existing magnitude-spectrum benchmarks. It does not identify every PMS level, the digital clock divider, or the exact note/reset behavior. No DSP, preset, UI, or host files were changed by this audit.

The [machine-readable record](lfo-pitch-audit-2026-10-18.json) freezes the protocol, every input/source hash, all 54 main score rows, synthetic estimator tests, and frequency sensitivity. Source audio, extracted curves, code, and figures remain local in the ignored `build/lfo-audit-20261018` directory. Native DSP was snapshotted after the bounded D1 correction; `Press78Engine.cpp` SHA256 is `1d44d28a0794003e908dfee9f265f8b182fa90436b49bbcd94abc665a847bcfd`. The engine still used the previous modulation defaults at that snapshot. Artificial noise was neither added nor used in the analysis.

## Documentary evidence

Yamaha's [exact-model PSS-780 manual](https://usa.yamaha.com/files/download/other_assets/1/317511/PSS780E.PDF), printed p9/PDF12, describes voice-specific delayed vibrato. Its voice format on printed p41/PDF44 exposes separate PMS, VDT and enable fields. It does not provide a numeric LFO rate, waveform, phase-reset rule, depth table or delay-step duration. PDF SHA256: `e1382c76aa9f6351fb3de191228b3209def0cf4ceba54ca6a20406c1e2db0adb`. The relevant effects page was rendered locally and visually checked.

The original [PSS-580 owner investigation](https://stereoninjamusic.weebly.com/yamaha-pss-580-specifications.html), updated 21 July 2023 and rechecked for this audit, reports a fixed triangle LFO with editable modulation depth and delay. This is an original sibling observation, with insufficiently recorded measurement conditions to establish an exact PSS-780 clock or phase law. It is consistent with the new target-recording result; it is not the measurement used to calibrate it.

## Recording, selection and estimator

The source is the already-used [PSS-780 preset-tour recording](https://www.youtube.com/watch?v=ONfIvtDOog0), decoded to 48 kHz stereo PCM16 in the external experiment workspace. Its polyphonic *Eugenia* performance has the existing globally frozen MIDI arrangement alignment:

`audio_seconds = 0.8906462238832541 + 0.9998070138348876 × midi_seconds`.

This was an exploratory selection after initial pitch inspection of the already-observed material. The subsequent protocol was frozen before fitting the reported model. It provides different-preset evaluation, **not a new, blinded hardware holdout**. No recording clips are redistributed.

Each trace uses arithmetic stereo mid, complex heterodyning at the nominal equal-tempered note partial, a sixth-order zero-phase Butterworth baseband low-pass, complex downsampling to 500 Hz, and the derivative of unwrapped phase converted to cents. Absolute note starts come from the unchanged global MIDI mapping; there is no onset adjustment. The word *partial* refers to an integer multiple of the played MIDI frequency, not necessarily the carrier multiplier.

| Role | Preset / MIDI | Partial / base frequency | Baseband cutoff | Scored note age |
|---|---|---|---|---|
| Sole calibration | 93 Human Voice 1 / 82 | 2 / 1864.655 Hz | 40 Hz | 0.38–0.98 s |
| Primary evaluation | 97 Musical Saw / 72 | 3 / 1569.753 Hz | 130 Hz | 0.40–1.60 s |
| Contamination check | 97 Musical Saw / 72 | 1 / 523.251 Hz | 130 Hz | 0.40–1.60 s |
| Low-confidence diagnostic | 65 Bowed Bass / 72 | 4 / 2093.005 Hz | 40 Hz | 0.65–1.60 s |
| Short phase diagnostic | 95 Whistle / 77 | 2 / 1396.913 Hz | 40 Hz | 0.43–0.56 s |
| Short phase diagnostic | 94 Human Voice 2 / 79 | 2 / 1567.982 Hz | 40 Hz | 0.31–0.56 s |

All named patches have Vibrato enabled in the published factory dump. PMS is 3 for the calibration and diagnostics and 6 for Musical Saw. The raw VDT values are respectively 24, 21, 39, 31 and 21. These byte values are not separately captured live settings. The video visibly includes effects; reverb, chorus, overlapping notes, tails, capture and codec remain confounds. The original global arrangement alignment also has local residuals of tens of milliseconds.

## One calibration; frozen other-preset predictions

For each candidate waveform, **only Human Voice 1** fits four shared parameters: rate, initial phase, PMS3 peak depth and tuning. No evaluation note or partial receives its own depth, tuning, phase, rate or gain. The phase is anchored to Human Voice 1's globally mapped note onset. Global phase advances from that epoch; reset phase restarts the same calibrated phase at each new note.

| Human Voice 1 calibration | Rate | PMS3 peak | Tuning | Pitch RMSE |
|---|---:|---:|---:|---:|
| Sine | 5.231058 Hz | 10.09354 cents | −1.98537 cents | 0.93546 cents |
| Triangle | 5.233705 Hz | 12.46597 cents | −1.96875 cents | **0.51085 cents** |
| Current uncalibrated default | 6.1 Hz | 10 cents | 0 cents | 12.80535 cents |

The triangle's calibrated initial phase is 0.5176157032 rad. A fairer fixed-rate comparison also allows the old 6.1 Hz sine to fit phase, depth and tuning on the same Human Voice 1 window. It still has **5.71863 cents RMSE**, versus 0.51367 cents for a fixed 5.240 Hz triangle with those same three nuisance parameters. The rate mismatch therefore cannot be explained merely by choosing a more favorable initial phase.

The present PMS table predicts a PMS6/PMS3 peak ratio of 4. A binary doubling candidate predicts 8. This corresponds to the candidate nominal table `[0, 3.125, 6.25, 12.5, 25, 50, 100, 200]` cents, multiplied by a **single** PMS3 calibration; it is not a separately fitted Saw depth. With the triangle fit, Saw's predicted peak is 99.72773 cents.

| Frozen Musical Saw partial3 prediction | Reset phase RMSE | Global phase RMSE |
|---|---:|---:|
| Sine, current PMS ratio4 | 37.14782 cents | 40.79434 cents |
| Triangle, current PMS ratio4 | 36.60449 cents | 38.53238 cents |
| Sine, binary PMS ratio8 | 13.77710 cents | 27.79353 cents |
| Triangle, binary PMS ratio8 | **11.99411 cents** | 21.15499 cents |
| Current 6.1 Hz sine, nominal40-cent depth | 71.53214 cents | — |

The deep Saw oscillation supports changing the current ratio4 hypothesis. It does **not** recover the six untested PMS depths: 0/1/2/4/5/7 remain unidentified by this comparison. The PMS6 nominal100-cent and PMS3 nominal12.5-cent candidate is supported at those observed levels, with residual capture/partial contamination and uncertainty still present.

## Phase law and rate precision

The clean Whistle phase diagnostic strongly favors the continuous global candidate at the frozen Human Voice 1 calibration: **1.05728 cents RMSE global versus 13.23803 reset**. Its simultaneously played MIDI74 carrier partial corroborates this result: 1.15332 versus 13.25774 cents. The two independently filtered note trajectories agree within 0.52289 cents RMS over the fixed 0.13-second interval. They are simultaneous notes in one recording, not independent recording sessions.

Human Voice 2 also favors global, 6.53869 versus 12.50464 cents, but is visibly more contaminated. Bowed Bass has low agreement with either phase law; its noisy partial and overlapping harmonic content are insufficient to identify its vibrato depth or contradict the cleaner traces. The audit does not fit Bowed Bass separately to conceal that failure.

The sole calibration contains only about three LFO cycles, so its last reported decimals are optimizer output, **not millihertz hardware accuracy**. Small fixed-rate changes, each refitting only the Human Voice 1 phase/depth/tuning, materially affect global extrapolation:

| Fixed triangle rate | Human Voice 1 RMSE | Saw global RMSE | Saw reset RMSE | Whistle global RMSE |
|---|---:|---:|---:|---:|
| 5.230 Hz | 0.51181 | 30.96139 | 11.73984 | 1.60199 |
| 5.233705 Hz | 0.51085 | 21.15499 | 11.99411 | 1.05728 |
| 5.240 Hz | 0.51367 | **9.75415** | 12.47459 | **0.48518** |
| 5.245209 Hz | 0.51999 | 18.48221 | 12.92423 | 1.01412 |

All errors are cents. The 5.240 Hz row is an explicit sensitivity candidate, **not an independent estimate chosen without evaluation inspection**. A shared continuous approximately5.24 Hz triangle is supported by the combined observations. The 93→97 onsets are four bars and about37 cycles apart, so those two presets alone poorly separate global from reset phase. The Whistle diagnostic helps separate them, but is shorter than one complete cycle. Longer staggered dry notes with captured MIDI times are required to establish reset behavior confidently.

The numerical coincidence `5.5 MHz / 2^20 ≈ 5.24521 Hz` is a possible future divider hypothesis. The present data neither selects that exact value nor identifies the chip clock. It must not be used to claim a recovered native sample rate.

## Delay observations and estimator limits

A separate fixed threshold observation asks when the pitch departs from its pre-vibrato median for at least12 ms. It does not fit the primary curves or change event alignment:

| Voice / raw VDT | First sustained excursion | Current10ms/step | Excursion/rawVDT |
|---|---:|---:|---:|
| Human Voice 1 / 24 | 0.32399 s at3 cents | 0.240 s | 13.4997 ms |
| Musical Saw / 21 | 0.29800 s at10 cents | 0.210 s | 14.1903 ms |
| Whistle / 31 | 0.41599 s at3 cents | 0.310 s | 13.4192 ms |

These observations consistently flag the old delay as too short. They support investigating roughly13.4–13.5 ms per raw step. They do not establish an exact delay law: the first threshold crossing depends on LFO phase, chosen threshold, filter smearing and the globally inferred note start. A waveform may already be enabled while it remains near its zero crossing. Delay is not silently converted into a freely fitted per-note latency.

The estimator was run on noise-free known sinusoidal and triangular pitch modulation using the same sample rate, carrier, filter and phase-derivative pipeline. At the applicable Human Voice 1 depths10/13.5 cents, maximum RMS estimation bias/error is0.16390 cents; at Saw partial3 with108-cent modulation it is0.75879 cents. This is much smaller than the observed rate/depth differences. The JSON retains deliberately out-of-range tests: applying the40 Hz Human Voice1 filter to108-cent modulation fails badly, up to48.13 cents RMS. A narrow filter must not be reused to infer deep Saw modulation.

Saw partial1 and partial3 differ by34.77344 cents RMS, median absolute difference25.89464 cents, despite their common strong periodicity. This limits the depth precision and rules out treating the residual as silicon noise or claiming an isolated dry waveform. The third partial is the primary Saw evaluation and the fundamental remains a contamination diagnostic; neither receives a fitted harmonic gain or phase.

## Consequence for the engine

The current 6.1 Hz sine and PMS ratio4 are not adequate hardware defaults for these observed voices. The next implementation experiment should use a documented roughly5.24 Hz triangle with a shared binary PMS candidate, then compare the complete native performance and existing regression voices. Phase/reset and delay behavior need their own explicit evidence, rather than being selected by a magnitude-spectrum score. Preserve all previous source snapshots and label any new global epoch as capture calibration, not a power-on phase.

The local reproduction is `python3 build/lfo-audit-20261018/audit.py`, followed by `sensitivity.py` and `finish.py` in that directory, with the external recording workspace available at its recorded path. Scripts, exact protocols, 500 Hz pitch arrays, figures, source snapshot and hashes are preserved locally. No full-synth audio improvement, circuit identification, bit exactness or market-superiority claim follows from this pitch-only audit.
