# EditingFun tonal-line extraction — 19 October 2026

**No new envelope rate qualifies.** A separately frozen tonal-line method was applied to the six existing display-21 supports in Jungle Jon's [PSS 680 Editing Fun!](https://www.youtube.com/watch?v=a0SFoa7lUNQ). All six fail the declared checks. Replacing the earlier speech-containing RMS reference with a frequency-selective measurement therefore does not rescue a rate estimate using this method. This is a bounded negative result, not evidence that no better estimator can separate the recording.

The [JSON receipt](editingfun-tonal-20261019.json) preserves all 76 control summaries, six source summaries, exact bindings and limitations. The [tool](../../Tools/analyze_editingfun_tonal.py) uses existing local media only. No production DSP, factory preset, package, audio gain, timing map or noise behavior changed.

## Frozen selection and measurement

The [earlier audit](opu-envelope-independent-20261019.md) selected source **70.10–70.20 s** and **70.15–70.45 s** for mid, left and right. This pass keeps those six intervals and their 21/61 evaluation centers, spaced 5 ms apart. All twelve display-31 rows remain rejected for range-edge crop; none was remeasured. These reused supports are not a fresh holdout. The visible carrier Decay display is 21, but physical gates, exact captured patch, overlapping notes, capture dynamics and effect state are not established sufficiently to identify a hardware envelope law.

Before any new control or target-tone evaluation, protocol SHA256 `533e79a6cefc570998defb9416affac6885e0e93fbdd511190d63e7e97a3df71` bound the implementation, old selections and source WAV. It prescribed one strongest Hann spectral peak between 180 and 2,000 Hz from the fixed mid union, with 32× zero padding and three-point interpolation. The resulting **349.284698 Hz** was used for every channel and both intervals. It is a selected spectral line, not an established fundamental, played MIDI pitch or a frequency optimized for decay agreement.

At each original center, weighted joint least squares extracts that line with a local quadratic complex amplitude. Its second and third harmonics have separate quadratic amplitudes; DC and a linear trend are nuisance terms. Both 20 ms and 40 ms Hann supports are evaluated. At interval boundaries they are truncated to the original support, with the coefficient still evaluated at the original center; no samples outside the declared interval enter a fit. The 40 ms result is primary. No boundary centers are dropped after inspection.

Fixed residual probes at ±75, ±125 and ±175 Hz measure interference left after the joint fit, excluding frequencies near the three modeled harmonics. They are **not an independent noise floor**, and low residual energy cannot exclude a coherent interfering tone. The frozen checks require R² ≥ 0.99, maximum amplitude-fit residual ≤ 0.5 dB, 20/40 ms slopes within 1 dB/s, residual phase-frequency span ≤ 2 Hz and line/probe separation ≥ 20 dB, alongside finite unclipped input, conditioning and decay checks. These are method qualification rules, not measurements of instrument accuracy.

## Controls and their limits

The 38 controls comprise 24 clean exponential signals, twelve mixtures with the already retained 60.0–60.2 s speech reference, and two explicit nonidentifiability cases. Clean signals span four pitches, three decay rates and two phases, with fixed second/third harmonics. Every control uses both supports and deterministic PCM16 conversion without dither.

- All **48 clean evaluations** qualify. Maximum primary-slope error is **0.00058825 dB/s**.
- All **24 speech-mixture evaluations** are rejected. The mixtures use fixed −20/−10 dB speech RMS relative to initial sine RMS. No admitted contaminated control has a falsely certified accurate slope, but this does **not** establish useful recovery in speech: none qualified.
- The **0.7 Hz nearby-tone confound passes both sets of checks**, while biasing the requested carrier slope by **9.21097 and 13.55624 dB/s**. It was predeclared as a diagnostic, outside the clean/admitted-speech gate. This is a substantial false-admission limit; these checks cannot certify that a captured line represents one isolated physical oscillator or envelope.
- The dynamic-gain control recovers the **captured** slope after a +12 dB/s gain ramp, with errors below 0.000064 dB/s. Its success cannot distinguish that capture gain from a different hardware envelope.

The prospective clean/admitted-speech gate passed, so the tool proceeded to target extraction. That gate is narrower than robustness against unknown coherent interference. The nearby-tone failure is retained and prevents interpreting any accepted line as physical envelope proof.

## Unqualified source results

All values below are diagnostics, **not recovered envelope rates**.

| Channel | Fixed support | 40 ms slope, dB/s | R² | 20/40 ms difference, dB/s | Result |
|---|---|---:|---:|---:|---|
| Mid | 70.10–70.20 | −50.46839 | 0.612880 | 4.53469 | Rejected |
| Left | 70.10–70.20 | −46.07209 | 0.620166 | 3.88939 | Rejected |
| Right | 70.10–70.20 | −54.45348 | 0.597114 | 4.90031 | Rejected |
| Mid | 70.15–70.45 | −21.80466 | 0.942561 | 1.88236 | Rejected |
| Left | 70.15–70.45 | −21.59945 | 0.958562 | 0.90443 | Rejected |
| Right | 70.15–70.45 | −21.97820 | 0.918546 | 2.74416 | Rejected |

Every source row fails linearity, phase stability and residual-probe separation. Five also fail the analysis-width comparison. The retained coefficient curves show appreciable oscillation and boundary sensitivity. These are **estimator outputs**, not direct proof that the hardware envelope itself fluctuates. The frozen three-line model can be contaminated by unmodeled FM partials, multiple notes or processing. The clean controls cover only its declared three-harmonic family; they do not validate every possible FM spectrum. No extra harmonics, replacement frequency, longer support, omitted endpoint or relaxed gate was introduced after seeing this result.

The old mid extended RMS fit, −23.110415 dB/s, remains rejected under its original protocol. The superficially nearby tonal-line estimate does not override that failure. This pass shows that the speech-RMS reference is not the only obstacle for this particular estimator; it does not establish which interference or capture mechanism causes the disagreement.

## Reproduction and retained evidence

With the existing ignored media and frozen protocol available:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -B Tools/analyze_editingfun_tonal.py \
  --protocol build/editingfun-tonal-20261019/protocol-frozen.json \
  --out build/editingfun-tonal-20261019/a-new-output-directory
```

The tool refuses an existing output directory and verifies source/implementation bindings. The original run, complete coefficients and controls, a standalone plot and validation remain under ignored `build/editingfun-tonal-20261019/run-001`. The post-run validator performs 189 checks spanning bindings, arithmetic, counts, gates and support conditions; independent OLS recomputation agrees within 3.56e-14 dB/s. It does not constitute a second implementation of the raw harmonic projection. No further audio acquisition or source redistribution occurred.
