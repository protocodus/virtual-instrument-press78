# PM envelope separation — control failure, 2026-10-19

**The method does not qualify, and no new Bass recording inference was attempted.** The full frozen suite completed 56 synthetic/native controls and four nested-grid checks. Only one of 45 recovery cases meets the expanded-error allowances; every overall gate fails. This is a completed measurement-method experiment, not a measured change to Yamaha's envelope law. Production DSP, presets and the no-additive-noise behavior are unchanged.

The [full ledger](pm-envelope-separation-20261019.json) preserves the original result, control failures, profile branches, code/protocol hashes and posthoc diagnostic. The [frozen protocol](pm-envelope-separation-protocol-20261019.json) has SHA-256 `7ccda95528886cf06021ff5c2e2dd04938b59918f7224574b976128e917db80a` and predates every new synthetic extraction in this pass.

## Source question and model

The existing [original-author recipe](https://www.pss680.com/patches.php) for Synth Bass 1 starts from 99 and lists panel values `63,63,24,22,1,1,00,77,86`: feedback really is 0. This does not reuse the earlier mistaken Saw-feedback premise; Saw has feedback 7. The [prior source audit](isolated-source-search-20261019.md) and [captured envelope study](opu-envelope-independent-20261019.md) already describe the same-name WAV, inferred notes, fixed body/ late supports and unknown capture processing.

Actual effects and MIDI gates are unrecorded. Original firmware shows that selecting 99 clears inherited Vibrato/Sustain but preserves Reverb; the author also leaves effects to preference. Neither the recipe nor a PCM-active boundary proves a dry, held-key D2 stage. The source is reused evidence, not an unseen holdout. Original media stays ignored and no commercial redistribution permission is claimed.

A 1:1 sine PM signal has overlapping positive/negative sidebands. With carrier/modulator relative phase δ, its positive harmonic coefficient is

```text
B_h(beta, delta) = [exp(i*delta)*J_(h-1)(beta)
                   - (-1)^(h+1)*exp(-i*delta)*J_(h+1)(beta)]/(2*i)
```

A simple ordinary-Bessel-magnitude inversion or assumed δ=0 would therefore be invalid. The proposed estimator uses weighted complex harmonic fits, temporal ratios, one constant relative phase per note, and per-time beta/carrier-amplitude measurement parameters. It imposes no exponential rate law or monotonic beta path. All compatible beta/phase branches are retained.

Magnitude double ratios `(Hh/H1)_time / (Hh/H1)_anchor` remove a fixed per-harmonic multiplier and carrier amplitude. This cancellation is conditional on a locally narrowband, constant-transfer approximation; arbitrary LTI filtering of changing envelopes is not exactly canceled. Predicted phase changes are checked through `arg[Zh(t)/Zh(anchor)] - h*arg[Z1(t)/Z1(anchor)]`, which removes common oscillator phase advance and fixed harmonic phase response. It does not require the invariant itself to stay constant.

## Frozen procedure

The intended source supports are all 21 previously defined body intervals at active-entry +0.15–0.55 s, plus all 21 late intervals at +0.65–1.05 s. Five old late metadata failures remain failures. Each interval has 17 fixed 25 ms-spaced centers and a 50 ms Hann extractor. The same first-body anchor serves both intervals; weak/null anchors are never replaced.

The extractor fits DC/trend and harmonics 1–10, with a local-affine complex amplitude for each harmonic. Scoring uses eligible H2–H6. Visibility is fixed against the preceding quiet reference and a projection-matrix PCM16 error scale; that scale does not establish independent white quantization noise. Real-source extraction is behind a hard control-first gate.

The finite search uses 2,401 log beta points in [0.001, 8] and 33 canonical phases in [0, π/2], retaining conjugate signs. Per-cell harmonic-ratio RMS must be at most 0.1 dB and profile mean at most 0.075 dB; the latter denominator includes the fixed zero-error anchor. These are predeclared precision demands, not measured error bars. Accepted beta endpoints reject a precision claim. Every reported range remains conditional on this finite domain and PM family; aliases outside it are not ruled out.

Controls include decaying carrier and beta at both prospectively predicted rate families, multiple pitches/phases including an off-grid phase, clock offsets, deterministic PCM16, causal filters/delays, native full-engine dry and Real outputs, constant-beta/null cases and processing confounds. Native controls use an independently authored patch, not a sampled factory voice. No stochastic noise or dither is added. Four preselected controls are also tested on 4,801 beta / 65 phase nested grids; no source-specific grid tuning is allowed.

## Results retained

All 56 cases ran, including 45 recovery cases, and all four grid checks completed. The whole run took 298.711 s. All global gates fail:

| Recovery measure | Body, qualified / 45 | Late, qualified / 45 | Unexpanded truth coverage, body / late |
| --- | ---: | ---: | ---: |
| Captured carrier slope | 1 | 1 | 0 / 0 |
| Beta slope | 1 | 1 | 0 / 1 |

The sole expanded-error qualifying case is analytic-22. Its carrier ranges do not contain the unexpanded truth. It cannot support a claim that the method generally recovers envelopes. Every native control is retained, including expected fast-decay/PCM-floor failures. The 10 native float WAVs total 7,056,440 bytes and remain ignored.

There is one explicit protocol/implementation interpretation mismatch: the prose prohibits falsely claiming a unique beta for pure-sine/null cases, whereas the frozen script additionally requires zero accepted profiles for the sine/no-beta case. The sine control actually produces 154,058 broad profiles reaching the beta boundary, with no qualified precision claim. The constant-beta case has zero compatible profiles, and the H1-null case has none. The stricter script flag and the actual nonunique outcome are both retained. This does not alter the experiment's failure: recovery and nested-grid gates fail independently. No artifact was rewritten to manufacture a pass.

The tool stopped before decoding the Bass PCM for new inference. Previously published RMS/H1 decay observations remain unchanged. There is no new measured carrier/beta slope, raw rate table, RR multiplier or score for the [separately frozen rate-family prediction](envelope-rate-family-protocol-20261019.json). That authored protocol is preserved byte-for-byte with its original hash; neither family was selected by this failed method.

## Separate posthoc diagnosis

A second, explicitly posthoc diagnostic compares the saved synthetic coefficients with exact instantaneous coefficients at their original rounded sample centers. It fits nothing and reads no source recording. Across 36 unprocessed analytic controls, maximum per-case temporal-ratio error is 0.169799–0.741862 dB; 316 cells exceed 0.1 dB. The exact phase-invariant identity agrees within 3.64e-12 rad, while the largest nearest-grid-only ratio error is 0.095463 dB. These separate window/measurement bias from a sign error in the overlapping-sideband formula.

Replacing only the saved complex coefficients with instantaneous truth, while retaining the original masks, radii and grids, gives:

| Fixed replay | Extracted profiles | Exact instantaneous, coarse / denser |
| --- | ---: | ---: |
| analytic-00 | 0 | 332 / 1,306 |
| analytic-11 | 0 | 171 / 715 |
| analytic-24 | 0 | 326 / 1,282 |

This explains a meaningful part of the rejection, but is not a rescued waveform-extraction pass. With exact coefficients, body carrier-slope ranges still span roughly 1.4–2.2 dB/s, above the frozen 1 dB/s width gate. Late-carrier ranges are much tighter in those idealized controls. Unknown phase/scale branches and finite tolerance therefore remain relevant even when extraction error is removed.

An independent root calculation on the same fixed three saved controls corroborates ratio bias around 0.36/ 0.59/ 0.72 dB. Its nominal-time calculation and this diagnostic's rounded-center calculation are separately retained; their small numerical differences are not model fits. Root's separate polynomial probe also retains unsuccessful higher-order alternatives, rather than changing this experiment.

The immediate technical gap is uncertainty-aware harmonic extraction: weak visible lines and dynamic-window leakage cannot be treated as exact instantaneous harmonics. A future method would need a separately frozen treatment and new control pass. Increasing every matching radius, choosing another anchor or borrowing a Yamaha rate law would not validate this failed method.

## Reproduction

The authored [estimator](../../Tools/measure_pm_envelope.py), [native control renderer](../../Tools/PMEnvelopeControl.cpp) and [posthoc diagnostic](../../Tools/diagnose_pm_envelope_controls.py) are research tools, separate from the instrument build. The protocol binds all nine native DSP inputs. Use the matching pinned source files and a fresh ignored output directory:

```sh
python3 Tools/measure_pm_envelope.py \
  --protocol Reference/Research/pm-envelope-separation-protocol-20261019.json \
  --native-source Source/DSP --out build/pm-control-reproduction --controls-only
```

Python needs NumPy, SciPy and threadpoolctl; the native control uses a C++17 clang compiler. Controls-only reproduction needs no third-party recording. The tool rejects existing output directories and mismatched implementation/source hashes. The full original run is under `build/pm-envelope-controls-20261019`; posthoc outputs are under `build/pm-envelope-control-diagnostics-20261019`. Their files and the separate independent checks are bound in the JSON ledger. No production or artificial-noise path changed.
