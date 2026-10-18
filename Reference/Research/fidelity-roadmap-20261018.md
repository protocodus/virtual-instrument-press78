# Press78 fidelity requirements and current evidence

The active objective is a premium, synth-focused PSS-780 model, validated against public circuit documentation and real recordings. A claim that it is the market's most accurate model remains unproven. This ledger preserves that full objective while recording concrete progress; neither passing software contracts nor a better score on one reused video completes it.

## Current evidence-backed work

- **Operator waveforms:** a newly acquired PSS-680 carrier-only table experiment supports the current four waveform identities, including signed squared sine. It does not identify numerical ROM precision or DAC encoding. See [recording audit](recording-holdout-audit-20261018.md).
- **D1 envelope endpoint:** the zero-height D1 stage no longer takes an unwanted decrement before D2. Controlled sibling behavior and explicit model endpoint tests support this bounded correction; factory changes are small. See [FM audit](fm-fidelity-audit-20261018.md).
- **Modulation:** reused PSS-780 pitch contours support about 5.24 Hz triangle modulation, with approximately 12.5 cents at PMS3 and 100 at PMS6. The frozen candidate improves pitch tracking on separately acquired PSS-580 Saw and Human Voice passages, with patch-identity and per-passage phase qualifications. Unobserved sensitivity levels and exact reset/delay rules remain hypotheses. See the [pitch audit](lfo-pitch-audit-20261018.md), [preregistered candidate](lfo-candidate-protocol-20261018.json) and [independent recording evaluation](recording-holdout-audit-20261018.md).
- **Analog integration:** the documented PSS-480 surrogate has a validated4x research component. End-to-end interpolation/circuit/decimation reduces its48kHz10kHz numerical magnitude error from1.43dB to0.076dB against the same continuous network. A tested80-host-frame matched-delay integration was rejected as the instrument default after it worsened75/100 PSS-780 comparisons. The shipping path retains its prior32-tick latency. Numerical accuracy to the sibling circuit does not establish exact-device agreement. See [schematic audit](output-schematic-audit-20261018.md) and `Tests/results/analog-oversampled.json`.
- **No added noise:** white and circuit-noise generation remain absent. Legacy noise properties are hidden/inert. Fidelity research does not override the user's explicit removal requirement.

## Requirements still needing stronger evidence

| Requirement | Evidence needed | Current status |
|---|---|---|
| Envelope attack/decay/release law across rate and pitch | Known raw patches, MIDI gates, several rates, static TL steps, independently disabled effects and known capture dynamics | New controlled sibling clips expose large timing mismatches, but compression, global Reverb and gating are unresolved. A blind threefold timing multiplier is not adopted. |
| Human Voice1 Reverb-dependent tail | Matched Reverb off/on, Sustain off/on recordings at fixed gates and pitches | Exact manual confirms separate states; implementation remains unidentified. |
| Pitch modulation transfer and phase | Multiple known PMS/VDT values, long isolated notes, overlapping notes and retriggers on another unit | Stronger candidate and independent data obtained; all sensitivity/phase/delay behavior is not recovered. |
| DT1, key level/rate scaling, feedback and velocity | Controlled parameter sweeps with raw dumps over pitch/velocity ranges | Existing smooth transfer laws remain assumptions. |
| OPU synthesis clock, pipeline and arithmetic | Chip documentation or separated alias/phase/quantization measurements | Exact divider, lookup widths, accumulator rounding and DAC code transfer unknown. Other Yamaha chip families cannot substitute for this evidence. |
| Exact PSS-780 output/chorus circuit | Complete PSS-680/780 foldout or trace, measured dry/wet transfer and operating levels | Exact parts known; PSS-480 output surrogate and empirical Recorded chorus remain explicitly labeled. |
| Broad recording agreement | Multiple independent exact-device recordings, controlled and expressive material, fixed protocols and blinded auditions | Original100-preset tour is reused regression material; new sibling captures add independent constraints but do not establish exact-device agreement. |
| Premium realtime behavior | Cross-rate/state/automation/silence/reset contracts, resource limits, target builds, actual host playback and persistence evidence | Native/component/host stages are tracked separately; b11 native, wrapper, package and protected Recon creation/conversion gates pass. Interactive playback and persistence remain unverified. |
| Market-leading accuracy | Reproducible relevant product comparisons against the same hardware conditions, with fair controls | Not established. A public product search found related OPLL/OPL2/OPK2 products, not evidence that an OPU accuracy ranking has been measured. |

## Market scope

[Plogue's own PortaFM page](https://www.plogue.com/products/chipsynth-portafm.html) identifies its current supported engines as OPLL/YM2413, OPL2/YM3812 and OPK2/YM7129. [discoDSP's own OPL page](https://www.discodsp.com/en/opl/) identifies an OPL2/partial-OPL3 instrument. These are relevant portable-FM comparators, but neither page establishes an exact YM3420/PSS-780 model. This bounded search is not proof that no other competitor exists and does not justify a superlative accuracy claim.

Completion requires measured agreement in the still-open behaviors above, plus complete instrument validation. Each further change should preserve raw source/capture provenance, separate calibration from evaluation, retain regressions and explain what is still unidentified.

The [optional controlled capture protocol](hardware-capture-protocol-20261018.md) prepares the next envelope investigation: independently authored pure-carrier voices, fixed gates, TL/rate sweeps and four matched Reverb/Sustain conditions. Its six MIDI files and 60 cases pass file-format, checksum and schedule validation. Generation performs no playback; deliberate use writes user bank 5 and requires the documented backup. No hardware measurements have yet been made with this kit.
