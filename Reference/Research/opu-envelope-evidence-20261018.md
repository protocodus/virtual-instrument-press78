# OPU envelope evidence and identifiability - 18 October 2026

No primary source recovered in this bounded pass identifies the YM3420's numerical envelope-rate table, envelope update divider, RR/SRR transformation, finite arithmetic or performance Reverb algorithm. Existing D2/RR observations still justify testing a slower law; they do not establish that the hardware is globally three times slower. This pass adds an algebraic separation of the competing explanations and checks several seemingly relevant sources against their actual contents. No runtime, preset, build or host changes accompany it. Additive noise remains absent.

## What can actually distinguish a rate error from compression

The current model advances attenuation by `96 / (F * 48 * 2^(-r/4))` per internal sample. Multiplying by its `F` samples/second gives:

`decay slope = 2 * 2^(r/4) dB/second`.

Consequently `F` cancels. Replacing the engine's 48 kHz synthesis rate with a suspected crystal-derived rate, while retaining this time-normalized formula, does **not** change envelope duration in seconds. A recovered chip divider would instead need to determine the real update interval and increment law. The current numerical constant 48 is a separate timing assumption.

For this exponential rate law, dividing the slope by three is also equivalent to reducing effective rate by `4*log2(3) = 6.3398500029` codes. A single linear-dB decay cannot distinguish these hypotheses. A memoryless compressor operating at a constant 3:1 ratio maps `output dB = input dB / 3 + constant`; it yields exactly the same threefold slope reduction. Neither explanation requires changing note pitch. More rate settings help detect quantized-rate patterns or a different RR mapping, but alone cannot distinguish a constant timing multiplier from constant compression.

| Existing law / proposed diagnostic | D2R20 | RR8 (assumed effective rate34) |
|---|---:|---:|
| Existing slope | 64.000 dB/s | 724.077 dB/s |
| One-third slope | 21.333 dB/s | 241.359 dB/s |
| Previously measured sibling slopes | about 21.24 dB/s | about 230-233 dB/s |

The approximately 4-5% residual in RR after the simple division remains material. These are calculations against the assumptions in `Press78Engine.cpp`, not recovered Yamaha values. Measurement provenance and caveats remain in the [independent recording audit](recording-holdout-audit-20261018.md).

Attack provides another separator. If the modeled attack's dB curve is `c - A*exp(-k*t)`, a memoryless constant-ratio compressor changes `c` and `A`, while preserving `k`. A genuine time stretch changes `k`. An attack fit must allow free amplitude and offset, select an above-knee interior and retain enough carrier cycles before comparing these explanations. A compressor with detector attack/release, a knee, capture gating, overlapping notes, analog transients or an incorrect assumed attack shape breaks that simple argument. The old short AR41 fits are therefore insufficient to identify either explanation. A numerical identity check reaches 3.6e-15 dB error; that check proves the algebra, not hardware behavior.

A static TL-step recording remains the cleanest separator: the same known raw patch, pitch and velocity at several carrier TL values, with settling time and documented effects. A constant capture gain cannot change level differences. Compression can; a pure timing correction cannot. Slow attacks and additional rates then constrain shape, quantization and RR mapping separately. The [optional capture protocol](hardware-capture-protocol-20261018.md) supplies the needed independently authored fixtures; no hardware execution is claimed here.

## Original editor code is an interface reference

The original [PSS-Revive source](https://github.com/BobanSpasic/PSS-Revive) was inspected at revision `bc0406b10e01be7fde72b8681d963a17c06a5006`. `src/untMain.pas`, `TfrmMain.RefreshGraph`, lines 444-505 constructs envelope drawings by adding `64 - rate` horizontal units for AR/D1R/D2R/RR and `128 - SRR` for the alternative tail. No physical seconds, chip counter, exponential timing table, clock measurement or audio engine appears in this procedure. The README itself lists improved envelope graphics as unfinished work. Thus the drawing cannot calibrate envelope duration or imply a special twofold SRR law.

The project's [hardware/software wiki](https://github.com/BobanSpasic/PSS-Revive/wiki/PSS-x80-hardware-and-software), revision `ba77c3a8d42604fd7c0771dce6d8a7efb6028c9e`, corroborates the related keyboards and shared patch interface, but adds no envelope timing or Reverb implementation. Hardware identity, patch identity and firmware behavior must still be distinguished. These sources are original editor implementations, not silicon documentation.

## Yamaha patents: relevant possibilities, no identified implementation

Yamaha's [US4928569A envelope-shape patent](https://patents.google.com/patent/US4928569A/en), from a 1986-priority family, describes release acceleration below a low-level mute threshold to reduce poorly represented quantized tails. Its example threshold is -60 dB; figures 8/9 and text column 14 show this explicitly. The downloaded 21-page English scan was rendered and inspected, including PDF 7 and 17. It does not identify YM3420, PSS-480/680/780, an OPU clock divider, or a PSS RR table. It is a candidate mechanism for a future cutoff experiment, not evidence that the observed sibling 48 dB truncation is internal. Its 7-bit RR datapath also cannot be equated directly with the documented 4-bit PSS voice field.

The older Nippon Gakki [US4586417A reverberation patent](https://www.freepatentsonline.com/4586417.html) instead describes tone-dependent delay/filter networks and programmable delay-memory processing. It supplies no identification with OPU or a PSS model. Its common manufacturer and general reference to FM do not make it the PSS performance Reverb algorithm. Neither patent licenses copying a threshold or effect into the production model.

## No newly supported OPL/OPK substitution

The original [MAME driver](https://github.com/mamedev/mame/blob/master/src/mame/yamaha/ympsr16.cpp) still declares PSS-480/680/780 without sound, treats its CPU divider as guessed, and marks the YM3420BF internal firmware undumped in its PSR36 region. The retrieved file hash is in the JSON. This is not a working reference for OPU envelopes or performance Reverb. Its external ROM declarations do not document the missing internal behavior.

The [chip investigator's original catalogue](https://www.dtech.lv/techarticles_yamaha_chips.html) distinguishes OPU from OPK/OPK2, OPL2 and OPZ; its OPU entry gives integration/pinout observations, not an envelope rate table. PSS-380/390 material belongs to the OPK line, and the investigator's [OPK research](https://www.dtech.lv/techarticles_yamaha_opk.html) explicitly notes software register updates contributing envelope and LFO behavior there. These facts argue against treating a PSS-380 rate or generic OPL EG divider as an OPU measurement. They do not prove that no internal design blocks were shared.

The bounded English/Japanese queries, source hashes, cloned revisions, inspected page images and arithmetic receipt are recorded in [the JSON ledger](opu-envelope-evidence-20261018.json). No public decap, identifiable low-level OPU register timing investigation or numerical rate table was recovered. This negative result only covers the searches and inspected sources recorded there. The justified next action is a separated capture comparison or a diagnostic rate sweep, with the current assumptions visible; it is not an unmeasured production timing or Reverb replacement.
