# Press78

Press78 is an editable two-operator FM synthesizer derived from the PSS-780 research experiment, as a VST3, CLAP and Standalone plug-in on macOS, Windows and Linux, plus an Audio Unit on macOS. Its independent C++17 engine also drives an eight-unit Reason Rack Extension prototype. It uses original Press78 branding and focuses on synthesis; it does not reproduce the keyboard, rhythms or accompaniment system. It is a behavioral model, not a bit-exact YM3420 emulator, and commercial redistribution of the imported factory bank has not been cleared.

![Press78 editor](Docs/screenshots/press78.png)

## Audio demos

Eight of the 100 factory voices, one from each of eight families, rendered by the main build from the phrases in `Docs/audio/midi` through the plug-in's default controls (the Real startup profile, Volume 0.25). Levels are the bank's own; nothing is normalised.

<!-- audio-demos-begin -->

| # | Preset | Demo | Length | Peak |
| --- | --- | --- | --- | --- |
| 3 | PSS 02 Electric Piano 1 | [003-pss-02-electric-piano-1.wav](Docs/audio/003-pss-02-electric-piano-1.wav) | 11.7 s | -12.1 dBFS |
| 14 | PSS 13 Jazz Organ | [014-pss-13-jazz-organ.wav](Docs/audio/014-pss-13-jazz-organ.wav) | 11.1 s | -14.3 dBFS |
| 23 | PSS 22 Trumpet | [023-pss-22-trumpet.wav](Docs/audio/023-pss-22-trumpet.wav) | 11.8 s | -23.3 dBFS |
| 33 | PSS 32 Alto Sax | [033-pss-32-alto-sax.wav](Docs/audio/033-pss-32-alto-sax.wav) | 11.9 s | -19.8 dBFS |
| 54 | PSS 53 Rock Guitar 1 | [054-pss-53-rock-guitar-1.wav](Docs/audio/054-pss-53-rock-guitar-1.wav) | 11.8 s | -25.2 dBFS |
| 63 | PSS 62 Slap Bass | [063-pss-62-slap-bass.wav](Docs/audio/063-pss-62-slap-bass.wav) | 11.9 s | -22.4 dBFS |
| 85 | PSS 84 Tubular Bells | [085-pss-84-tubular-bells.wav](Docs/audio/085-pss-84-tubular-bells.wav) | 11.9 s | -25.1 dBFS |
| 93 | PSS 92 Human Chorus | [093-pss-92-human-chorus.wav](Docs/audio/093-pss-92-human-chorus.wav) | 11.6 s | -15.7 dBFS |

<!-- audio-demos-end -->

## Version history

### Unreleased — 0.1.13 — PSS-780 firmware laws, chip rate, analog chorus and amplifier

- 0.1.13: **Power** becomes a slider. 100 % is six fresh alkaline C cells, as 0.1.12's **Batteries**; each step down moves the same cells nearer the end of their life, and the top step, **AC**, is the adaptor. Worn cells sag further under the speakers' current, so **AUX** clips sooner and pumps; near the end the sagging rail also pulls the keyboard's +5 V down, which narrows the mixer's headroom before the volume slider. At the default Volume a four-note PSS 46 Jug chord at full velocity changes by −50.5 dB at 90 %, −28.5 dB at 50 % and −12.9 dB at 1 %, and PSS 00 Piano 1's by −56.5, −42.4 and −18.9 dB at 50, 26 and 1 %. The real keyboard would blink its LEDs near 26 % and reset on loud notes below about 19 %; Press78 plays on, so the lowest steps exaggerate. **Phones** change less and **Preamp** not at all. Fresh cells and **AC** sound exactly as 0.1.12's **Batteries** and **Adaptor**, and a 0.1.12 song on the adaptor opens at **AC**.
- 0.1.12: Adds a **Power** choice. New instances, Init, the 100 `PSS` patches and the modern presets run the amplifier from fresh **Batteries**, so **AUX** and **Phones** clip as the AN7148 does when **Volume** is pushed. A four-note chord at full velocity changes by less than −50 dB at the default Volume on every `PSS` voice; at twice the default, 38 of the 100 chords change by more than −40 dB, and at Volume 1 half of them by more than −20 dB. Loud speaker bass sags the battery rail, so positive peaks flatten first. **Adaptor** idles with more headroom but sags further under load. **Ideal** keeps the earlier linear amplifier, and older songs that lack the setting use it. **Preamp** is unchanged.
- 0.1.11: **AUX** hears the loudspeaker's own impedance on the amplifier's output, with a similar 12 cm driver standing in for the PSS-780's undocumented one. Bass between 60 and 120 Hz is up to 1.8 dB fuller than with the plain 4 Ω load used before, 20 to 30 Hz up to 0.9 dB weaker, and 150 Hz about 0.7 dB weaker; above 500 Hz the change is under 0.1 dB. **Phones** and **Preamp** are unchanged.
- 0.1.10: **AUX** and **Phones** load the volume slider with the amplifier's input, as the PSS-480 does. Near full **Volume** the deepest bass is lower: 3 dB lower at 20 Hz and 1 dB lower at 50 Hz at the top, under 0.1 dB at the default setting. **Preamp** is unchanged.
- 0.1.9: New instances, Init, the 100 `PSS` patches and the modern presets run the FM chip at the YM3420's own sample rate, 57,291.67 Hz, instead of 48 kHz. Bright high notes fold their top partials back to the hardware's inharmonic pitches: C7's sit at 785.0 and 1307.8 Hz, within 0.2 Hz of PSS-680 recordings, where 48 kHz put them at 135 and 1958 Hz. Across the `PSS` voices at C6, G6 and C7, 26 of 300 notes carry such lines above −60 dB, Bagpipe's C7 the strongest at −39 dB. Lower notes, timing and latency are unchanged; twelve FM voices take about a quarter more CPU at 48 kHz. Older songs that lack the setting keep 48 kHz.
- 0.1.8: Adds an **Output jack** choice. New instances, Init, the 100 `PSS` patches and the modern presets play from **AUX**, through the power amplifier as the PSS-480 builds it: bass is 1 dB lower at 80 Hz and 4 dB lower at 33 Hz, and treble 1 dB lower at 10 kHz and 2 dB lower at 15 to 20 kHz. **Phones** passes the headphone jack's network instead, with a 32 Ω headphone, which takes about 2 dB off the centre of a 65 Hz bass note and lets low bass leak between the earpieces. **Preamp** keeps the earlier output, and older songs that lack the setting use it.
- 0.1.7: New instances, Init, the 100 `PSS` patches and the modern presets pass the Recorded chorus's delayed signal through the bucket-brigade chorus's analog filters, with values borrowed from the PSS-270 schematic. The chorus shimmer loses its fizz: the stereo difference signal is about 12 dB lower from 5 to 8 kHz and about 2 dB higher from 1.5 to 3 kHz, and each channel changes by 1 to 2 dB in those bands. Studio chorus and patches without chorus are unchanged. Older songs that lack the setting keep the unfiltered delay.
- 0.1.6: New instances, Init, the 100 `PSS` patches and the modern presets allocate voices as the PSS-780 does in its normal keyboard mode. Replaying a note cuts that note's own release instead of stacking a second copy on it, so fast repeats on long-release sounds no longer build up or phase; a held key sent again is ignored; and a new note takes a released voice before stealing a held one. Older songs that lack the setting keep the previous free-voice-then-oldest policy.
- 0.1.5: New instances, Init, the 100 `PSS` patches and the modern presets scale each operator's level across the keyboard with the PSS-780 program's own per-key tables. Most patches change by under 1 dB; Human Chorus, Human Voice 1, Strings and Soprano Sax are up to 4.3 dB different at the ends of the keyboard, and modulator changes of up to 5.8 dB alter brightness from low to high notes. Older songs that lack the setting keep the earlier curves.
- 0.1.4: New instances, Init, the 100 `PSS` patches and the modern presets follow the PSS-780's own MIDI velocity curve: soft notes are louder than before (velocity 16 sits 15.75 dB below full instead of 18 dB, velocity 1 at 23.25 dB instead of 42 dB), and velocities from 32 up change by under 1 dB. Older songs that lack the setting keep the linear curve.
- 0.1.3: Adds the PSS-780's **Portamento** effect with its five speeds (1 slow … 5 fast, default 3), switchable from the panel or MIDI CC65. Each new note glides from the previous note in a fixed time per speed, whatever the interval, as the keyboard's own program does. The glide's absolute timing is an estimate.
- 0.1.2: New instances, Init and the 100 `PSS` patches start with a ±1 semitone pitch wheel, the PSS-780's own reset value (owner's manual, printed pp. 10 and 39). Older songs that lack the setting keep ±2, and the modern presets keep their own ranges.
- 0.1.1: Applies the selected B listening options: a longer envelope-Reverb tail and shared asymmetric output headroom, enabled by default. No artificial noise is added. Existing patches acquire the selected character when their models are enabled. The values are chosen assumptions, not recovered PSS-780 calibration. See the [decision](Docs/decisions.md) and [adoption note](Docs/release/assumed-hardware-adoption-2026-10-19.md).

### 0.1.0 — 2026-10-18 to 2026-10-19 — engine, Rack prototype and plug-in front end

- Two-operator FM engine with the 100 `PSS` factory voices and an Init sine, sibling-circuit output stage, Studio and Recorded chorus, and clock variation.
- b11: the D1 endpoint correction and a 5.24 Hz triangle LFO with recording-supported vibrato depths; additive noise removed (its two controls stay as inert, hidden ids).
- b12: a **Pitch model** selector, Original (the firmware pitch-command table, the new default) or Equal (the earlier continuous law).
- b13: the Original release-pedal policy (the pedal selects the release rate; key-up releases at once), a hidden setting that new patches turn on.
- b14: a fixed output bus and final converter keep the 48 kHz output character at every host rate; other rates change audio and latency.
- b15: 50 modern Rack presets (basses, donks, plucks, leads, pads and FX) beside the 100 `PSS` voices; the plug-in does not include them yet.
- b16: new Reason devices open **BASS - Vowel Engine**, a velocity-responsive low-register growl. Init remains available in the patch browser; saved sounds and the JUCE plug-in's startup are unchanged.
- Reason Rack Extension prototype 0.1.0b16, built outside this repository.
- First JUCE plug-in: every control as a parameter, Init plus the 100 voices as programs, and a working editor; the Rack panel design is not yet ported to it.

## Downloads

<!-- build-download-begin -->
**[Download main build 33](https://github.com/protocodus/virtual-instrument-press78/actions/runs/40661256228/artifacts/12804533167)**, built from [`689a419971c4`](https://github.com/protocodus/virtual-instrument-press78/commit/689a419971c46cda13a9c211dd5356c912d9cc4b). It holds the macOS, Windows and Linux packages, `SHA256SUMS` and `BUILD.txt`.
<!-- build-download-end -->

---

## How it works

### Engine

Both operators expose ratio, fine/coarse detune, four waveform families, raw envelope rates, key scaling and AM. Additional controls cover feedback, velocity, LFO phase/depth/delay, twelve-voice allocation, pitch bend, mod wheel, clock variation, analog output, tone, drive, chorus and stereo width. The Rack adapter adds separate MIDI/CV note ownership and Note/Gate/FM/Level CV inputs. All 68 visible controls have explicit Reason automation mappings. The two former noise properties and their IDs remain reserved for compatibility; they are hidden and inert. The registry stays frozen in `Assets/rack-automation.json`; Volume/Tone retain MIDI CC7/74.

The initial port preserved the frozen Python raw-FM behavior. Starting with b11, a documented D1 endpoint correction and recording-supported modulation replace those corresponding hypotheses; the Python files remain frozen historical references. It adds fixed-storage voice management, short voice-stealing tails, continuous-control smoothing and host-rate conversion. The floating-point operators, envelope laws and detune mappings are modeling choices, not recovered chip internals; so is the legacy 48 kHz timebase, which the YM3420 rate below replaces. The core has 0.67 ms (32 legacy samples) of nominal reconstruction latency at either rate. The b14 instrument adds a final host converter outside 48k; its declared Rack latency is 126/32/236/256/512 frames at 44.1/48/88.2/96/192k. Clock controls also scale that physical delay; upward clock shifts can alias near-Nyquist energy. Clock drift is a controllable scenario, not a measurement of aged hardware. Memory faults and random digital bit corruption are not introduced as normal vintage behavior.

The b12 rear **Pitch model** selector offers **Original** and **Equal**. New Init/PSS patches explicitly select Original; older patches missing the new property retain Equal. Original uses the independently reconstructed 384-word firmware pitch-command table, including its nonmonotonic A-flat fractional entry and high-seven-bit MIDI bend behavior. Device Tune rounds to 3.125-cent steps; host master tuning and internal vibrato stay continuous. The downstream command-to-frequency floor/grid remains a recording-supported behavioral hypothesis, not identified silicon arithmetic. Extended keyboard/tuning ranges are plugin extensions. The selector displays the requested model; changes wait until held notes, releases and steal fades finish, or reset/all-sound-off. [Firmware evidence](Docs/research/opu-pitch-command-path-2026-10-19.md), [physical panel mapping](Docs/research/front-panel-envelope-map-2026-10-19.md) and [frozen comparison](Docs/research/hardware-pitch-b12-2026-10-19.md) separate verified commands from inferred synthesis behavior.

The b11 modulation profile uses a continuous 5.24 Hz triangle and a binary PMS depth hypothesis: 0,3.125,6.25,12.5,25,50,100,200 cents. The original PSS-780 recording directly supports roughly 12.5 cents at PMS3 and 100 cents at PMS6; unobserved levels remain a modeled interpolation. New PSS-580 recordings independently corroborate the approximately 5.24–5.25Hz triangle motion, with raw patch-depth and global-phase qualifications. The existing 10 ms/VDT delay law remains uncertain. D1 now tests whether its endpoint is already reached before applying a decay increment, eliminating unwanted attenuation from a zero-height stage. See the [FM audit](Docs/research/fm-fidelity-audit-2026-10-18.md), [pitch audit](Docs/research/lfo-pitch-audit-2026-10-18.md) and [independent recordings](Docs/research/recording-holdout-audit-2026-10-18.md).

### Chip sample rate

The YM3420 runs at the PSS-780's 5.5 MHz OPU clock divided by 96, 57,291.67 Hz (`Press78Engine::kYm3420Rate`). The divider is measured, not documented: in PSS-680 recordings (the same chip) 205 alias lines across 63 notes fit 96 × fs = 5.4992 MHz, within 150 ppm of that clock, where dividers of 95 or 97 would need a 1 % clock error. At that rate the firmware's pitch words are the chip's 20-bit phase step per sample. The FM operators are not band-limited, on the chip or here, so partials above 28.6 kHz fold back to inharmonic lines; C7's f0 is almost exactly 8/219 of the rate, which puts them on the odd multiples of f0/8 that recordings of C7 show. A 48 kHz core folds them elsewhere. Pitch, envelopes, LFOs, smoothing, portamento and steal fades are laws in seconds, so notes whose partials stay below the fold sound as before; the host converter's delay is held at 32/48000 s so latency does not change. **Chip sample rate** is a hidden compatibility setting: YM3420 for new instances and the factory patches, Legacy (48 kHz) for older songs. A change waits until voices are idle, like the other firmware laws.

### Output circuit

The enabled-by-default output circuit combines the selected shared asymmetric headroom curve with the six-section small-signal transfer from the researched **PSS-480** circuit. The curve's normalized headroom of 1 and bias of 0.14 were selected through the B audition; the filter is a sibling surrogate. Neither is a recovered PSS-780 board, verified YM3420 DAC transfer or transistor-level model. The existing output-circuit switch bypasses both together. Drive remains a separate creative saturation control.

Authentic DAC behavior, component tolerances and power sensitivity remain fidelity requirements despite removal of artificial noise. The selected output curve supplies deterministic signal-dependent color; its constants do not establish physical operating levels. A [research supply component](Docs/research/local-supply-model-2026-10-19.md) implements the documented sibling local rail filter with independent circuit checks. Its load and voltage-to-audio coupling remain unknown and are not connected to the audio engine.

B14 preserves the established 48k output character across host rates through a fixed output bus and a final stereo converter. It intentionally changes non-48k audio and latency in existing documents; all 48k renders remain unchanged. [Adoption and A/B evidence](Docs/research/output-bus-b14-2026-10-19.md) separates improved host-rate consistency from still-unidentified DAC, BBD nonlinear and voltage-to-audio behavior.

### Amplifier and output jacks

**Output jack** chooses which socket is heard (`Source/DSP/AmplifierCircuit.h`). **Preamp** is the signal at the top of the volume slider, where the output circuit above ends. **AUX** and **Phones** add the power amplifier after the slider. The PSS-780 lists the same AN7148 amplifier, 1000 µF/16 V output capacitors, 4 Ω speakers and 3.3 µH headphone coils as the PSS-480, so the values come from the PSS-480 drawing (KEC-11861) and the AN7148 datasheet and are borrowed. The slider's wiper drives 10 kΩ into 1 kΩ ‖ 4700 pF, a pole at 37.25 kHz. The datasheet's gain curve, −1 dB at 15 kHz, is read as one pole at 29.48 kHz; both poles together lose 0.8 dB at 10 kHz and 1.7 dB at 15 kHz. They sit near or above the engine's 24 kHz Nyquist frequency, so one first-order section matches their combined level at DC, 15 kHz and Nyquist, within 0.4 dB from 1 to 20 kHz.

AUX OUT is taken from the speaker node, after the output capacitor, as the PSS-270 and PSS-560 take it; the PSS-780's own AUX network is not documented. Into the datasheet's resistive 4 Ω, 1000 µF is a 39.8 Hz high-pass, which accounts for the low end of the datasheet's curve (−1 dB at 80 Hz, −3.7 dB at 33 Hz). The instrument's node instead holds the loudspeaker, which the jack leaves connected (owner's manual, p. 8). The PSS-780's XG516A00 (12 cm, 4 Ω, 3 W) has no published data, so the Visaton FR 12 – 4 Ω, a 12 cm weak-motor driver sold for electronic instruments, stands in: Re 3.4 Ω, fs 110 Hz, Qms 5.61, Qes 2.8, in free air because the case's shared cavity is not documented. Of four similar drivers, its curve is nearest their median. Below resonance the driver looks inductive and lifts 60 to 120 Hz by up to 1.8 dB against a plain 4 Ω; its 3.4 Ω coil makes 20 to 30 Hz up to 0.9 dB weaker; the −3 dB corner stays at 39.4 Hz. Across the similar drivers the 50 to 200 Hz ripple varies by about ±1.5 dB, as much as a ±20 % tolerance on the capacitor would. **Phones** follows the PSS-480 headphone jack: 100 Ω in series, and a sleeve that returns to ground through one 47 µF shared by both earpieces, with the speakers cut (PSS-780 owner's manual, p. 8). With a 32 Ω headphone, an assumed load, the shared capacitor puts a 52.5 Hz high-pass on the centre (mid) signal only, so bass on one side leaks into the other: −6.7 dB at 50 Hz. Higher-impedance headphones lower that corner (about 17 Hz at 300 Ω). The wiper's 10 kΩ and 1 kΩ also load the slider: the 1 µF that couples the pot top sees less than the pot's own 10 kΩ as the wiper rises, so the 15.9 Hz corner of the output circuit, which leaves the wiper unloaded, moves to 30.4 Hz at the top (the AN7148's own input resistance is not given). Each path is set to unity gain in its passband, so **Volume** still sets the level. **Volume** is twice the wiper's loaded share of the pot-top voltage: its top, 2, is the slider's top, a convention that makes the slider's undocumented taper irrelevant.

**Power** chooses what feeds the keyboard, and with it how **AUX** and **Phones** clip: six alkaline C cells from fresh (100 %) to spent (1 %), or the adaptor (**AC**). The hidden **Power circuit** setting keeps older songs on **Ideal**, the earlier linear amplifier. The AN7148's output follows y = v (1 + |v/Vc|¹⁰)^(−1/10), fitted to the datasheet's distortion curve at 9 V into 4 Ω: Vc is 3.66 V, the fit stays within 2.7 dB of the curve from 0.4 to 22 % distortion, and it gives 2.08 W at 10 %, where the datasheet's table gives 2.10 W. Vc rises 0.376 V per supply volt; into headphones it is taken as half the supply less 0.51 V. To place that in the instrument, one engine unit at the top of the volume slider is taken as 1.0 V peak: the NJM4558 mixer that drives the slider, as the PSS-480's does, swings 0.72 to 1.72 V, and the owner's manual (pp. 11 and 29) says chords of loud voices occasionally overload it, which puts one unit between 0.5 and 2.3 V. The AN7148 gains 44.5 dB over the wiper's 1/11. Fresh cells are 9.54 V behind 1.35 Ω (Energizer EN93 and E93 data). **AC** is an unregulated PA-3 class adaptor, 16.5 V open-circuit as one owner measured a "12 V" PA-3C, falling to 12 V at its rated 0.7 A, behind the PSS-480's series 1SR35 diode. Either charges the rail's 470 µF (PSS-480), which an estimated 0.2 A idle current and each channel's positive output current draw down. The output's midpoint is held by a capacitor, so a fast dip of the rail lowers only the positive limit. On batteries the rail idles at 9.27 V, where Vc is 3.76 V; a loud stereo speaker signal pulls it towards 8 V and flattens its positive peaks first. The adaptor idles at 14.4 V (Vc 5.68 V) but sags further under load; its own reservoir capacitor is unknown, so that sag is an upper bound. At the default **Volume** of 0.25 the amplifier stays clean on fresh cells.

Below 100 % the cells age along their published discharge curves at the keyboard's 0.45 A: the voltage on load follows Energizer's E93 and Duracell's MN1400 curves, which agree within 0.03 V, and each cell's resistance rises from 0.225 Ω to about 1.1 Ω as Varta's pulse data for AA cells does. The slider is linear in that loaded voltage, from 8.93 V at 100 % to 4.80 V at 1 %, the 0.80 V per cell where every curve ends, so each step changes the sound by a similar amount rather than spending the same charge. The idle rail falls from 9.27 V to 7.39 V at 50 % and 6.45 V at 1 %, where Vc is 2.70 V, and the resistance behind it grows almost fivefold, so loud notes sag it much further. The keyboard's +5 V comes from a zener-held 2SC3419 follower fed through 150 Ω, 100 µF and 150 Ω (PSS-480 drawing; the PSS-780 lists the same parts). It holds until the rail falls to about 6.2 V, estimated from a 0.15 A load and a transistor gain of 110 (5.8 to 7.5 V across their ranges), and then follows the rail down through the 100 µF. The NJM4558 mixer's limits track its supply one to one, around a bias of half the +5 V held for 110 ms, so a sudden sag narrows its headroom above the bias and a lasting one narrows both sides by half as much, one engine unit per volt. A low-battery detector would blink the LEDs once +5 V reaches 4.70 V and another would reset the keyboard at 4.39 V; neither is modelled, so the lowest steps keep playing where the hardware would stop.


### Portamento

The glide follows the PSS-780 program (`xg503b0-132`, read 2026-10-20; nothing from it is included). A note-on glides from the most recent note-on, held or released, when Portamento is on; the first note after reset does not glide. Its slot starts at the previous pitch and moves linearly in 1/256-semitone steps of `interval × 2^speed` per pass of the program's main loop, heard as 1/32-semitone pitch commands, until it reaches the new note. Every glide therefore takes `2^(8 − speed)` passes: 128, 64, 32, 16 and 8 for speeds 1–5. Chords glide note by note from the note played just before. The main loop is not paced by a timer and was not measured; Press78 assumes 2.5 ms per pass, giving 320/160/80/40/20 ms. CC65 values of 64 and above switch it on and lower values off, overriding the panel control until Reset All Controllers.

### Velocity

With the Original velocity curve, a note's carrier level follows the table the PSS-780 program (`xg503b0-132`, bank 2 `$7890`) applies in its MIDI sound-source mode (Mode 99): a carrier attenuation of 31 TL codes below velocity 3, falling by one code at each of velocities 3, 4, 5, 6, 7, 9, 10, 12, 13, 15, 17, 19, 22, 24, 27, 30, 34, 37, 41, 46, 51, 56, 62, 68, 74, 80, 87, 94, 102, 111 and 118, where it reaches zero. A TL code is taken as 0.75 dB, the engine's existing TL law. **Velocity to level** scales that attenuation in dB, so 1 is the hardware's curve and 0 is the keyboard mode (Mode 00), which ignores velocity. **Velocity to FM** is Press78's own and keeps its linear law. The firmware's saturation of TL plus addend at 127 is more than 95 dB down and is not modelled. The hidden **Original velocity curve** setting keeps the linear `(velocity/127)^sensitivity` law for older songs.

### Key scaling

With Original key scaling, each operator's level follows the per-key TL offsets the PSS-780 program adds before it sends a level to the sound chip. Its 16 lower and 16 upper tables, chosen by the patch's low and high key-level settings, give a signed offset per pair of keys: lower tables run from key 24 up to middle C, where every table is zero, and upper tables from middle C to key 102, holding their end values beyond. The sum saturates at 0 and 127, so a negative offset never lifts an operator above full level, and the result mutes the operator at 99 and above, as a raw TL of 99 does. The tables (`Source/DSP/FirmwareLevel.h`, from `Tools/generate_firmware_level.py`) are re-expressed from the program's results; no ROM bytes or code are included. A code is taken as 0.75 dB, the engine's existing TL law. The [b13 comparison](Docs/research/hardware-key-level-b13-2026-10-19.md) against an old recording failed its adoption gate on Bowed Bass by about 0.2 dB while improving the 100-patch average; the owner chose to ship the keyboard's own tables regardless. The hidden **Original key scaling** setting keeps the earlier fitted curves for older songs, and a change waits until held notes, releases and steal fades finish.

### Voice allocation

With Original voice allocation, notes follow the PSS-780 program's Mode 00 allocator (`Source/DSP/FirmwareAllocation.h`, re-expressed from the [recovered command path](Docs/research/opu-allocation-command-path-2026-10-19.md); no ROM bytes or code are included). A note-on for a key already held does nothing. A new key first reuses the slot that last played the same note, held or released, ending its old sound with the engine's short steal fade. Otherwise it takes the slot with the lowest saturating 8-bit rank: a held key is ranked 255 and a released one 127, and every key event ages the others by one, so released voices are always taken before held ones and the oldest within each class goes first. Reduced polyphony uses the first N slots. MIDI and CV are two separate key sources sharing the pool, a Press78 extension. When the chip's key-on resets oscillator phase and how fast the program services keys are not known; Press78 keys the slot immediately and keeps the oscillator and envelope laws it already had. The [recording comparison](Docs/research/hardware-allocation-2026-10-19.md) failed its adoption gate on a short sine passage while greatly improving Bowed Bass; the owner chose to ship the keyboard's own allocation. The hidden **Original voice allocation** setting keeps the earlier policy for older songs, and a change waits until every key is up and voices, releases and steal fades have finished.

### Sustain pedal

B13 adds the [Original release-pedal policy](Docs/research/sustain-policy-2026-10-19.md): the pedal selects RR/SRR while keyoff releases immediately, including live rate updates on released notes. New Init/PSS files select it; older documents retain conventional pedal holding. The hidden compatibility setting leaves the panel unchanged. All eight no-pedal full-performance WAVs match b12 exactly, so existing recording scores are unchanged. The authored Sustain button does not display the temporary pedal override, and the plugin does not emulate complete keyboard program-change behavior.

### Chorus

Two realtime chorus modes are available. **Studio** preserves the original creative delay effect. **Recorded** implements the frozen v3 effective stereo transfer from the PSS-780 recording: roughly 0.49–1.51 ms delay, a continuous 0.954647 Hz LFO, second-harmonic motion and direct mid leakage. It adds no whole-output latency. The rate and depth remain editable. This is a recording-derived approximation, not an identified MN3206 circuit. The offline v4 branch correction remains a reference because an exact causal port would need about 21.83 ms lookahead compensation at 48 kHz.

With the PSS-270 chorus circuit (`Source/DSP/ChorusCircuit.h`), Recorded mode's delayed signal also passes the BBD's analog wet path, with values read from the PSS-270 schematic (KEC-11463). The PSS-780 uses the same MN3206/MN3102 pair and carries the PSS-270's clock and inverter parts, but its own filter values are not documented, so these are borrowed. Before the delay, a 0.1 µF / 1.5 kΩ / 33 nF network into the 50 kΩ bias puts poles at 23.5 Hz and 4.35 kHz. After it, a 0.1 µF coupling into 50 kΩ feeds a unity-gain Sallen-Key low-pass (22 kΩ + 22 kΩ, 12 nF, 680 pF; 2.53 kHz, Q 2.1). Together they give −1.6 dB at 100 Hz, +4.1 dB at 2.39 kHz, −8.2 dB at 4 kHz and −19 dB at 6 kHz relative to 1 kHz. The right channel's inverted copy also passes the inverter's 47 kΩ / 220 pF pole at 15.4 kHz. Two conventions, not circuit values, keep the recorded fit intact: the filters are normalised to unity at 1 kHz, where the fit's wet gain was identified, and their 0.092 ms group delay at 1 kHz comes off the recorded delay. The pre-delay filter runs after the delay read; at the recorded depth the delay's motion shifts pitch by at most 0.4 %, so the order is inaudible. The hidden **Chorus wet-path circuit** setting keeps the unfiltered delay for older songs.

### Noise

The standalone PSS-480 resistor/opamp noise model and earlier noise research remain as historical reference tools. They are not connected to the instrument engine; no additive PRNG, circuit-noise generator or noise controls remain in the unit. The [b11 audit](Tests/results/noise-removal-b11-audit.json) preserves the initial verification; the [b12 noise-removal audit](Tests/results/noise-removal-b12-audit.json) verifies current source, source-bound normal/sanitized wrapper tests, absent GUI controls and all 101 packaged patches.

### Startup profile and factory bank

The Rack Init and all 100 factory patches use the **Real** startup profile: related-hardware output circuit on, Recorded chorus at its captured rate/depth and full reference side level, and a slow ±20 ppm clock excursion at 0.1 Hz (about ±0.035 cents). Clock offset and creative Drive stay zero. Clock excursion is an explicit modeling choice, not recovered PSS-780 calibration. Additive noise has been removed from the runtime, including both White and Circuit paths. Old patches and automation may still contain the former noise properties; their values are ignored and cannot restore hiss. Other values remain editable and persist with patches. The portable constructor also uses the new 5.24 Hz shared triangle LFO; its effect defaults remain independent of the Rack Real profile. Model selectors and fine calibration are on the rear.

New Reason devices open **BASS - Vowel Engine**, the existing modern preset selected by `Assets/FactoryBank/rack-startup.json`. Play MIDI notes 30–54 for its throaty, rhythmic growl; velocity adds bite and the wheel adds slow pitch wobble. Its sound parameters are unchanged. Init remains an independently defined sine patch in the standard patch browser. This Rack startup selection does not change saved patches, compatibility defaults or the JUCE plug-in's Init startup.

The public development bank contains the 100 original parameter presets as `PSS 00 …` through `PSS 99 …`. The Rack bank also carries 50 modern presets (12 basses, 8 donks, 12 plucks, 8 leads, 6 pads and 4 FX) under `Modern`, defined in `Assets/FactoryBank/modern-*.json`; the [factory presets guide](Docs/guide/factory-presets.md) lists them, and [the modern audition page](Docs/guide/modern-presets.html) plays each one. Loading/editing a Rack patch retimbres held voices while preserving their oscillator/envelope state. The standalone engine also offers future-voices-only program snapshots.

### Plug-in front end

The plug-in's parameter IDs are the control ids in `Assets/controls.json`, the same names as the Rack properties; `Source/PluginControls.h` is generated from that file by `Tools/generate_plugin_controls.py`. `Source/ControlMapping.h` maps the controls to the engine's patch and controls for both the plug-in and the demo renderer. Program 0 is Init and programs 1–100 are the factory voices; a program change sets the 36 sound controls and leaves performance and output controls, including Pitch model, alone, and editing a sound control retimbres held voices, as the Rack does. Pitch bend scales by Pitch bend range, which starts at ±1 semitone as on the PSS-780 after ALL RESET, and Original receives the raw 14-bit wheel as the firmware does; the mod wheel adds its position times Wheel to vibrato to Pitch depth (this mapping is the plug-in's own choice; the Rack adapter's is not in this repository). A new instance starts with Pitch model and the Original release policy on, as the Rack Init does, and CC64 reaches the engine as its raw value because Original treats any nonzero value as down. The release policy and the two inert noise ids stay as parameters so saved sessions load, but like the Rack panel the editor omits them. The programs are Init and the 100 `PSS` voices; the 50 modern presets are Rack patches only for now. The editor is a working one-control-per-parameter layout; the designed Rack panel below is not yet ported to it.

### Panel design

The Rack panel and its interactive layout prototype belong to the Reason adapter in the private `protocodus/reason-rack-extensions` repository (`Examples/Press78/Design/`). The plug-in editor here is the plain control grid described above.

### Repository layout

| Path | Purpose |
| --- | --- |
| `Source/DSP` | Fixed-storage polyphonic engine and generated circuit/preset tables (JUCE-free, C++17) |
| `Source/Plugin*`, `Source/ControlMapping.h` | JUCE plug-in front end and its control mapping |
| `Assets/controls.json` | Parameter contract shared with the Rack adapter: 64 controls, two inert legacy noise properties and the hidden release policy |
| `Assets/rack-automation.json` | Frozen Reason automation IDs |
| `Assets/FactoryBank` | 100 original `PSS` parameter patches, 50 modern Rack presets and provenance |
| `Tools/reference` | Frozen research implementation used as the comparison oracle |
| `Tools/prototypes` | Unadopted candidate patches and their checks, kept with their evidence |
| `Docs/research/migration.json` | Original source location and file hashes |
| `Tests/results` | Native validation, Python parity, circuit and timing evidence |

## Known gaps

The [four-waveform fidelity audit](Docs/research/oscillator-fidelity-audit-2026-10-19.md) verifies the current mathematical shapes and exposes higher-partial, internal-DC and capture-chain constraints. Low-order shape agreement does not establish OPU ROM precision, arithmetic or native timing. The separate Drive/output study distinguishes creative saturation and safety limiting from unidentified hardware overload.

A focused [Human Voice 1 release audit](Docs/research/human-voice1-release-audit.md) finds a tail deficit under the original inferred timing. At 150–220 ms after the clearest inferred note-off, its tracked carrier component falls about 16 dB in the recording versus 60 dB in the former model. The selected B estimate now applies an envelope-Reverb tail: after the carrier envelope reaches an assumed 18 dB during release, both operators use no faster than their own native RR4/RKS slope. Already slower releases remain slower. This sibling-inspired choice is enabled by default, but the exact [PSS-780 Reverb behavior](Docs/research/reverb-release-evidence.md) remains unidentified. The original [release A/B report](build/release-analysis-20261018T0905/report.html) and [timing sensitivity test](Docs/research/timing-sensitivity-2026-10-19.md) remain historical diagnostics; the latter reverses Human Voice 1's joint-band preference under alternative timing maps. The [new audition](Docs/research/assumed-hardware-auditions-2026-10-19.md) and listener choice do not establish measured hardware fidelity.

- The YM3420's converter is undocumented: whether its DAC holds each sample, its word length, and the fixed 14.3 kHz spur in the PSS-680 recordings are not modelled. Those recordings rule out a coarse converter, any 9- or 10-bit linear one or the YM2413, YM3438 and YM2612 formats, but bound only its step, at most 2⁻¹⁰ of a voice's peak, so no word length is modelled ([converter resolution](Docs/research/ym3420-converter-resolution-2026-10-20.md)). The alias lines' pitches follow from the chip rate; their levels also depend on that converter and on the recordings' capture chain.
- The speakers' sound is not modelled: no response or cabinet data exists for the PSS-780's 12 cm XG516A00 drivers. Their electrical load on AUX borrows a similar driver's parameters.
- Where the amplifier starts to clip rests on an estimated level: one engine unit at the top of the volume slider is taken as 1.0 V, inside the 0.5 to 2.3 V the mixer's swing and the manual's overload warning allow, so the **Volume** at which clipping sets in is uncertain by about ±6 dB. It also assumes an active mixer drives the slider, as in the PSS-480 and the output circuit above; if the PSS-780 mixed passively like the PSS-270, the slider would carry 0.148 of that level and the amplifier would not clip below full scale. The idle current, the adaptor's rating and reservoir, and the PSS-780's own supply circuit are estimates or borrowed from the PSS-480.
- Worn cells borrow their resistance through life from AA pulse data; no C-cell figures exist. The +5 V load, the follower's gain and the zener's knee are estimates, which place the rail where +5 V gives way anywhere from 5.8 to 7.5 V. How the YM3420's output level and the chorus clock change as +5 V falls is not documented, so both stay fixed; so does the 1.9 mF on +5 V, which would slow its fastest falls.
- The plug-in has only passed the checks CI runs; it has not been tried in a DAW. Its editor is a plain control grid, not the designed panel.
- The b11–b15 fidelity work, its rejected candidates and the open fidelity requirements are in [fidelity status, 2026-10-19](Docs/research/fidelity-status-2026-10-19.md); no superlative accuracy claim follows from it.
- The native evidence, sanitizer runs, hardware comparison and Rack prototype validation are recorded in [native evidence, 2026-10-18](Docs/validation/native-evidence-2026-10-18.md) for b9 and in the fidelity status above for b11 and b12. They establish agreement with the research model, not with Yamaha hardware.
- The preset source is recorded in [bank provenance](Assets/FactoryBank/provenance.json). Public availability of a SysEx archive and the editor project's license do not establish permission to distribute Yamaha's factory bank commercially. No research videos, recordings, manual scans or executable Yamaha firmware are shipped in this repository. `Press78` has not received trademark clearance; development names and source availability are not legal clearance.

## Build

The engine, tools and unit, fuzz and audio tiers build without JUCE:

```sh
cmake -S . -B build-dsp -DCMAKE_BUILD_TYPE=Release -DPRESS78_BUILD_PLUGIN=OFF -DBUILD_TESTING=ON
cmake --build build-dsp --parallel
ctest --test-dir build-dsp -L unit --output-on-failure
build-dsp/press78_render --output /tmp/press78-init.wav --note 60 --seconds 3 --gate 1.5
```

The plug-in build fetches the pinned JUCE 8.0.14 and clap-juce-extensions unless `PRESS78_JUCE_PATH` and `PRESS78_CLAP_JUCE_EXTENSIONS_PATH` point to local checkouts. On Linux, install JUCE's ALSA, FreeType, fontconfig and X11 development packages first (the list is in `.github/workflows/ci.yml`); on macOS, `scripts/build-macos.sh` builds universal binaries and runs every test.

```sh
cmake -S . -B build-plugin -DCMAKE_BUILD_TYPE=Release -DPRESS78_BUILD_PLUGIN=ON -DBUILD_TESTING=ON
cmake --build build-plugin --parallel
ctest --test-dir build-plugin --output-on-failure
```

Every test is `Press78.<Suite>` with one tier label: `unit` (including `Press78.DspFuzzReplay`, the fuzz harness replaying `Tests/Fixtures/fuzz/` and seeded inputs), `audio` (`Press78.AudioDemos` renders every demo twice and compares the bits), `render` (`Press78.EditorRender`, the editor screenshot), `fuzz` (`Press78.DspFuzz`, and `Press78.ParameterMatrix` in the plug-in build) or `perf` (`Press78.CpuBudget`, the demos timed against a budget in a Release build). `-DPRESS78_ENABLE_SANITIZERS=ON` builds everything under ASan + UBSan, and `-DPRESS78_BUILD_FUZZER=ON` with Clang builds the libFuzzer target. `scripts/validate-plugins.sh build-plugin Press78 aumu P781 Pr78 0x50373830` runs pluginval, clap-validator and, on macOS, auval on a plug-in build.

`press78_render --raw <66 hexadecimal digits>` renders a decoded 33-byte voice. `--transparent` disables the output circuit, envelope-Reverb estimate, creative tone filter, DC removal and output protection and sets unity gain for reference comparisons. Native diagnostic callers can select `--envelope-reverb 0|1` independently; this is not a new host parameter. Other options include gain, chorus mix, drive, clock offset and clock drift. See `Tools/NativeRender.cpp` for the complete bounded CLI.

Numerical comparison tools additionally require NumPy and SciPy; Numba accelerates the frozen Python renderer when available.

```sh
python3 Tools/generate_factory.py --check
python3 Tools/generate_analog.py --check
python3 Tools/check_python_parity.py --help
python3 Tools/check_analog_runtime.py --help
python3 Tools/check_chorus_runtime.py --help
python3 Tools/check_circuit_noise.py
```

To regenerate the Rack parameter declarations, mappings and 151 local development patches:

```sh
python3 Tools/generate_rack.py /path/to/SDK-worktree/Examples/Press78
python3 Tools/check_rack_contract.py /path/to/SDK-worktree/Examples/Press78
```

## Licensing

Press78's source is available under the [PolyForm Noncommercial License
1.0.0](LICENSE): you may read, study, change and share it for any non-commercial
purpose, but not sell it or use it commercially. Official Protocodus builds
carry an additional permission in the same file to use them for any purpose,
including making music commercially. Commits made before this licence change
were published under MIT and remain so. The plug-in builds with JUCE (official
builds use a commercial JUCE 8 Starter licence) and clap-juce-extensions; see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The factory voice parameters
are not covered by that licence and their redistribution rights are unresolved;
the notices file explains why.
