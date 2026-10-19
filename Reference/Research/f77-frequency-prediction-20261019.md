# F77 fixed-tail frequency prediction diagnostic — 2026-10-19

**Result: inconclusive under the frozen gates.** Neither of the two F77 events has a qualified estimator family. The captured Opus/AAC estimates agree and pass the quiet checks, but every method fails to recover known equal temperament in the existing finite-tail research render. All captured estimates are descriptively closer to equal temperament than to the frozen candidate. This adverse direction is retained; the failed controls prevent treating it as a precision falsification or validation.

This tests a new note class against the candidate in [the frequency hypothesis](opu-frequency-hypothesis-20261019.md), using the already retained [PSS-780 recording](https://www.youtube.com/watch?v=ONfIvtDOog0). It is **not an unseen-source or unseen-pitch holdout**. The prior [pitch-pattern audit](pitch-pattern-audit-20261019.md) already measured held F77 observation `w09_1746`, at 177.868080737268–177.928626166836 s. Event 1728 was previously excluded by that audit's fixed program-start guard. Those earlier F77 frequency estimates were not read to design this test; the new fixed tail windows were frozen before opening target audio.

## Frozen prediction and windows

The candidate's F seed remains 1,065. At musical MIDI 77 its integer word is 12,780 and its frequency before the common nuisance is 698.2684135437012 Hz, or −0.466172539985 cents relative to equal temperament. The previously fixed G67 anchors, events 1760/1770, supply the unchanged common offsets: **−1.852738918932 cents for the candidate** and **−1.482160557032 cents for equal temperament**. No F77 tuning, clock offset, local time shift or frequency-center fit is allowed. Thus the two fixed predictions differ by approximately 0.836751 cents.

Both F77 events have mapped gates of 0.220545429568 s. Source-MIDI gates and the continuous old audio mapping need not have identical numerical durations. Each measurement interval starts exactly 0.2 s after its mapped note-off and lasts one previously calibrated RecordedChorus period, 1.047507885130 s:

| Event | Mapped note-on | Mapped note-off | Frozen analysis window |
| ---: | ---: | ---: | ---: |
| 1728 | 175.783171871158 | 176.003717300725 | 176.203717300725–177.251225185856 |
| 1746 | 177.768080737268 | 177.988626166836 | 178.188626166836–179.236134051966 |

There is no F77 retrigger inside either interval. Subsequent other notes, previous releases, possible voice stealing and coincident or near-coincident lower-note harmonics remain confounds. A full chorus-period duration only removes an idealized periodic endpoint difference when that component survives and the effect follows the assumed law; it is not a general guarantee of unbiased pitch estimation.

The frozen protocol SHA-256 is `37587fdf8cc946d649e6060a4da6e491c8f9b39e616f08b1836c78bce45d4f46`.

## Methods and gates

The unchanged estimator families from the prior final-tail test are fixed 6/12 Hz, fourth-order, zero-phase complex-demodulated **endpoint** phase differences, and full-window Hann/Blackman spectral peaks. Phase filtering uses actual ±0.5 s context and the nominal F77 center, without a frequency-center fit or phase-slope regression. Spectral search remains nominal ±75 cents, at least 16× zero padding and bounded peak refinement. All four methods run on both events in arithmetic mid, left and right, for the existing PCM16, Opus and AAC files and the existing research render. AAC drops only the frozen 627-frame lag; the research render drops its declared 32-frame latency.

Eight analytical controls use all 22 Sine99 musical pitches in stationary or −14 dB/s exponential ensembles, each with common shifts of 0/−2 cents and two fixed initial-phase rules. Their target frequencies are known. The unchanged RR3-carrier Reverb-on full-performance render adds a finite-tail/composition/effect stress control; it is a hypothetical equal-tempered render, not hardware evidence or adopted production behavior. No new full WAV was generated.

For each event/method, **all eight analytic controls and research-render mid must be valid and have absolute known-frequency error ≤0.05 cents**. Captured Opus/AAC mid must then be valid, differ by ≤0.05 cents and pass both amplitude requirements: minimum at least 0.2 times the interval median and at least ten times the fixed post-extinction floor. Spectral methods inherit the 12 Hz quiet diagnostics. Arithmetic mid is the predeclared primary channel, matching the old G calibration; neither side can replace it after inspecting results.

The floor interval is the previously fixed final-composition quiet window, 184.378989328624–184.978989328624 s. A floor defined relative to each earlier F77 note-off would contain subsequent performance or the other F77 event. This metadata-only choice was disclosed before measurement. Both a phase endpoint and a spectral family must qualify for a window to become evaluable. No thresholds, windows or methods were relaxed.

## Failed control and retained capture results

All analytic known-frequency errors are tiny: maximum absolute error 0.000180836 cents. The finite-tail render fails every method:

| Event | Phase 6 Hz bias | Phase 12 Hz bias | Hann bias | Blackman bias |
| ---: | ---: | ---: | ---: | ---: |
| 1728 | −5.935077 | −9.496397 | **−0.066471** | **−0.068201** |
| 1746 | −7.130492 | −14.237733 | −1.475419 | −1.513809 |

Values are cents relative to the render's known equal-tempered F77. Even the first window's small spectral failures exceed the strict 0.05-cent gate. They are not rounded into eligibility. The finite signal history, effects, release survival, allocation and possible leakage are not separately identified by this failure. It establishes that these exact windows/methods cannot reliably recover the known pitch in that stress composition.

All eight captured mid method/window combinations pass the quiet and codec gates; the largest absolute AAC-minus-Opus disagreement is 0.0302072 cents. Those successes do not override the control failures. Across all 16 Opus/AAC mid estimates, the candidate residuals are **+0.436561…+0.767900 cents**, versus **−0.400190…−0.068850 cents** for the fixed equal-tempered prediction. Every one is closer to the equal-tempered prediction, but all are unqualified. All channels, encodes, known-control errors and model residuals remain in [the JSON report](f77-frequency-prediction-20261019.json), rather than selecting a favorable estimate or hiding an adverse one.

There are 40 source/channel/event rows and 160 estimator outputs. All eight event/method eligibility decisions fail solely at the finite-tail control gate. The outcome supports neither adopting the candidate for F nor correcting its F seed from these captures. It preserves a concrete adverse lead for a future effects-off, isolated chromatic recording, where a known gate, continued signal and reference pitch can be established.

## Artifacts and unchanged scope

Ignored artifacts are under `build/f77-frequency-prediction-20261019/`: `freeze_protocol.py`, `protocol-frozen.json`, `analyze_f77.py` and `result.json`. The tracked JSON binds their hashes and all reused source/protocol inputs. The result hash is `fa36a67f25811b8c093b6580c85af8b15f828826904426356d9088d211cec133`.

No media was acquired, no audio file was generated, and no production DSP, noise path, preset, UI, host, package, prior research output or Git operation was changed. This is a bounded research diagnostic with retained failed gates.
