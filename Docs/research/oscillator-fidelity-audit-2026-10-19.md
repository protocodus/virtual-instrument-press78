# Four-waveform and nonlinear-output fidelity audit — 19 October 2026

The four separate waveform investigations find consequential constraints, but do not establish a circuit-accurate YM3420 oscillator. The current engine still uses analytic waveforms and floating-point phase. New research code now checks the actual native implementation, the retained capture coefficients, and the separation of FM feedback, shared Drive and output limiting. No production DSP, preset, default or noise path is changed by this research branch.

## Four waveform investigations

| Waveform | Current implementation | New bounded result | What remains unidentified |
|---|---|---|---|
| [SIN](oscillator-sine-audit-2026-10-19.md) | `sin(phi)` | Captured H2 remains about −35 dBc across all seven fixed subwindows. Static half-wave-symmetric lookup and symmetric amplitude quantization alone preserve zero even harmonics. | Source/capture asymmetry, native-clock alias folding, ROM contents and arithmetic widths. |
| [SIN²](oscillator-signed-square-audit-2026-10-19.md) | `sin(phi)*abs(sin(phi))` | H3 agrees closely, but captured H5/H1 is −54.48 dB versus −30.88 dB from the actual engine, or −31.53 dB with its current sibling output circuit. | The approximately 24 dB deficit cannot be assigned to ROM or DAC: the output/speaker/capture transfer remains uncontrolled. |
| [HALF](oscillator-half-sine-audit-2026-10-19.md) | `max(sin(phi),0)` | Its mathematical mean is `1/pi`. The native modulator retains that mean inside carrier phase modulation. A final output DC filter cannot substitute for changing that internal placement. | Physical OPU mean handling, especially during an envelope or feedback transient; stable carrier-only recordings cannot decide it. |
| [HALF²](oscillator-half-squared-audit-2026-10-19.md) | `max(sin(phi),0)^2` | Mean `1/4`; odd coefficients are half the signed-square coefficients. More generally, phase-half gating of any shared antisymmetric table preserves normalized odd coefficients. Captured H3 differs by +0.458…+1.280 dB across the fixed support pairs. | Whether the same internal table/gate is used. Estimated pitches and unknown capture/effect response prevent an unconditional common-filter rejection. |

At a matched pitch, one shared LTI response preserves the **cross-table equality** of normalized odd spectra and relative harmonic phases. It need not preserve an individual waveform's unfiltered phase-invariant value. The HALF² audit keeps the actual unequal frequency estimates and does not invent a physical smoothness bound. Weak fifth and higher partials are particularly vulnerable to the substantial capture residual; their numerical regression precision is not hardware precision.

The previous low-order evidence supports broad table families. It does not verify every partial, the log-to-linear pipeline, phase/address precision, attenuation rounding, feedback delay/precision, native update cadence or operator state transitions. Yamaha patent [US4813326A](https://patents.google.com/patent/US4813326A/en) provides a primary-source digital log-sine/power/gating architecture lead; it does not identify the YM3420 or license adopting its numerical embodiment as the target.

A [bounded follow-up source search](target-primary-route-search-2026-10-19.json) records 16 queries and 12 primary-source routes. Additional Yamaha patent-family pages, US4766795A and accessible text from the 1987 Yamaha LSI catalogue do not establish target-chip arithmetic or timing. Failed catalogue/index access is recorded separately from inspected material. The receipt is published unchanged after the search; its `new_public_document_created:false` flag describes the original search pass, before this later publication copy. This negative result does not prove that target documentation is unavailable elsewhere.

## Drive and physical output distortion

The [new native output study](drive-output-separation-2026-10-19.md) freezes 72 public-API cases. Independent per-voice FM feedback and the linear sibling output preserve chord additivity within float-output error. Shared Drive and the safety limiter break additivity, and their gain-placement responses differ. Increasing the plug-in MasterGain from 0.25 to 2 changes no non-limiter normalized waveform; it does activate the limiter in the declared loud cases. This is a measurable distinction among current processing stages, not a reconstruction of Yamaha's MELODY VOLUME circuit.

Yamaha's exact manual separately describes operator-feedback fuzz and level-dependent overload. Its qualitative loud-level warning does not locate the overload in digital summation, DAC, buffer, mixer or power amplifier. Creative tanh Drive and protective limiting must remain separately labelled until electrical or controlled capture evidence identifies the actual nonlinear transfer and signal level. A newly checked sample-pack author explicitly describes a defective unit with fuzz/static; those samples are not a healthy-target distortion calibration.

The [target-board trace reassessment](target-am-net-trace-2026-10-19.md) also remains negative: the current photo registration/contact uncertainty does not uniquely identify pads. Conditional copper/pinout matches are retained, but there are zero accepted new named nets or value-to-pin associations. No clock, BBD bias, converter width, supply coupling or clipping coefficient is inferred from proximity.

## Envelope investigation status

The [read-only PM-v2 state audit](pm-envelope-v2-status-2026-10-19.md) finds the original process and tool handle missing. There are 73/93 completed coarse controls, no nested-grid completion and no final result. All eight prospective informative controls fail the required joint late carrier/beta precision gate. The termination cause is unknown; the original run is preserved and not restarted. No source decoding or new envelope inference is performed.

A separate [matched-level Bass diagnostic](bass-matched-level-decay-2026-10-19.md) reuses 16 saved fundamental-amplitude curves. Exact sample-center brackets give every high-pitch example a shorter −22 to −26 dBFS traversal duration than every low-pitch example, with a minimum pairwise separation of about 5 ms. This constrains the narrow hypothesis of identical intrinsic constant H1 decay rates followed by one shared static scalar H1 mapping. It does not identify a carrier-envelope, RKS or distortion law: fitted H1 magnitude errors, changing FM timbre and unknown capture/patch processing remain unresolved. The original interpolated-slope limitation and a floating-timestamp comparison failure are preserved alongside the separately frozen exact-sample correction.

## Implementation and completion boundary

This round implements bounded native and numerical research probes and records new constraints on model selection. It does not improve the shipping sound by adding a guessed quantizer, fifth-harmonic notch, internal DC compensator, reverb law or generic analog grit. Those would require the currently missing separating evidence. The complete objective—verified envelope behaviour, target converter/output nonlinearity and well-reconstructed digital operators—remains active and unproven.

No release or host installation is performed by this research round.

## Independent review

The [independent waveform review](../validation/waveform-independent-review-2026-10-19.json) passes 783 scoped checks, including source/artifact bindings, all 16 copied coefficient rows, 96 cross-ratio/slope calculations, 80 phase orientations and adaptive integration of the four Fourier formulas. It does not repeat native audio rendering or capture extraction; those evidence levels remain separate.

The [independent Drive/PM review](../validation/drive-pm-independent-review-2026-10-19.json) passes 984 scoped checks across 193 file bindings. It confirms the incomplete PM run and its failed necessary precision gate, the 72-case Drive grid, source/API placement and independently recomputable spectral aggregates. The Drive experiment discarded its PCM after measurement: this review therefore cannot independently recompute sample-derived waveform errors or certify the recorded PCM hashes. It performs no replacement render or PM run.

The [independent Bass diagnostic review](../validation/bass-matched-level-independent-review-2026-10-19.json) verifies the saved-curve arithmetic, all 1,296 reconstructed extraction centers, the original slope limitation, the exact-sample correction and the final report bindings. It confirms the conditional duration result without identifying a physical envelope or distortion law. Its source-header/hash provenance check does not decode PCM samples; the analysis runners use existing JSON and text only.
