# HALF² waveform: a shared-table constraint, not a recovered OPU circuit

The current HALF² operator, table 3, correctly implements the ideal positive
half of a squared sine. A new quantitative cross-waveform audit shows what a
shared digital table and a common output response would have to preserve. It
also shows why the available PSS-680 video cannot determine a new table curve
or a DAC distortion coefficient. No production DSP, preset, default, package,
output character or artificial noise changed.

The [machine-readable result](oscillator-half-squared-audit-2026-10-19.json)
retains every declared comparison, all copied complex coefficients, original
source bindings and the actual native test receipt. The
[bounded probe](../../Tools/prototypes/oscillator-half-squared-audit-20261019/README.md)
reads the separately frozen harmonic-fit JSON; it does not open PCM or render
audio. This is a new analysis of already inspected sibling material, not a new
recording or an untouched holdout.

## What the primary sources establish

Yamaha's [PSS-780 manual](https://usa.yamaha.com/files/download/other_assets/1/317511/PSS780E.PDF),
printed p41, names table 3 Squared Sine Half Wave. It does not give ROM contents,
phase-address width, rounding, signed zero, conversion cadence or a transistor
implementation.

[Kevin's original PSS-680 experiment](https://diyelectromusic.com/2023/08/02/arduino-pss-680-synth-editor-part-1/)
changes only the carrier table of the Sine Wave voice, with no feedback,
modulation or frequency multiplication. Its table sequence and transition
caveat support the existing guarded-window selection. They do not certify an
unchanged, linear, dry electrical recording chain.

Yamaha's [US4813326A, Fig22](https://patents.google.com/patent/US4813326A/en)
describes shifting logarithmic sine data before conversion to obtain a power
of sine, followed by phase-dependent gating and sign control. This is a
documented digital architecture consistent with this family of ideal shapes.
The patent does **not** identify YM3420 or establish which embodiment it uses.
Its generic name OPU is not a target-chip identification. No patent-derived
precision or circuit constants enter the engine.

## An exact relation between SIN² and HALF²

Let `q(phi) = sin(phi)*abs(sin(phi))` be the current signed-square table and
`r(phi) = max(sin(phi), 0)^2` the current HALF² table. Then

```text
r(phi) = (sin(phi)^2 + q(phi))/2
       = 1/4 - (1/4)*cos(2*phi)
         - (4/pi)*sum_{n positive odd} sin(n*phi)/[n*(n*n-4)].
```

Consequently HALF² has mean `1/4`, cosine H2 coefficient `-1/4`, no even
partials H4 and higher, and every odd coefficient is exactly half that of
signed-square. Their normalized odd amplitudes are identical: H3/H1 is
−13.979400dB and H5/H1 is −30.881361dB.

The unchanged actual C++ helper passes 262,169 assertions over 65,536 equally
spaced phase points. Its mean is 0.2500000000000001, maximum pointwise
decomposition error is 2.78e−17 and maximum error across the 24 tested sine and
cosine coefficients is 3.33e−15. The quadrature count and tolerances are test
choices, not measured OPU precision.

There is a stronger invariant that does not assume a squared sine. For any
shared table `q` with `q(phi+pi) = -q(phi)`, copying its first half and zeroing
the second produces a table `r` whose odd Fourier coefficients are `q/2`.
This remains true with an arbitrary shared magnitude curve or symmetric
quantized table. A common LTI output filter preserves the relation at equal
pitch. Separate constant gains and arbitrary time origins still preserve
normalized odd magnitudes and the phase invariant `arg(Zn)-n*arg(Z1)`.

Five declared synthetic table families, including two arbitrary quantized
fixtures, pass 42 checks. The checks cover the coefficient identity, an
arbitrary common four-tap circular filter, unequal gains and different circular
shifts. Intrinsic harmonic nulls retain coefficient checks; their undefined
normalized phase is not scored. These fixtures prove the algebra and software
diagnostic, not the hardware topology. They concern the phase-domain waveform
and do not simulate native-clock images or alias folding; the target update
cadence remains unknown.

## What the retained recording does and does not satisfy

The independently frozen [signed-square audit](oscillator-signed-square-audit-2026-10-19.md)
fits all four unchanged source windows and all their equal thirds. This audit
uses every one of its 16 mid-channel coefficient rows. The original stable
windows are mono at the sample level, so L/R/mid do not provide independent
hardware observations.

For the full windows:

| Partial | Signed-square capture | HALF² capture | HALF² minus signed-square |
| --- | ---: | ---: | ---: |
| H3/H1 | −13.94654dB | −12.73458dB | +1.21196dB |
| H5/H1 | −54.48039dB | −56.76956dB | −2.28917dB |

Across all 16 full/third support pairings, the H3 difference remains
+0.458…+1.280dB. H5 differences are −3.276…−1.384dB, but these much weaker
partials are more vulnerable to the recording and fitting residual. All 80
odd-partial comparisons are retained, including the less stable higher
partials. The intervals are diagnostics within one recording, not confidence
intervals or independent replications.

Both captures strongly suppress H5 relative to the ideal curve, by 23.60dB
and 25.89dB respectively. Thus the weak H5 cannot safely be attributed to the
digital oscillator alone; a shared capture/output response remains an
explanation. Conversely, one common equal-frequency response would not make
the measured normalized odd coefficients exactly identical. This relation also
means that changing a **shared** power curve or quantizer alone cannot explain
a difference between the two normalized odd spectra under that hypothesis.

The estimated fundamentals are not identical: 523.067696Hz versus
523.080669Hz, a difference of 0.012972Hz. Without an independent smoothness
bound, an arbitrary LTI response can have different values at those distinct
spectral frequencies. It is therefore invalid to claim the measured mismatch
unconditionally rejects a common filter.

The audit instead states a conditional requirement. If those estimated
frequencies were exact and one stationary linear response `D(f)` in dB alone
explained the full-window H3 difference, its maximum absolute slope over the
fundamental and third-partial intervals would have to be at least
23.36dB/Hz. This follows from

```text
abs(delta normalized partial dB) <= (n+1)*abs(delta f0)*max(abs(D'(f))).
```

No such slope bound is assumed or fitted. Frequency-estimation error,
nonstationary amplitude/phase, nonlinear output/capture behaviour, effects,
different table construction and imperfect partial estimation remain possible.
The full-window fit residuals are 4.59% and 4.10% respectively, substantial
enough that tiny numerical regression precision is not chip precision.

A separate declared H2 comparison uses HALF versus HALF². Their ideal H2/H1
ratios differ, so that known difference is removed algebraically. The
full-window implied normalized-response difference is +0.92454dB. It is
retained as another unresolved consistency condition, with all 16 support
pairings, rather than used to fit a filter.

## All four tables contain energy outside the strict ideal/LTI model

At the analytically absent harmonics, the Euclidean amplitude-vector norm
relative to the vector of all twelve fitted partials is:

| Table | Analytically absent partials | Full-window vector ratio |
| --- | --- | ---: |
| SIN | H2–H12 | 1.7632% |
| SIN² | All even partials | 1.3052% |
| HALF | Odd H3 and higher | 0.5285% |
| HALF² | Even H4 and higher | 0.3144% |

An LTI filter cannot create a harmonic absent from a stationary periodic input.
These nonzero coefficients therefore fall outside a strictly ideal static
table plus LTI-only description of the **complete recording**. This does not
locate them in the chip or establish their statistical significance. The vector
ratio is not an audio RMS error or a calibrated lower bound on physical
distortion; finite-window coefficient estimates and capture imperfections also
contribute. The [SIN audit](oscillator-sine-audit-2026-10-19.md) separately
examines persistence of its strongest forbidden partial.

## Consequence for the instrument model

Preserve the current mathematical HALF² function while marking its finite
table, arithmetic and native update schedule as unverified. There is no support
here for arbitrary bit reduction, a fitted asymmetric waveshaper, an invented
voltage-fluctuation coefficient, added noise or replacing the digital operator
with an analog VCO circuit.

A useful separating recording would document exact patch bytes and equal
pitch, preserve gain and note level, disable each effect explicitly, and switch
only the carrier between tables 1 and 3 at several levels. Matched electrical
output would help distinguish a shared table/gating relation from output
nonlinearity and capture response. A corresponding modulator experiment is
still needed for internal mean handling; carrier-only settled AC does not
identify it. These are source/measurement requirements, not a request for
hardware access or a claim that the detailed YM3420 circuit has been recovered.
