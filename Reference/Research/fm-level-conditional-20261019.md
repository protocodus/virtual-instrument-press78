# Conditional FM level and feedback test — 2026-10-19

This pass does **not** justify an amplitude-model change. It first corrects a material source assumption: Jon Jungle's Saw synth recipe has **Feedback 07**, not zero. Its low-note stationary spectra are close to the current coupled FM/feedback primitive. A globally fitted alternative improves average error, but fails the frozen validation rule, and four numerical controls fail their explicitly frozen accuracy rules. Eight additional controls fail a residual check also applied by the script. All failures are retained in the [JSON proof](fm-level-conditional-20261019.json). Production DSP and the removed-noise behavior are unchanged.

## Source and command constraints

The author's [patch page](https://www.pss680.com/patches.php), reopened for this pass, gives base voice99 and panel parameters `63,63,00,00,01,01,07,77,86`. The [sample page](https://www.pss680.com/samplepacks.php) supplies the same-name continuous Saw Synth WAV and describes ascending C/E-flat/G/B-flat notes. The [earlier source audit](isolated-source-search-20261019.md) binds its original archive, PCM16 mono44.1kHz WAV and frozen note interiors. No recording was downloaded again.

The same name is a conditional recipe association, not an observed patch dump. Effects are left to preference; actual physical settings, upstream processing, recording route, transposition and source clocks remain unknown. This recording has already supported pitch and envelope research, so it is not fresh audio or an independent hardware replicate. It has no recorded MIDI gates or embedded root/loop metadata. No redistribution or commercial sample license is claimed; the media remains ignored.

A bounded original-program execution in both PSS-680 and PSS-780 verifies that panel parameter6 directly increments/decrements the raw three-bit feedback field, saturating at0/7. Forty-four transitions preserve every other working-voice bit. Two further witnesses show that parameter7 at77 corresponds to raw modulator TL22 from base99. This agrees with the separately verified [front-panel level mapping](front-panel-level-map-20261019.md). It proves software commands, not the chip's internal feedback law or actual recorded patch. The earlier assumed Feedback0 premise was rejected **before** new harmonic measurements. A no-feedback Bessel fit would be inappropriate.

## Frozen selection and estimator

The design was written before these new measurements: SHA-256 `6009805e9868a031b472035c3c4456039bc5f650d768aeeca9d623632bfe88b6`. It reuses exactly the first eight previously frozen Saw interiors, inferred notes36,39,43,46,48,51,55,58. Even indices—C/G—are calibration; odd indices—E-flat/B-flat—are validation. Their prior phase-frequency estimates stay fixed. No window, pitch, time shift or note-specific FM parameter was adjusted.

Joint Hann-weighted least squares fits DC, a trend and the first12 harmonic sin/cos pairs. Scoring uses magnitudesH1–H8 divided algebraically by their L2 norm, then dB differences. The highest scored partial is below1.865kHz. There is no gain/EQ/capture-response fit; normalization removes constant gain, not frequency-dependent filtering, saturation or effects. Three fixed subwindows check harmonic-magnitude stability. The real-note gates require less than1dB strong-harmonic change, at most10% weighted residual power, an adequate fundamental, no clipping and sufficient samples.

All eight real windows pass. Their maximum subwindow harmonic change is0.073059dB, weighted residual fractions span0.014995–0.018069 and peak PCM magnitude is0.887360. Stable spectra make them useful conditional shape fixtures; stability does not establish a clean or flat recording path.

## Conditional primitive and validation

The compared recurrence is the current engine's sine/1:1 primitive, expressed with a normalized modulator:

```text
u[n] = sin(theta[n] + kappa * (u[n-1] + u[n-2]) / 2)
y[n] = sin(theta[n] + beta * u[n])
```

It runs at the existing model choice48kHz with a fixed0.5second settling interval. The current combined assumptions give `g = 10^(-0.75*22/20)`, `beta = 8*pi*g = 3.760450356` and `kappa = 4*pi*g = 1.880225178`. This is an equation-level comparison; it does not render the full native engine, chorus or analog output. Source effects and frequency response therefore remain confounds.

The frozen family shares only two parameters across every note: beta0.1–10 and kappa0–3. A fixed121-point grid seeds five bounded least-squares runs; selection uses calibration error alone. No validation data chooses a parameter or minimum. All starts, local minima, residuals and the declared calibration-only beta profile remain in the ledger.

| Conditional primitive | Calibration RMS, dB | Validation RMS, dB |
| --- | ---: | ---: |
| Current beta and feedback | 0.478794 | 0.554417 |
| Half beta, same feedback | 4.384759 | 4.416601 |
| Double beta, same feedback | 2.442923 | 2.512400 |
| Feedback0, contrary to recipe | 7.029670 | 7.151331 |
| Selected global beta4.010501 / kappa2.017217 | 0.168485 | 0.309588 |

The selected alternative reduces validation RMS by about44%, below the required50%, and one held-out note worsens: inferred51 goes from0.213753 to0.223085dB. It fails independently of the numerical-control problem. The current primitive's small error gives no support for a large FM-depth correction under these source assumptions.

Ninety-six controls compare PCM16-quantized simulations at current/half/double beta and four phase starts against a two-second steady reference. **92 meet the explicitly named accuracy/consistency criteria; four fail.** The four double-beta controls at inferred48 exceed0.05dB harmonic-estimator accuracy, reaching0.168986dB. These failures alone keep overall qualification false.

A final scope check also found that the script applied the shared estimator's10% residual rule to controls, although the frozen controls subsection explicitly repeated only the accuracy and1dB consistency rules. Under that additional script check, eight current-model controls at the two highest notes fail with0.108377–0.125493 residual power, giving **84/96 combined passes**. Both counts are retained. The12-harmonic representation leaves this residual; it does not establish an error in the first eight harmonic magnitudes. The frozen design, script, results and flags were not rewritten. The original report is preserved with hashes in the JSON amendment disclosure. No criterion was relaxed to qualify the experiment: it remains unqualified under either reading. The tables above are descriptive conditional results, not a qualified silicon-law estimate.

## Identifiability and reproduction

Only one published modulator level is available here. Even a perfect fit would identify an effective product such as `beta = phase_scale * 10^(-TL_step * 22/20)` under the assumed operator amplitude, envelope, velocity and feedback placement. It cannot separate8pi from0.75dB/code, establish a DAC transfer or recover the actual hidden source settings. Filtering or nonlinear capture could also explain a small residual improvement. No fitted value is adopted.

Ignored `build/fm-level-conditional-20261019/` contains the immutable design, original-program mapping probe, C++ recurrence, analysis script, full controls, calibration search and result. The JSON binds every artifact by hash. The analysis refuses to overwrite an existing result; reproduction requires a separate direct child of `build`, the copied design/script/helper, the existing local media, exact source bindings and NumPy/SciPy/threadpoolctl. The original-program probe uses the already installed research py65 environment. Its first system-Python invocation failed for a missing dependency; the unchanged probe then passed in that existing environment. No package, source, preset, host session or artificial-noise path changed.
