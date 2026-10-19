# Output schematic and DAC evidence audit, 18 October 2026

The exact PSS-680/780 overall foldout remains missing from the acquired public evidence. The usable complete output circuit is still the related PSS-480 drawing. This refresh found a concrete numerical deficiency in its native implementation: host-rate bilinear integration darkens the upper spectrum substantially more than the continuous circuit predicts. Correcting that approximation is a supported improvement; inventing a YM3420 DAC format is not.

The user's current requirement excludes **all added noise**. No hiss generator, PRNG excitation, memory corruption, clock whistle, or arbitrary noise floor is recommended here. Noise figures in historical source documents do not override that requirement.

## Exact instrument evidence and bounded search

The [Yamaha PSS-780 service supplement](https://www.manualslib.com/manual/4045165/Yamaha-Portasound-Pss-780.html) directs servicing to the PSS-680 base manual. Its acquired twelve-page scan has no overall foldout despite the cover mentioning one. Page 12, visually inspected from the preserved raster, identifies YM3420BF/C, NJM4558 variants, a 5.5 MHz **ceramic resonator**, and MN3102/MN3206 on AM board VF108000. This establishes the parts involved, without establishing converter resolution, timing, or surrounding analog connections. A resonator frequency is not a DAC update specification.

A newly indexed [original PSS-680 overall-foldout listing](https://www.ebay.com/itm/366559737055), updated in August 2026, is a concrete acquisition lead. The seller says it is photographed folded; the public listing supplies no readable component network. No purchase or external message was made. The [Transanalog catalogue](https://www.transanalog.com/manuals/Yamaha/) also lists the PSS-680 service manual, but explicitly offers mailed copies rather than scanned downloads.

The [Russian manual index](https://pdf-manuals.ru/yamaha/pss680_manuals.html) advertises a 6922 KB document; its current public fetch returned an error, and no PDF was obtained. A [repair-file index](https://www.test.remont-aud.net/load/lcd_pdp_tv/pro_audio/243) lists a 2019 PSS-680 service upload; its public fetch returned 403. These are leads, not acquired schematics. Searches also covered PSR-16, PSR-36 and DSR-500 service material: accessible listings did not provide another complete, readable OPU output path. This is a bounded search result, not proof that no public copy exists anywhere.

The [first-hand PSS-680 teardown](https://katzelectronics.blogspot.com/2015/08/yamaha-pss-680-keyboard-teardown.html) does not trace the analog board. Board photographs or an unverified statement that models are similar cannot justify copying a whole analog topology.

## Documented sibling output path

The complete [PSS-480 foldout posted by its scanner](https://forum.mamedev.org/viewtopic.php?start=10&t=1017) is drawing KEC-11861. The preserved full drawing, buffer crop, and preamp crop were visually checked again. Its FM path is:

| Location | Actual connection/value | Consequence |
| --- | --- | --- |
| OPU / D4 | TB analog output through 47 kohm into IC13 pin 5; pins 6/7 form a follower | Integrated analog OPU output; no external FM DAC identified |
| D4 | IC13 pin 7 through 2.2 kohm into 0.01 uF to ground and IC13 pin 3; pins 1/2 form a second follower | Main passive low-pass pole about 7.23 kHz |
| G3 | One common 1 uF bipolar coupler feeds both 47 kohm FM mixer resistors | Both branches load that capacitor; ideal equivalent is 23.5 kohm |
| G3 | IC12 stereo inverting mixers, each 47 kohm parallel 220 pF feedback | Feedback pole about 15.39 kHz; output polarity is inverted |
| G3 | Separate zeroed-rhythm branches retain their documented 1 uF/10 kohm network | FM-only analysis still preserves the declared mixer circuit |
| G3 / AM connection | 1 uF output coupler to each 10 kohm master-volume-pot top | A second high-pass/loading contribution; endpoint is before the wiper |
| Analog supply | +5A and +2.5 V mixer bias shown | Actual headroom/distortion needs calibrated signal volts and suitable amplifier behavior |

The currently simulated endpoint is the **PSS-480 volume-pot top**. It is neither the full PSS-780 AUX jack nor a complete speaker/headphone chain. The PSS-480 AM circuit has no MN3102/MN3206 chorus, whereas the exact PSS-780 parts list does. Its complete output board therefore cannot be treated as an identical PSS-780 board.

## Converter and BBD limits

[D-tech's first-hand chip investigation](https://www.dtech.lv/techarticles_yamaha_chips.html) identifies the integrated converter and different OPU package variants; its [BF pin drawing](https://www.dtech.lv/files_ym/YM3420_OPU_pinout.png) supports TB/AVDD/AGND and the separate channel pins. Neither provides a converter transfer table, measured audio-update clock, or bit depth. The PSS-480 scanner reports that PSR-36 uses CHA/CHB instead of mono TB, so even another OPU instrument requires its output route to be identified.

The [current MAME driver](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/yamaha/ympsr16.cpp), freshly checked during this audit, is still a skeleton without OPU sound. Its 5.5 MHz / 4 divider is expressly guessed. It cannot supply DAC cadence, quantization, or pipeline behavior. The [ymfm supported-chip list](https://raw.githubusercontent.com/aaronsgiles/ymfm/main/README.md) does not implement YM3420. Importing another Yamaha chip's companding, multiplex schedule, or ladder discontinuity remains speculative.

The manufacturer's [MN3206 datasheet](https://github.com/fmillion/yamaha-pss270/blob/8943bf963f196f20b4e2fc714f15400db578891b/datasheets/MN3206.pdf) was rendered and visually checked at PDF pages 1 and 5 (printed pages 75 and 79). Its 128 physical stages, 10-200 kHz CP and 0.32-6.4 ms delay imply 64 complete CP periods of delay. Its application circuit includes a distortion-minimizing bias adjustment. These facts support a charge-transfer delay with calibrated bias and filtering; they do not identify the actual PSS-780 clock trajectory or justify a fixed hidden distortion control. The manufacturer's application schematic is also not the keyboard schematic.

## A measurable implementation error to fix

`Source/DSP/AnalogOutput.h` currently implements the frozen circuit with six second-order sections produced by **bilinear integration at the host sample rate**. `Press78Engine::prepare()` supplies the host rate directly. Existing coefficient/runtime parity tests correctly prove agreement with that discretization, but do not bound error against the continuous analog network.

This audit compares the native mathematical response against an independent direct descriptor solve, `G + j*2*pi*f*C`, from the preserved component network. It uses no recording, resampler, fitting, or loudness normalization. Negative errors mean additional attenuation relative to the same continuous circuit:

| Host rate / integration factor | 5 kHz | 10 kHz | 12 kHz | 20 kHz |
| --- | ---: | ---: | ---: | ---: |
| 44.1 kHz / 1x current | -0.166 dB | -1.756 dB | -3.217 dB | -24.828 dB |
| 48 kHz / 1x current | -0.138 dB | -1.430 dB | -2.576 dB | -16.100 dB |
| 96 kHz / 1x current | -0.033 dB | -0.312 dB | -0.532 dB | -2.178 dB |
| 44.1 kHz / 4x candidate | -0.010 dB | -0.090 dB | -0.151 dB | -0.583 dB |
| 48 kHz / 4x candidate | -0.008 dB | -0.076 dB | -0.127 dB | -0.489 dB |
| 96 kHz / 4x candidate | -0.002 dB | -0.019 dB | -0.032 dB | -0.119 dB |

At 48 kHz, the current phase error is -8.65 degrees at 10 kHz and -12.83 degrees at 12 kHz; 4x integration reduces those to -0.49 and -0.70 degrees. The previously preserved Python audio reference already uses 4x integration plus resampling. This explains one native/reference difference that circuit-identity uncertainty does not explain away.

The 4x entries above concern the integration filter **alone**. They are not the end-to-end response of an implemented oversampling chain. An adopted change must include and measure interpolation, decimation, latency, state continuity, and CPU cost. Linear interpolation adds its own droop; changing analog integration rate must not accidentally change oscillator rate or claim a recovered YM3420 output clock. Alternatives that reduce continuous-response error without unsafe high-order numerics can be compared against the same descriptor solve.

The next defensible model change is to reduce this known numerical warping while preserving documented topology, loading, polarity and low-frequency behavior. Then compare fixed recording benchmarks and controlled dry-sine/multitone fixtures at 44.1, 48 and 96 kHz. There is insufficient new evidence to change the declared DAC encoding or add converter artifacts.

The accompanying JSON records component-source hashes, explicit unknowns, acquisition outcomes, and sixteen dense-grid integration comparisons. Additional frequency rows are in ignored `build/schematic-audit-20261018/native-continuous-transfer.json`. These results identify a software approximation error within a documented sibling circuit; they do not prove the missing PSS-780 AUX transfer.
