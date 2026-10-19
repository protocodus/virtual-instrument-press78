# Lo-fi signal path, distortion and supplies - 19 October 2026

Removing additive noise does not imply an ideal, clean output path. Yamaha explicitly documents level-dependent distortion, and the readable PSS-480 sibling circuit contains separate supply filtering, low-voltage opamp stages and an AN7148 power amplifier. These are concrete directions for further modeling. They do **not** yet identify the target PSS-780 AUX transfer, converter resolution, a normal amount of power sag, or a calibrated nonlinear default.

This is a source and circuit audit, not a new hardware measurement. No DSP, controls, presets, packages or noise behavior changes. The [JSON receipt](lofi-signal-path-audit-20261019.json) records sources, exact observations, crop coordinates, derivations, acquisition outcomes and hashes. Third-party documents and images remain in ignored research storage.

## Existing evidence reviewed first

The [output audit](output-schematic-audit-20261018.md), [exact-circuit search](exact-circuit-source-search-20261019.md), [DAC endpoint study](dac-endpoint-evidence-20261019.md) and [clock/circuit note](opu-sibling-clock-circuit-20261019.md) already establish the important boundary: the complete acquired drawing is PSS-480 KEC-11861, while the acquired PSS-780 supplement ends at its parts list. The target AM board is VF108000 and includes MN3206/MN3102 chorus; the PSS-480 drawing has no such chorus. Its analog route is a useful surrogate, not an identical target board.

The earlier low-level tone endings do not recover DAC bits. Two encodes reproduce them, but share an unknown upload master. Neither an arbitrary quantizer nor a random memory/supply disturbance follows from those observations. The existing BBD discussion also distinguishes its manufacturer THD conditions from the actual keyboard's unknown signal volts, clock, bias and filters. Those limits are retained here.

## The exact manual confirms overload, without locating it

Yamaha's [PSS-780 owner's manual](https://www.nurykabe.com/dump/docs/PSS/manuals/PSS-780_00.pdf), printed pages 11 and 29, warns of distortion with high front-panel TOTAL LEVEL and maximum MELODY VOLUME, including chords. The recommended remedy is to lower those settings. This is direct exact-model evidence for a level-dependent limitation; it is not merely an owner's preference for a vintage sound.

Here TOTAL LEVEL is the front-panel **loudness display**, not raw operator-TL attenuation. A raw attenuation value of 90 must not be used as the overload threshold. The linked Ctrlr panel maps its Level display using `TL=max(99-display,0)`; this pass does not independently execute the physical TOTAL LEVEL firmware macro.

The manual does not locate the limitation in digital summation, the integrated converter, a buffer, mixer or amplifier, nor supply its threshold in volts. Printed page 4 documents the battery/adaptor arrangement and low-battery indication; it supplies no sag transfer law. Printed page 8 distinguishes AUX and headphones and advises reducing keyboard VOLUME for a stereo connection. That advice does not establish the AUX tap's circuit location.

## Newly traced sibling power and output domains

The [original scanner's PSS-480 drawing](https://forum.mamedev.org/download/file.php?id=323), posted in the [MAME investigation](https://forum.mamedev.org/viewtopic.php?start=10&t=1017), was inspected at original resolution. The following are direct drawing observations, rather than inferred PSS-780 wiring:

| PSS-480 location | Observed network | Modeling consequence |
| --- | --- | --- |
| AM power input | DC input marked 9-12 V, battery input, power switch, protection diodes and suppression coils | Input source impedance and battery state are not specified by the voltage label |
| AM regulator | A common output labeled +5A/+5D, Tr1, 6.2 V ZD1, two 150 ohm resistors, a 100 uF reference-network capacitor and 470 uF rail capacitors | FM/preamp and logic do not simply see the full adapter excursion; reference current, dropout and load remain unknown |
| OPU IC1 | AVDD pin 41 receives +5A through 47 ohms, with 470 uF to AGND pin 43 | An additional local low-pass exists before the integrated analog-output circuitry |
| Buffer IC13 | NJM4558DV; pin 8 on +5A with 470 uF local decoupling, pin 4 grounded | Small-signal gain/filter response does not identify low-voltage clipping or crossover behavior |
| Stereo mixer IC12 | NJM4558DV; pin 8 fed from +5A through 3.3 uH with 470 uF local decoupling; pin 4 grounded | Mixer supply dynamics differ from the OPU's RC-filtered supply |
| Mixer bias | 2.2 kohm/2.2 kohm divider from +5A, bypassed by 100 uF, labeled +2.5 | Bias motion and clipping symmetry require an actual operating point, not a generic centered tanh |
| Power amplifier IC15 | AN7148, pin 10 on upstream +9; stereo 10 kohm volume pots precede its input networks | Power-amplifier headroom can respond differently from regulated FM/preamp stages |
| Output endpoint | Power-amplifier outputs drive the speaker/headphone network | A speaker/headphone amplifier model is not automatically a model of the PSS-780 AUX jack |

The board notes identify Tr1 as 2SC3419. The `+5` labels are nominal rail names, not a precision-voltage guarantee. This pass does not estimate the real emitter voltage from one generic base-emitter drop or assign a dropout value.

As a narrowly stated derivation, an ideal unloaded 47 ohm/470 uF low-pass has time constant 22.09 ms and corner about 7.205 Hz. Its response to supply movement is not the response to audio at TB. The actual AVDD load, capacitor ESR and regulator transfer are omitted, so this calculation neither calibrates audible ripple nor establishes how much adapter movement reaches the chip. The IC12 choke network is a different topology; it must not be replaced by that same pole.

The exact PSS-780 electrical-parts page confirms AN7148, NJM4558DV/NK alternatives, 2SC3419/2SC2603 transistors, 5.6/6.2 V zeners and a 1000 uF capacitor on its AM assembly. A parts list cannot assign those devices to the sibling's nodes. No exact-model supply connections or AUX tap were recovered by this pass.

## Datasheet facts and their operating conditions

The publicly downloaded [Panasonic AN7148 datasheet](https://datasheet.octopart.com/AN7148-Panasonic-datasheet-180974205.pdf), PDF pages 1-3, specifies a 6-18 V operating range. At 9 V, 4 ohm load, 3 mV input and 1 kHz, it gives THD typical 0.20%, maximum 0.75%. Its typical 2.10 W figure uses **10% THD**, a materially different condition. The graphs show input-level and supply dependence and an application circuit with feedback, ripple filtering, bootstrap and output capacitors. These support a nonlinear power-amplifier investigation; they do not select one odd-harmonic polynomial, a rail-sag time constant or a target AUX distortion amount. A headphone load also differs from the 4 ohm test load.

The official [NJM4558 product page](https://www.nisshinbo-microdevices.co.jp/en/products/operational-amplifier/spec/?product=njm4558) and [public datasheet](https://www.nisshinbo-microdevices.co.jp/en/pdf/datasheet/NJM4558_E.pdf), version 20260723, specify total supply 8-36 V. The main electrical table is characterized at +/-15 V; its familiar 1 V/us slew and 3 MHz bandwidth figures are not verified behavior at the sibling's nominal +5A rail. The exact historical DV/NK variants are not individually characterized by this modern family sheet. Thus a generic 30 V macromodel must not be presented as validated low-voltage clipping behavior. This is a characterization gap, not a claim that a working keyboard is defective. The manufacturer's SPICE download requires an account; no account or access workaround was used.

The manufacturer's [MN3206 datasheet](https://github.com/fmillion/yamaha-pss270/blob/8943bf963f196f20b4e2fc714f15400db578891b/datasheets/MN3206.pdf) already retained by the project gives a bias-adjusted distortion test, not an invariant keyboard effect. The [previous BBD audit](hardware-pass-20261018.md) records 0.3% typical/2.5% maximum THD at 5 V, 40 kHz CP, 1 kHz and 0.25 Vrms input. Its measured-condition dependence should be retained when proposing a physical wet path. No hiss source is needed to investigate this signal-dependent distortion.

## What the present engine does and does not reproduce

The current PSS-480-derived `AnalogOutput` is a **linear** small-signal network. Its state and frequency response add filtering, loading and phase, but cannot produce amplitude-dependent harmonics. The existing Drive is a creative tanh crossfade; Output Limit is a separate bounded safety transfer. Neither is a recovered YM3420, NJM4558 or AN7148 nonlinear characteristic. The Original pitch mode recovers software pitch commands plus an explicit downstream frequency hypothesis; it is not a DAC-resolution model.

No source in this pass identifies a YM3420 conversion bit depth, companding curve, native update clock, code-dependent glitch or static transfer. No target resistor/capacitor tolerance distribution, voltage coefficient, aged ESR or oscillator supply sensitivity was recovered. Manufacturing tolerance can change a fixed unit's filter response; it does not, by itself, justify random modulation or added harmonics. Unknown values should remain unknown rather than acquiring generic vintage percentages.

The practical next discriminator is the exact manual's overload condition: fixed factory/simple patches, several pitches and chord sizes, documented front-panel levels, and harmonic/intermodulation changes across level. Distinguish speaker/headphone from AUX, keep master-volume position and capture gain fixed, and preserve any capture clipping ambiguity. Root's separate investigation can use already retained recordings where the visible settings qualify. No new numeric audio fixture qualified in this source pass, so no harmonic, compression, sag or release parameter was fitted here.

A future supply model should preserve the observed rail partition and regulator/local filters, use a documented source/load hypothesis, and remain silent at zero input without an excitation source. Applying arbitrary random voltage changes to every clock and audio stage would not implement this circuit. The absence of measured supply movement also means that default random sag is not supported. Any interim nonlinear or sag audition should be labeled as a scenario, with its electrical scaling and assumptions visible.

## Preserved release-search outcome

Before the user's lo-fi steering, the existing Reverb/Sustain, recording-holdout, Soden and independent-envelope reports were inventoried. No repeated full video was downloaded and no audio was measured. Three separating observations were retained:

- [Stereo Ninja's original PSS-580 review](https://stereoninjamusic.weebly.com/yamaha-pss-580-review.html), originally 2016 and updated 2023, describes Reverb as extending the carrier's sustain. This is another firsthand qualitative sibling observation, not a measured threshold, RR/SRR substitution or verified OPU algorithm.
- [Alfonse's own PSS-680/780 page](https://www.alfonsemusic.com/yamaha-pss-680-780/) discloses that even the 'honest mix' includes external reverb. It is not a dry release/DAC fixture. Its composed examples were not downloaded for calibration.
- The already retained [Soden/ako video](https://www.youtube.com/watch?v=eiIw-ffhzXM), source approximately 836-845 s, visibly demonstrates Sustain and Reverb on an edited bank b.1. Previously retained frames/captions establish the opportunity, but not its raw patch, isolated gate pair or fixed capture transfer. The [earlier source audit](soden-pss680-source-audit-20261019.md) remains the full provenance. No release law was inferred or window moved to rescue it.

The public searches also encountered generic manuals, modified keyboards, processed compositions and repeated existing sources. None supplies a calibrated healthy-unit power-starvation capture. That is a bounded search result, not proof that no such source exists. No outreach, purchases, logins, cookies, hardware operation or access bypass occurred.
