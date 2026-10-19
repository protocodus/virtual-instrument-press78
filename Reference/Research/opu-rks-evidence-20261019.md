# OPU rate-key-scaling evidence - 19 October 2026

**Raw RKS0 does not yet prove pitch-flat OPU envelope timing.** The original Yamaha manuals establish its two-bit encoding and name without a zero-setting rule or rate equation. A firsthand PSS-480 tutorial describes zero as off, which is useful counterevidence to a minimum-nonzero interpretation. That description is not a controlled timing measurement and does not exclude an independent baseline pitch dependence elsewhere in the chip.

This pass changes research records only. It does not change DSP, factory data, the capture kit, native resources, version, host state or noise behavior. Cross-note slope measurements are a separate investigation; no new audio-rate measurement is claimed here.

## Original manufacturer pages

These scans were rendered and visually inspected, including the field boundaries and graph captions:

| Instrument/source | PDF page, one-based | Printed page | What is established |
| --- | ---: | --- | --- |
| [PSS-780 original Yamaha manual](https://usa.yamaha.com/files/download/other_assets/1/317511/PSS780E.PDF) | 44 | 41 | Raw bytes7/8 use bits7..6 for RKS beside six-bit AR; RKS is named rate key scaling |
| [PSS-680 manual mirrored by an editor author](https://github.com/artaslove/PSS-680/blob/master/pss680.pdf) | 45 | 41 | Same RKS field and name |
| [PSS-480 Spanish manual, Yamaha English MIDI appendix](https://usa.yamaha.com/files/download/other_assets/1/317521/PSS480S.pdf) | 45 | Add-1 | Same RKS field and name |

None of these pages says RKS0 is disabled, provides RKS0..3 curves or identifies the key-code-to-effective-rate calculation. The keyboard graph is explicitly **level** key scaling, LKS(LO)/LKS(HI), rather than a rate-scaling graph. Its flat LKS0 line cannot be used as an RKS0 timing specification. The generic envelope drawing identifies AR/D1R/D2R/D1L/RR/SRR without a numerical time scale.

The PSS-480 web extractor incorrectly presents some field widths as four columns. Inspection of the original scan confirms the two-bit RKS field; automatic table extraction is not the basis for that conclusion.

## Editor implementations and firsthand tutorial

[PSS-Revive](https://github.com/BobanSpasic/PSS-Revive/blob/bc0406b10e01be7fde72b8681d963a17c06a5006/units/untPSSx80Voice.pas#L194) directly masks RKS to0..3 and shifts it into the upper two bits of the operator AR byte. [PortaSound JS](https://github.com/mmontag/portasound-js/blob/a9e312623191db1922583f31981f824bec081f36/src/portasound.js#L97) likewise exposes four values in raw byte7/8 at bit6, defaulting to0. The retained original Ctrlr panel packs `64*RKS + AR` and reads RKS with a six-bit right shift. Its D1L field is explicitly inverted, whereas RKS is not.

These independent editor implementations support **displayed0 equals raw0**. They transport parameters to hardware; they do not implement or measure an OPU effective-rate function. Their default values and envelope drawings therefore cannot validate a pitch-flat envelope simulation.

Keen On Keys' [PSS-480 editor demonstration at 10:10](https://www.youtube.com/watch?v=2TfpcAmaPGg&t=610) is more specific: its retained automatic English captions describe four settings and include **“0 is off”**, followed by1 being faster and3 maximum. The captions are YouTube automatic captions, not an author-supplied transcript. This is a firsthand tutorial interpretation, not a manufacturer specification or a verified numerical rate table.

Freshly decoded frames at source610 and650 seconds show the modulator RKS changing from0 to3 while carrier RKS stays0. The visible patch has substantial FM modulation. It is not an isolated pure-carrier comparison of rawRKS0 at several known pitches. The tutorial consequently supports the intended meaning of the adjustable RKS control without proving that the entire envelope engine has zero residual pitch dependence at raw0.

## Consequence for the current model

`Source/DSP/Press78Engine.cpp` currently uses `rateScaling = {0, 0.0625, 0.125, 0.25}` and an effective-rate correction around MIDI60. At raw0, that correction is identically zero. This is a modeling assumption, not a recovered OPU law. Neither the coefficient spacing nor the MIDI60 reference is established by the source pages reviewed here.

The evidence supports keeping three claims separate:

- The raw RKS field has four direct settings: established.
- The adjustable contribution is intended to be off at0: supported by captioned firsthand narration, with limited verification.
- The complete OPU rate is exactly independent of note at raw0: unverified, as is the contrary claim of a minimum nonzero baseline.

An unrelated Yamaha chip's baseline key-code contribution cannot settle this question. A faster release at a high pitch with the same rawRKS0 would require investigating intrinsic key-rate behavior, effective-rate quantization, patch interpretation, component interference and capture effects before attributing all endpoint-time differences to an attenuation cutoff.

The useful next capture is one independently authored pure carrier, muted modulator, LKS0, fixed TL and velocity, dry effects, and several known pitches at rawRKS0. Repeat at RKS1..3 and measure interior D2/key-off slopes rather than disappearance time alone. Preserve unchanged gain, full raw settings and actual gate uncertainty. This can identify whether pitch dependence remains at0 and whether the higher settings add a linear, stepped or other correction. No hardware execution is implied by that proposal.

The [machine-readable source ledger](opu-rks-evidence-20261019.json) binds original PDFs, inspected renders, editor commits and relevant lines, video/caption metadata and the current implementation hash. Source scans, editor checkouts and frames remain ignored under `build/opu-rks-evidence-20261019`. The finalized DAC endpoint ledger was left untouched.
