# SIN oscillator audit — 19 October 2026

The current SIN table is a useful analytic approximation, but is not a recovered
YM3420 oscillator. A new bounded reanalysis establishes a more specific
constraint: the retained pure-SIN capture's coherent second harmonic cannot be
explained by a **static, half-wave-symmetric sine lookup table and symmetric
amplitude quantizer alone**. It does not identify whether that asymmetry belongs
to the chip, analog output, speaker, microphone, or recording. No production DSP,
preset, default, package or artificial noise changed.

The [machine-readable audit](oscillator-sine-audit-2026-10-19.json) retains all
72 capture fits, all 99 synthetic candidates, original input hashes, the frozen
protocol and implementation bindings. The
[probe](../../Tools/prototypes/oscillator-sine-audit-20261019/README.md) reads
only the original local PCM and emits no audio.

## What the available primary sources establish

Yamaha's [PSS-780 owner manual](https://usa.yamaha.com/files/download/other_assets/1/317511/PSS780E.PDF),
printed pp26–28 and41, describes digital operators, the unmodulated Sine Wave
voice, and four table selections. Its operator terminology does not support
replacing SIN with an analog VCO circuit. It does not give sine-ROM contents,
phase/address width, arithmetic rounding, phase-reset rules or native synthesis
update rate.

A newly examined Yamaha patent,
[US4813326A](https://patents.google.com/patent/US4813326A/en), priority1984,
describes a useful implementation family in Fig22: phase-addressed logarithmic
sine data, shifts, logarithmic-to-linear conversion, phase-section gating and
sign control. It also describes sharing one operator circuit over time. This
provides an architectural lead for digital reconstruction. **The patent does
not identify YM3420 or PSS-780.** Its generic abbreviation “OPU” is insufficient
to establish that the target chip implements that embodiment, its four table
mapping, or any numerical width. No patent-derived constants are adopted.

[Kevin's original PSS-680 procedure](https://diyelectromusic.com/2023/08/02/arduino-pss-680-synth-editor-part-1/)
states that the Sine Wave voice has no feedback, modulation or frequency
multiplication and that only the carrier's table field is changed. The existing
[recording audit](recording-holdout-audit-2026-10-18.md) supplies independently
retained acquisition metadata and cautiously validates the four broad shapes.
It supplies no guaranteed direct, unprocessed, dry capture or DAC calibration.

## New fixed-window result

This is a new analysis of previously inspected material, **not an untouched
holdout**. Before executing it, the adjacent protocol froze the original
10.50–10.85second table0 window, its seven contiguous50ms subwindows, all
three channels, the original523.066373737Hz frequency, and three nuisance
orders. No new frequency search, crop selection, EQ or harmonic correction was
allowed. Each fit uses 12 joint harmonic sine/cosine pairs plus DC. Additional
orders add slow fundamental-only linear/quadratic amplitude/phase terms.

| Measurement | H2/H1 | H3/H1 |
|---|---:|---:|
| Original full-window basis, reproduced | −35.4180dB | −46.8485dB |
| Full window, quadratic fundamental nuisance | −35.4320dB | −46.8625dB |
| All seven subwindows and all nuisance orders | −36.3722…−34.5934dB | −47.1684…−45.2563dB |

The second harmonic persists in every declared interval. Its phase relative
to twice the fundamental phase ranges −0.7402…−0.5316radians across the
subwindows. These are overlapping single-session diagnostics, not independent
hardware observations. The selected window's left and right channels are
bit-identical, so the three channel fits provide no stereo corroboration.

The full-window residual remains substantial:3.9496% unweighted RMS with the
original basis. More nuisance terms lower the weighted fitting objective
slightly, but worsen the unweighted full-window residual to4.2418%; no claim
that this solves capture nonstationarity is justified. Tiny regression precision
cannot be interpreted as chip precision.

## Separating static digital quantization from the captured asymmetry

If a periodic waveform obeys `q(phase + pi) = -q(phase)`, its DC and even
Fourier coefficients vanish. Uniform phase addressing with a mirrored signed
sine table preserves that identity. Applying an odd, symmetric amplitude
quantizer preserves it too, irrespective of their unknown widths. An LTI
output filter cannot create absent harmonics.

The bounded probe constructs99 combinations:6–14 phase-address bits and6–16
symmetric linear amplitude bits, using65536 points per phase cycle. Every
candidate has exact half-wave antisymmetry and exactly zero computed DC/even
harmonics. An intentionally asymmetric quadratic **test fixture**, with
arbitrary alpha0.04, returns H2/H1=0.02 (−33.9794dB), exactly its analytic
prediction. All298 declared synthetic checks pass. The candidate widths are
examples for the invariant, not proposed Yamaha specifications.

This excludes attributing the recorded approximately1.7%-amplitude H2 directly
to ordinary symmetric *static* lookup/amplitude quantization. It does **not**
exclude a chip with an asymmetric table, phase-section logic, asymmetric
conversion or folded high-frequency images. In particular, the proof concerns
the phase-domain waveform; it does not simulate native-clock sampling and
alias folding, whose cadence is unknown. Time variation and recording
nonlinearity also remain possible. No converter bit depth or asymmetric drive
coefficient can be estimated from this observation alone.

## Current implementation and next useful step

`Source/DSP/Press78Engine.cpp` currently computes SIN with `std::sin` from
double phases, advances at48kHz, and wraps phase with `fmod`. It has no
recovered finite-address sine ROM, log-to-linear table or native update
schedule. Firmware pitch-command precision is separately evidenced in the
[pitch ledger](opu-pitch-command-path-2026-10-19.md); its13-bit packed FNUM
does not establish phase-accumulator width. The
[clock/circuit ledger](opu-sibling-clock-circuit-2026-10-19.md) likewise does
not identify an FM divider.

The next separating evidence is a matched pure-carrier level series at several
pitches with unchanged capture gain, exact patch bytes and individually
disabled effects; a direct electrical output is preferable. Constant normalized
harmonics, level-dependent asymmetry and pitch-dependent aliases make different
predictions. Without such data or target internal documentation, adding a
coarse sine table to sound “older” would substitute a new assumption for the
current approximation. The new constraint instead prevents mistaking captured
even distortion for proof of symmetric ROM quantization.
