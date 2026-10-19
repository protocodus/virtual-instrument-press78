# Feedback fuzz, Drive and output overload — 19 October 2026

A new native experiment separates three audibly different mechanisms already
present in Press78: per-voice FM feedback, shared postmix Drive, and final output
limiting. **None of these measurements recovers the original DAC or analog
overload.** They provide a reproducible discriminator for that missing behavior
and prevent the existing Drive control from being counted as hardware evidence.
No production DSP, default, preset, package or noise behavior changed.

The [full results](drive-output-separation-2026-10-19.json) retain all72
predeclared cases and source hashes. The
[native probe](../../Tools/prototypes/drive-output-separation-20261019/README.md)
uses the shipping engine's public API, rather than reimplementing its saturation
formula offline. It writes no audio files.

## The manufacturer's two distortion descriptions are different

Yamaha's [exact PSS-780 manual](https://usa.yamaha.com/files/download/other_assets/1/317511/PSS780E.PDF),
printed p11, warns that some chords can distort at maximum MELODY VOLUME when
displayed TOTAL LEVEL is90 or more. Printed p29 describes some voices
distorting above90, especially with MELODY VOLUME9. Both recommend reducing
level. The slightly different wording is a conditional operating warning, not
a measured hard threshold at90/91. The original retained page rasters were
visually checked for this pass.

Printed p28 separately describes feedback setting6 as producing a fuzz-like
sound through operator1 self-modulation. This is a synthesis parameter, not
evidence that the DAC is clipping. The manual gives no output-stage location,
transfer curve, supply law, electrical level or converter resolution for the
overload warning. Displayed TOTAL LEVEL is loudness, whereas raw operator TL
is attenuation; they must not be equated numerically.

A tempting additional recording lead is explicitly unsuitable as a healthy
calibration: [Joel Bisson's PSS-480/680 pack](https://www.audiobombs.com/items/671/yamaha-pss-480-680-sample-pack-%28sfz%29)
states that the recorded unit has a defect producing static-like distortion
in its audio path. That is useful provenance from its author, not evidence of
normal YM3420 behavior. No media from it was acquired or used.

## Frozen native experiment

The protocol was written before execution. It renders independent sine patches
at MIDI45/51 (110 and155.56349Hz): each note alone and both together, raw
carrier TL0/24, and plugin MasterGain0.25/2. All gates begin at sample0 and
remain held. Each case lasts0.6seconds; analysis uses0.2–0.6seconds without
latency adjustment. Clock variation, tone, DC block and chorus are disabled.
The unchanged48kHz synthesis and32-tick latency remain in place.

Six cases select the mechanism: linear bypass; linear sibling AnalogOutput;
Drive1; output limiter; ordinary FM with feedback0; and the same FM with
feedback6. Both FM cases use modulator raw TL24, fixed carrier level and the
same ratios/envelopes. No factory bytes or alleged physical thresholds enter
the experiment. All72 executions, including43.2seconds of native output,
completed in about1.6seconds. Raw float32 crosses a subprocess pipe in memory;
only hashes and measurements are retained.

For each mechanism and level, the primary separator is the chord waveform
minus the sum of its separately rendered notes. This removes independent
per-voice synthesis, including intentional FM harmonics. A common fixed
Hann-weighted harmonic/intermodulation basis has condition number1.4164.
Six named cross-note frequency witnesses are45.5635,265.5635,64.4365,
201.1270,375.5635 and421.1270Hz. They describe energy in the additivity
residual; they are not a complete THD/IMD specification.

## Measured separation

At raw carrier TL0:

| Mechanism | MasterGain | Additivity residual / chord RMS | Six IMD witnesses / chord RMS |
|---|---:|---:|---:|
| Linear bypass |0.25|3.46×10⁻⁸|1.11×10⁻⁹|
| Linear sibling circuit |0.25|3.54×10⁻⁸|1.16×10⁻⁹|
| FM, feedback6 |0.25|3.72×10⁻⁸|1.03×10⁻⁹|
| Shared Drive1 |0.25|0.94756|0.39185|
| Output limiter |0.25|3.46×10⁻⁸|1.11×10⁻⁹|
| Output limiter |2.0|0.66752|0.32802|

The dimensionless residual is **not a distortion percentage**: it includes
the difference between compressing the combined signal and compressing each
note separately. Across both raw carrier levels and master settings, linear,
circuit and independent FM cases preserve superposition within3.75×10⁻⁸
relative RMS. Feedback changes an individual voice's spectrum substantially
while preserving that cross-voice property. For the110Hz tone at TL0,
feedback0→6 changes H2/H1 from−2.263 to−31.750dB and H3/H1 from−7.635
to−18.905dB for this particular synthetic patch. Those are intentional
synthesis changes, not recovered hardware distortion measurements.

Carrier level excites Drive differently: at **TL0, the higher-amplitude
condition**, the110Hz tone has H3/H1−9.717dB; at **TL24, the quieter
condition**, it has−17.565dB. After removing the engine's current nominal
carrier attenuation, its chord waveform differs by5.3606 relative RMS between
these levels. Independent FM and the linear circuit preserve the normalized
waveform within floating-point error. This verifies amplitude dependence in
the existing shared creative effect; it does not identify a Yamaha transfer.

Increasing plugin MasterGain from0.25 to2 gives exactly8×RMS and an exactly
identical gain-normalized waveform in **every nonlimiter case**, including
Drive. That places this master gain after Drive. The limiter's TL0 chord
instead grows4.0905×RMS and changes its gain-normalized waveform by0.55225
relative RMS. At MasterGain0.25 the limiter is bit-identical to bypass for all
six note/level cases. This confirms the distinction between a creative effect
before master gain and protection after it.

The experiment does **not** establish where the real instrument's MELODY
VOLUME or physical VOLUME acts. Plugin MasterGain is an output parameter with
its own defined placement; it is not a verified hardware control mapping.
Consequently its measured placement alone proves neither that the hardware
model is wrong nor that hardware overload has been replicated.

## A physical-capture discriminator

The separating sequence is two pure-carrier notes independently and together,
with exact patch bytes, fixed gate/velocity and capture gain, comfortably below
twelve voices. Keep feedback/modulation absent, and independently disable
Reverb/Sustain/Chorus/Vibrato. Vary displayed TOTAL LEVEL and MELODY VOLUME
separately; repeat at a second physical VOLUME setting and identify AUX versus
headphone/speaker routing. Preserve the captured levels before any listening
normalization.

For real recordings, unknown phase resets mean one cannot blindly subtract
independent single-note takes sample for sample as in this controlled native
fixture. Instead, seek cross-note frequencies absent from both isolated
spectra and examine their level dependence. Intentional independent FM can
have rich harmonics without those cross-note products; shared overload can
generate them. Recording-interface distortion can do the same, so this result
alone still does not locate the nonlinear element inside the keyboard.

The next implementation candidate should be justified against such a transfer
or an identified nonlinear circuit. A tanh curve, a final safety limiter,
random supply fluctuation or a defective-unit sample cannot fill the missing
DAC/output law. The existing linear
[sibling circuit and supply constraints](lofi-signal-path-audit-2026-10-19.md)
remain valid and separate.

All predeclared contracts passed. No gate, window, level, frequency or case was
changed after execution; no failed native contract was suppressed. This is
software mechanism validation and a more discriminating research fixture,
not target-hardware fidelity certification.
