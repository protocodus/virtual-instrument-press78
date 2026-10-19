# MN3206 AC distortion constraints, 2026-10-19

This adds a **signal-level-explicit aggregate-THD constraint oracle** to the
research circuit tools. It quantifies a retained manufacturer's typical curve
at its stated conditions. It does not process audio, construct a nonlinear
transfer, or change Press78. The U-shaped curve was already known qualitatively
in the v4 study; the new work makes supported scalar queries reproducible and
exposes their reading limits.

The source is Panasonic's [MN3206 datasheet, printed p.77](https://github.com/fmillion/yamaha-pss270/blob/8943bf963f196f20b4e2fc714f15400db578891b/datasheets/MN3206.pdf),
top-right THD–Vi panel. The retained 1377×1800 raster has SHA-256
`34916e399deedf1f7247c5c1e481197854786d1604bb6e292a26b66d1c1dd90f`.
No source was downloaded and no PDF page was re-rendered. This is not a new hardware holdout.

## What the component can answer

The [oracle](../../Tools/prototypes/mn3206-ac-constraints-20261019/mn3206_ac.py)
requires an input level on the **manufacturer's dBm graph axis** and every
visible panel condition: VDD 5 V, VGG 14/15 VDD, CP 40 kHz, input frequency
1 kHz, temperature 25 °C, and the indicated 20 kHz / −48 dB-per-octave LPF.
Supplies are referenced to chip ground. Exact VGG 14/3 V and its single nearest
binary64 representation are accepted; that representation alias introduces no
physical voltage tolerance. Other conditions and missing/invalid ports reject.

The retained p.76 table was visually inspected: it does **not** define
0 dBm as 0.775 Vrms. Accordingly, this component supplies no dBm/voltage/power
conversion. Its separate 0.25 Vrms, 0.3% typical THD table entry is not mapped
onto the curve. The p.76 table states a 100 kΩ load, but that is not silently
imposed on the p.77 panel. Panel input bias, output load/joining and analyzer
noise treatment remain unspecified. The middle-right gain-versus-input panel
omits the THD panel's VGG/filter labels; it is not fused into this component.

Thirteen manually read pixel centerlines and all coordinate scenarios were
[frozen before implementation](../../Tools/prototypes/mn3206-ac-constraints-20261019/design-frozen.json).
The oracle uses exact-rational piecewise-linear interpolation, an explicit
reading approximation. One considered column, x=1105, is preserved with a null
ordinate because vertical grid ink confounds it. The near-vertical endpoint
at/after x=1170 was excluded; no continuation to 0 dBm or the axis limit was
invented.

The returned range spans 64 declared coordinate-reading corners: ±1 pixel for
each axis endpoint and ±3 pixels horizontally/vertically for the trace.
**It is not a device tolerance, statistical confidence interval, or a bound over
every continuous trace inside those boxes.** Requiring every scenario to stay
inside retained knots narrows the input domain to −1716/89 through −100/89 axis
dBm, approximately −19.281 to −1.124. Outside values reject rather than extrapolate.

The returned binary64 scenario limits round outward. The comparison method
classifies against the exact rational extrema, so feeding a displayed rounded
limit back can classify just outside by less than one ulp. This is numerical
representation semantics, not an additional physical tolerance.

| Input on graph axis | Nominal THD | Declared reading-scenario range |
| --- | ---: | ---: |
| −18 dBm | 0.34330% | 0.29413–0.39246% |
| −12 dBm | 0.24916% | 0.21251–0.28581% |
| −4 dBm | 0.46212% | 0.39777–0.52648% |
| −2 dBm | 0.67430% | 0.57598–0.77631% |

These levels were selected in the frozen protocol. Across the declared scenarios,
THD at −18 exceeds THD at −12 by at least 0.00832 percentage points. THD at −2
also exceeds THD at −12. Thus a static compressive cubic as the **sole** mechanism,
whose normalized THD increases with amplitude before fold-back, cannot explain
this whole typical-curve region. An unknown common level reference does not
reverse the ordering. This does not identify a noise floor, even/odd harmonics,
bias error, or another unique explanation. The existing v4 single-point cubic
remains an explicitly limited scenario; these data do not replace it with an
identified target transfer.

## Checks and reproducibility

The first run passed **7,023 checks**: source/design/implementation bindings,
all 13 coordinate conversions, 11 supported knots, 101 independent interpolation
queries, 6,464 independently expressed scenario checks, exact support and
boundary rejection, exact-rational VGG handling, invalid/missing conditions,
statelessness, and aggregate-THD comparison classification. Numerical source
bindings were frozen before execution. The [receipt](mn3206-ac-constraints-2026-10-19.json)
retains the exact first-run result and source hashes.

```sh
python3 -S Tools/prototypes/mn3206-ac-constraints-20261019/check.py \
  build/mn3206-ac-constraints-review/validation.json
```

The receipt path must not already exist. The oracle and checker use only Python's
standard library; the checker also verifies the existing local acquisition
files. Inspection crops/overlays remain under ignored
`build/mn3206-ac-constraints-20261019/`. No native DSP, production schema, UI,
host, presets, recordings, clock, DAC, supply-sag, or noise behavior changed.
The actual PSS-780 BBD input voltage, bias and surrounding AC circuit remain
unidentified by this experiment.
