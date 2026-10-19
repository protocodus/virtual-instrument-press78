# Assumed shared output headroom

This is one deliberately chosen audible hypothesis, authorized as an estimate.
It is **not a recovered YM3420 transfer, calibrated analog circuit, DAC bit depth,
or hardware-fidelity improvement**. Shipping source and defaults remain unchanged.

## Choice and rationale

The exact instrument manual warns that high displayed TOTAL LEVEL and MELODY
VOLUME can distort, particularly with chords. The readable PSS-480 sibling has
biased, low-voltage output stages. The retained carrier-SIN capture contains a
second harmonic near -35 dBc, although the chip, output, speaker, microphone and
capture chain cannot be separated. These observations make shared asymmetric
headroom a plausible experiment. They do not identify its location or constants.

`OutputHypothesis.h` implements the following memoryless, deterministic curve:

```
t = tanh(x / H)
y = H * t / (1 + tanh(b) * t)
```

The **chosen** headroom scale is `H = 1.0` in the engine's normalized mono units.
The **chosen** shape bias is `b = 0.14`, dimensionless. An illustrative sine peak
of `0.25` is one quarter of this headroom scale. It is an audition reference,
not a measured factory level, voltage conversion or fitted recording amplitude.
No value was optimized against the source waveform or benchmark scores.

The curve is equivalent to a biased tanh with its zero-input value subtracted
and its small-signal slope normalized to one. The implemented algebra avoids
subtracting nearly equal tanh values at very low input. For finite real input:

- Zero maps exactly to zero, with unity derivative at zero.
- The mathematical curve is continuous, bounded and strictly increasing;
  floating-point evaluation can round to its limits. There is no gate.
- Positive and negative limiting values differ because of the assumed bias.
- Its quadratic term creates even harmonics; higher input levels also create
  odd harmonics and compression. Several voices excite the same shared curve.

At low levels its expansion is
`y = x - tanh(b)/H*x^2 + (tanh(b)^2-1/3)/H^2*x^3 + ...`.
For the illustrative peak-0.25 sine, these lowest orders suggest H2 of roughly
-35 dBc and H3 of roughly -46 dBc. Those are analytical order-of-magnitude
expectations, **not numerical readbacks, capture fits or acceptance targets**.
The sign of the assumed asymmetry is also a choice. Recorded harmonic phase
does not establish this polarity or the physical bias.

## Native insertion and limitations

The renderer should generate an explicitly marked research copy of
`Press78Engine.cpp` and insert
`mono = press78::research::OutputHypothesis::process(mono);` immediately before
`const double circuit = analog_.process(mono);`. Assert exactly one
insertion. This changes the shared mono signal inside the native output path,
before the existing linear output network, tone/Drive, stereo chorus, DC removal,
master gain and safety limiter. It is not an effect applied to exported WAVs.
Its placement before the sibling filter is a scenario choice, not a traced
target connection. The original/native baseline must use the unchanged source.

There is no startup bias or excitation: silence remains exactly silent through
this component. Signal-dependent mean shift can occur while asymmetric signals
are present, then the existing coupling/high-pass stages determine its tail.
There is no random source, hiss, hum, dither, supply oscillator, fault, memory
corruption or added quantizer. This component does not model power sag or clock
drift and should not be described as having done so.

The curve runs at the existing renderer's output rate, without extra
oversampling or latency. It can produce folded high harmonics when driven hard;
that is a numerical limitation, **not modeled YM3420 alias behavior**. The
intended first auditions are the fixed 48 kHz research renders. All envelope,
waveform, level conversion, chorus and capture limitations remain in force.

For a fair audition, retain the original unscaled output, then create separate
listening copies using one declared RMS gain per complete phrase and common
pair headroom. Loudness compensation must not be inserted into this curve or
used to call the hypothesis more accurate. Direct transfer checks should cover
exact zero, the limiting values, a finite-difference unity slope near zero and
monotonicity; resulting audio should be checked separately for silence, finite
samples, peaks and level dependence. Root owns those checks and audition metrics.

Relevant evidence remains in
[signal-path audit](../../../Docs/research/lofi-signal-path-audit-2026-10-19.md),
[SIN audit](../../../Docs/research/oscillator-sine-audit-2026-10-19.md) and
[Drive/output separation](../../../Docs/research/drive-output-separation-2026-10-19.md).
