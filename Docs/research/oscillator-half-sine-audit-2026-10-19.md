# HALF operator waveform: DC placement and what the recording can identify

The current HALF table, index 2, implements `max(sin(phi), 0)` correctly as a
mathematical half sine. Its positive mean is retained inside FM modulation.
That mean is **not established as an OPU hardware bias** by the available
recording. Moving DC removal into the operator would make a substantial new
synthesis assumption, and the existing final output DC filter cannot stand in
for it. No production DSP was changed.

The new [source-bound native probe](../../Tools/prototypes/oscillator-half-sine-audit-20261019/README.md)
passes **1,033,114 assertions**, including 36 actual native `Voice::next`
cases. The [JSON record](oscillator-half-sine-audit-2026-10-19.json) binds its
prospective protocol, implementation, first-run receipt, engine and retained
recording metadata. This is new verification of a consequential internal
placement constraint; it is not a new hardware match score.

## Primary sources and limits

The exact [Yamaha PSS-780 manual](https://usa.yamaha.com/files/download/other_assets/1/317511/PSS780E.PDF),
printed p41, assigns SIN TBL 2 to Sine Half Wave. It names the table but does
not state its sample values, numerical widths, zero representation, DC
compensation, or the internal handling of that mean. The retained manual
SHA256 is `e1382c76aa9f6351fb3de191228b3209def0cf4ceba54ca6a20406c1e2db0adb`.
The primary PDF was opened through the browser during this audit; no new
manual or recording was downloaded.

Kevin's [original PSS-680 experiment](https://diyelectromusic.com/2023/08/02/arduino-pss-680-synth-editor-part-1/)
changes **only the carrier** table of the Sine Wave voice, without feedback,
modulation or frequency multiplication. The independently retained
[recording audit](recording-holdout-audit-2026-10-18.md) identifies the guarded
table-2 interior as 39.12–39.32 seconds. Part 2 changes multiple parameters,
including modulator table, and provides no isolated, timed modulator-mean
comparison. Neither demonstration supplies numerical OPU arithmetic.

Yamaha's [US4813326A](https://patents.google.com/patent/US4813326A/en) describes
phase-dependent gating of sine data, including a modulator path in Fig 9:
gated sine data is scaled by a modulation index and added to carrier phase.
This establishes that retaining a gated waveform in the modulation path is a
documented Yamaha design option. The patent does not identify YM3420 or prove
its selected implementation. No patent bit width or circuit detail is copied
into the engine from this analogy.

## The exact mathematical constraint

For the ideal half sine `h(phi) = max(sin(phi), 0)`, the Fourier series is

```text
h(phi) = 1/pi + (1/2)*sin(phi)
         - (2/pi)*sum_{k=1..infinity} cos(2*k*phi)/(4*k*k-1).
```

The native helper's mean is 0.31830988616855949; error against `1/pi` is
1.52e-11 using 262,144 equally spaced samples. All 12 checked Fourier
coefficients differ from the analytic values by at most 3.05e-11. This numerical
integration resolution is a test choice, not evidence of an OPU table size.

The retained carrier recording agrees with the broad parity pattern: its third
harmonic is 43.72 dB below the fundamental, with a prominent second harmonic.
It does **not** reproduce the ideal partial amplitudes:

| Partial | Ideal relative to H1 | Retained capture | Capture minus ideal |
| --- | ---: | ---: | ---: |
| H2 | −7.444 dB | −2.725 dB | +4.719 dB |
| H4 | −21.424 dB | −25.048 dB | −3.625 dB |
| H6 | −28.783 dB | −42.688 dB | −13.904 dB |
| H8 | −33.889 dB | −41.067 dB | −7.179 dB |

These unequal deviations rule out treating one overall gain change as an exact
match. They do not identify a replacement oscillator curve: electrical/capture
response, effects, lossy encoding, changing signal level, and the OPU table are
not separated. The old harmonic observations and source window are reused
unchanged; there is no new partial fitting or source selection. In particular,
the H2 excess must not become a guessed DAC distortion coefficient.

## Operator mean and output DC removal are different

At zero feedback, the current source evaluates a sine carrier as

```text
y_raw = sin(phi_c + K*g*h(phi_m)),       K = 8*pi
```

where `g` contains the modulator envelope, TL, velocity and AM. A hypothetical
mean-subtracted operator would evaluate

```text
y_centered = sin(phi_c + K*g*(h(phi_m) - 1/pi)).
```

The lookup phases differ by `K*g/pi = 8*g` radians. For a constant envelope
this is a fixed phase rotation; it is **not steady detuning**. With a varying
envelope, the mean contribution has phase derivative
`(4/pi)*dg/dt` Hz under the current index scale. That is a derived phase
contribution, not a prediction that the perceived pitch follows it. With
coherent carrier/modulator ratios, a constant rotation can also change
interference between overlapping spectral terms. Unknown note-on phase makes
that another unmeasured state.

The native probe checks 36 combinations of three TLs, three notes and four
integer carrier/modulator ratio pairs over 4,800 ticks each. Actual output
matches the unipolar equation to 1.43e-15. A separate arbitrary synthetic
gain ramp verifies the phase and derivative identities; the measured residual
steady derivative is below 2.18e-10 Hz. Neither fixture estimates a hardware
envelope, TL law or modulation-index scale. Feedback is excluded: once the
lookup phase itself is warped by feedback, the simple uniform-phase mean
argument cannot be carried over unchanged.

In the source, `Voice::next` feeds the operator directly into the carrier
lookup. The 10 Hz DC filter comes after voice mixing, the optional PSS-480
small-signal surrogate, tone filtering, creative Drive, and chorus. There is
no individual operator DC-block stage. The surrogate's own coupling behaviour
is separate from that explicit final filter.

Two direct probes of the actual final output function expose the distinction:

- Feeding `h` and `h - 1/pi` as carrier-only held inputs produces a difference
  of `(1/pi)*r^n`, exactly the DC-filter startup response. Agreement with that
  closed form is within 2.06e-15; the final difference after one second is
  5.56e-17. Thus those two steady inputs cannot be distinguished from their
  settled AC output alone.
- Feeding carrier outputs generated with the two different **modulator** mean
  choices remains different after the same output DC filter. A fixed synthetic
  125 Hz 1:1 fixture, modulator gain 0.2, gives relative RMS difference 1.903
  over the final half second. This establishes noncommutation, not an audible
  hardware error magnitude, preference, or promotion score.

The retained carrier-only stable-window metrics therefore do not decide
internal modulator mean handling. A known envelope transient could provide
additional information, because a varying output mean is not constant DC;
the present manual-gate/capture metadata does not isolate that experiment.

## What would separate the remaining hypotheses

A documented sibling recording could settle more than a new guessed circuit:
hold carrier sine and all effects off, feedback zero, preserve one known
carrier/modulator phase policy, change only modulator SIN TBL 0→2, and record
matched static TL plateaus plus an independently documented envelope change.
For harmonic ratios, compare complex partials and the phase-dependent
interference, rather than just note frequency or a final DC measurement.
Captured raw SysEx, actual note gates, direct line output and an unchanged
capture chain are needed to avoid trading mean handling against unknown
modulation scale, phase reset, gate dynamics or compression. This is a source
search/measurement requirement, not a request for hardware access.

Until that evidence exists, preserve the mathematically consistent HALF
waveform and explicitly classify its internal mean handling as a hypothesis.
There is no support here for added noise, invented quantization, a random
operator offset, or promoting a generic Yamaha patent to a detailed YM3420
circuit simulation.
