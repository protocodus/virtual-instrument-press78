# Signed squared sine: higher-partial and observability audit

The current `sin(phase)*abs(sin(phase))` is a defensible **shape hypothesis**,
but the previously reported third-harmonic match does not validate its
higher partials. The retained PSS-680 recording has a fifth harmonic about
24 dB below this formula. The same deficit appears in the half-squared
wave, so an unknown shared output/capture response remains a plausible
explanation. This audit identifies a new constraint; it does not identify
a replacement waveform or justify a production DSP change.

The [JSON receipt](oscillator-signed-square-audit-2026-10-19.json) contains
all 16 fixed capture-window analyses, the two short native controls,
conditional transfer diagnostics and validation. The
[research-only probe](../../Tools/prototypes/oscillator-signed-square-audit-20261019/README.md)
includes the actual unchanged engine translation unit rather than copying
its oscillator formula. The original failed checks and their corrections
remain beside it.

## Primary-source constraints

The [Yamaha PSS-780 manual, printed p41](https://usa.yamaha.com/files/download/other_assets/1/317511/PSS780E.PDF)
names four SIN TBL forms, but supplies no coefficient table, phase address
width or numerical implementation. Kevin's own
[PSS-680 experiment description](https://diyelectromusic.com/2023/08/02/arduino-pss-680-synth-editor-part-1/)
states that only the carrier table is changed from the Sine Wave voice,
without feedback, modulation or frequency multiplication. The new audit
uses the already retained recording and the original guarded windows;
there is no new acquisition or choice of a more favorable passage.

Yamaha's [US4813326A, FIG22 and its accompanying description](https://patents.google.com/patent/US4813326A/en)
describes a logarithmic sine table, a shifter and logarithm-to-linear
conversion. Shifting a log magnitude by one bit can produce squared sine;
sign and phase gating are distinct subsequent operations. This makes
signed or gated squared-sine generation historically plausible without a
separate analog waveshaping circuit. **The patent does not identify the
YM3420.** Its generic term “operator unit OPU” is not proof that its exact
pipeline, widths or tables are the PSS chip's implementation.

## What the present engine actually generates

For the implemented odd, half-wave-antisymmetric function
`w(x)=sin(x)*abs(sin(x))`, the Fourier sine coefficients are

`b_n = -8/[pi*n*(n*n-4)]` for positive odd n; all even coefficients and DC
are zero. Thus `b_1=8/(3*pi)`, `b_3/b_1=-1/5`, and
`b_5/b_1=-1/35`. Independent numerical integration verifies these
coefficients. Squaring a complete sine without retaining its sign would
instead produce DC and a frequency-doubled component; it is not an
equivalent substitute.

The following numbers are relative to each signal's fundamental:

| Path | H3/H1 | H5/H1 |
| --- | ---: | ---: |
| Exact signed-square formula | −13.979400 dB | −30.881361 dB |
| Actual native engine, circuit off | −13.979400 dB | −30.881361 dB |
| Actual native engine, current sibling circuit on | −14.196168 dB | −31.525688 dB |
| PSS-680 table1, original 29.85–30.20 s window | −13.946544 dB | −54.480387 dB |

The two native one-second stationary notes use the exact previously
measured fundamental, 523.0676963516906 Hz, with no modulation, chorus,
tone filter, Drive, limiter, DC blocker or clock modulation. Only the
existing sibling output circuit toggles; the final 350 ms is analyzed.
Consequently the current modeled circuit does not account for the fifth
deficit in this captured passage. This comparison does **not** establish
the actual hardware output/capture response or prove a ROM error.

The actual C++ waveform is also probed at 65,536 coherent phases and four
fixed PM indices. Its maximum difference from the declared formula is
5.56e−17 at unit amplitude, within floating-point rounding. Its coherent
unmodulated mean is −6.07e−18. These are software properties, not recovered
hardware arithmetic. The engine applies the waveform to the summed
carrier-plus-modulator phase; its envelope/TL gain follows that operation.
An output DC blocker does not establish the internal modulator's DC
handling. Asymmetric PM, feedback and transient phase histories still
need hardware-specific evidence.

## The missing fifth is persistent, and is not stereo cancellation here

At the same frozen frequency, the three equal thirds of the original
table1 window give H5/H1 from −53.64 to −54.24 dB, while H3/H1 stays
between −13.56 and −13.91 dB. No frequency or subwindow search is used.
All four originally analyzed waveform windows have exactly equal left
and right samples. Their midpoint therefore cannot cancel an out-of-phase
fifth harmonic. The **entire recording is not exactly mono**: 1,568 samples
outside these windows differ between channels. Only the measured-window
claim is established.

The half-squared window independently repeats the pattern: H3/H1 is
−12.734585 dB and H5/H1 is −56.769555 dB. Its fixed thirds give fifths
between −55.86 and −56.92 dB. Both ideal squared forms have the same
normalized odd-harmonic coefficients; the half-squared form has half
their absolute amplitudes plus its DC/even harmonics.

## A common capture path is still a live explanation

Conditionally assuming the ideal shapes and a linear time-invariant
downstream path, the response needed at H3/H5 relative to H1 is:

| Passage | Required H3 response | Required H5 response |
| --- | ---: | ---: |
| Full squared sine | +0.032856 dB | −23.599027 dB |
| Half squared sine | +1.244816 dB | −25.888194 dB |

These are algebraic requirements, **not calibrated filter coefficients**.
The phase-origin-invariant response angle, `arg(Z_n)-n*arg(Z_1)-pi`,
differs between the two passages by only 0.019225 radians at H3, about
1.1 degrees. Their H3 magnitude requirements differ by 1.211959 dB;
H5 requirements differ by −2.289168 dB and 0.577386 radians. The close H3
phase and shared fifth deficit are consistent with a common output,
speaker, microphone, effect or capture response. They do not demonstrate
one exactly shared LTI filter: effects, manual playing, changing signal
level and source dynamics remain uncontrolled, and the fifth is weak.

This conditional comparison was requested after the first measurements
and is explicitly a post-observation diagnostic. It reuses the frozen
coefficients, reports every odd harmonic 3..11 and all fixed thirds, and
introduces no new fit, threshold or promotion gate. The independent
HALF² audit may further test cross-wave constraints.

## Implications for fidelity work

The low-order topology evidence remains useful: table1 preserves the
fundamental, strongly favors an odd third over an even second, and is
inconsistent with treating its index as a borrowed OPL2 half-wave table.
It does not establish all partials or bit accuracy. Truncating the formula
to its first and third harmonics merely because that matches this capture
would fit an unidentified recording chain and could change PM sidebands
substantially; that is not a supported correction.

The unresolved digital details are phase addressing, log/linear lookup
coefficients, sign/gating order, attenuation rounding, feedback precision
and native update timing. They are not evidence for arbitrary voltage
drift or analog oscillator instability. A separating public fixture
would give several pitches and levels through a documented direct path,
then carrier-only and modulator-only table changes with identical
controls. Until such evidence constrains the common transfer and internal
PM behavior, neither a fifth-harmonic notch, guessed quantizer nor a new
physical constant should be installed in production.

The final verifier passes 111 scoped software/data checks. An initial
analysis broadcasting error and three overstrong verifier assumptions
are preserved with their actual observations; no audio, model source,
estimator, frequency or window changed to repair them. No shipping DSP,
defaults, presets or product version changes in this audit.
