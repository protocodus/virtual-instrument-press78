# Press78

Press78 is an editable two-operator FM synthesizer derived from the PSS-780 research experiment, as a VST3, CLAP and Standalone plug-in on macOS, Windows and Linux, plus an Audio Unit on macOS. Its independent C++17 engine also drives an eight-unit Reason Rack Extension prototype. It uses original Press78 branding and focuses on synthesis; it does not reproduce the keyboard, rhythms or accompaniment system. It is a behavioral model, not a bit-exact YM3420 emulator, and commercial redistribution of the imported factory bank has not been cleared.

![Press78 editor](Docs/screenshots/press78.png)

## Audio demos

One demo per factory voice, rendered by the main build from the phrases in `Docs/audio/midi` through the plug-in's default controls (the Real startup profile, Volume 0.25). Levels are the bank's own; nothing is normalised.

<!-- audio-demos-begin -->

| # | Preset | Demo | Length | Peak |
| --- | --- | --- | --- | --- |
| 1 | PSS 00 Piano 1 | [001-pss-00-piano-1.mp3](Docs/audio/001-pss-00-piano-1.mp3) | 12.9 s | -12.9 dBFS |
| 2 | PSS 01 Piano 2 | [002-pss-01-piano-2.mp3](Docs/audio/002-pss-01-piano-2.mp3) | 12.9 s | -14.8 dBFS |
| 3 | PSS 02 Electric Piano 1 | [003-pss-02-electric-piano-1.mp3](Docs/audio/003-pss-02-electric-piano-1.mp3) | 13.9 s | -10.9 dBFS |
| 4 | PSS 03 Electric Piano 2 | [004-pss-03-electric-piano-2.mp3](Docs/audio/004-pss-03-electric-piano-2.mp3) | 13.9 s | -13.8 dBFS |
| 5 | PSS 04 Honky-Tonk Piano | [005-pss-04-honky-tonk-piano.mp3](Docs/audio/005-pss-04-honky-tonk-piano.mp3) | 11.0 s | -14.3 dBFS |
| 6 | PSS 05 Toy Piano | [006-pss-05-toy-piano.mp3](Docs/audio/006-pss-05-toy-piano.mp3) | 11.4 s | -21.1 dBFS |
| 7 | PSS 06 Reed Organ | [007-pss-06-reed-organ.mp3](Docs/audio/007-pss-06-reed-organ.mp3) | 14.0 s | -9.6 dBFS |
| 8 | PSS 07 Pipe Organ 1 | [008-pss-07-pipe-organ-1.mp3](Docs/audio/008-pss-07-pipe-organ-1.mp3) | 15.9 s | -8.3 dBFS |
| 9 | PSS 08 Pipe Organ 2 | [009-pss-08-pipe-organ-2.mp3](Docs/audio/009-pss-08-pipe-organ-2.mp3) | 15.9 s | -10.7 dBFS |
| 10 | PSS 09 Small Church Organ | [010-pss-09-small-church-organ.mp3](Docs/audio/010-pss-09-small-church-organ.mp3) | 15.9 s | -7.2 dBFS |
| 11 | PSS 10 Electronic Organ | [011-pss-10-electronic-organ.mp3](Docs/audio/011-pss-10-electronic-organ.mp3) | 12.5 s | -6.8 dBFS |
| 12 | PSS 11 Transistor Organ | [012-pss-11-transistor-organ.mp3](Docs/audio/012-pss-11-transistor-organ.mp3) | 11.8 s | -6.3 dBFS |
| 13 | PSS 12 Tremolo Organ | [013-pss-12-tremolo-organ.mp3](Docs/audio/013-pss-12-tremolo-organ.mp3) | 13.4 s | -11.1 dBFS |
| 14 | PSS 13 Jazz Organ | [014-pss-13-jazz-organ.mp3](Docs/audio/014-pss-13-jazz-organ.mp3) | 11.1 s | -12.8 dBFS |
| 15 | PSS 14 Street Organ | [015-pss-14-street-organ.mp3](Docs/audio/015-pss-14-street-organ.mp3) | 11.0 s | -16.4 dBFS |
| 16 | PSS 15 Harpsichord 1 | [016-pss-15-harpsichord-1.mp3](Docs/audio/016-pss-15-harpsichord-1.mp3) | 12.0 s | -15.4 dBFS |
| 17 | PSS 16 Harpsichord 2 | [017-pss-16-harpsichord-2.mp3](Docs/audio/017-pss-16-harpsichord-2.mp3) | 12.9 s | -16.9 dBFS |
| 18 | PSS 17 Funky Clavi | [018-pss-17-funky-clavi.mp3](Docs/audio/018-pss-17-funky-clavi.mp3) | 14.9 s | -19.0 dBFS |
| 19 | PSS 18 Celesta | [019-pss-18-celesta.mp3](Docs/audio/019-pss-18-celesta.mp3) | 13.4 s | -20.0 dBFS |
| 20 | PSS 19 Glass Celesta | [020-pss-19-glass-celesta.mp3](Docs/audio/020-pss-19-glass-celesta.mp3) | 14.4 s | -23.2 dBFS |
| 21 | PSS 20 Accordion | [021-pss-20-accordion.mp3](Docs/audio/021-pss-20-accordion.mp3) | 12.0 s | -17.6 dBFS |
| 22 | PSS 21 Bandoneon | [022-pss-21-bandoneon.mp3](Docs/audio/022-pss-21-bandoneon.mp3) | 13.3 s | -17.8 dBFS |
| 23 | PSS 22 Trumpet | [023-pss-22-trumpet.mp3](Docs/audio/023-pss-22-trumpet.mp3) | 13.9 s | -21.5 dBFS |
| 24 | PSS 23 Mute Trumpet | [024-pss-23-mute-trumpet.mp3](Docs/audio/024-pss-23-mute-trumpet.mp3) | 15.3 s | -27.4 dBFS |
| 25 | PSS 24 Wow Trumpet | [025-pss-24-wow-trumpet.mp3](Docs/audio/025-pss-24-wow-trumpet.mp3) | 15.0 s | -26.0 dBFS |
| 26 | PSS 25 Electric Trumpet | [026-pss-25-electric-trumpet.mp3](Docs/audio/026-pss-25-electric-trumpet.mp3) | 13.1 s | -20.2 dBFS |
| 27 | PSS 26 Horn | [027-pss-26-horn.mp3](Docs/audio/027-pss-26-horn.mp3) | 16.5 s | -21.7 dBFS |
| 28 | PSS 27 Alpenhorn | [028-pss-27-alpenhorn.mp3](Docs/audio/028-pss-27-alpenhorn.mp3) | 17.1 s | -19.7 dBFS |
| 29 | PSS 28 Trombone | [029-pss-28-trombone.mp3](Docs/audio/029-pss-28-trombone.mp3) | 15.3 s | -22.0 dBFS |
| 30 | PSS 29 Tuba | [030-pss-29-tuba.mp3](Docs/audio/030-pss-29-tuba.mp3) | 17.1 s | -16.9 dBFS |
| 31 | PSS 30 Brass Ensemble | [031-pss-30-brass-ensemble.mp3](Docs/audio/031-pss-30-brass-ensemble.mp3) | 14.4 s | -15.2 dBFS |
| 32 | PSS 31 Soprano Sax | [032-pss-31-soprano-sax.mp3](Docs/audio/032-pss-31-soprano-sax.mp3) | 12.4 s | -30.4 dBFS |
| 33 | PSS 32 Alto Sax | [033-pss-32-alto-sax.mp3](Docs/audio/033-pss-32-alto-sax.mp3) | 15.0 s | -19.1 dBFS |
| 34 | PSS 33 Tenor Sax | [034-pss-33-tenor-sax.mp3](Docs/audio/034-pss-33-tenor-sax.mp3) | 15.0 s | -24.1 dBFS |
| 35 | PSS 34 Clarinet | [035-pss-34-clarinet.mp3](Docs/audio/035-pss-34-clarinet.mp3) | 12.4 s | -26.3 dBFS |
| 36 | PSS 35 Bass Clarinet | [036-pss-35-bass-clarinet.mp3](Docs/audio/036-pss-35-bass-clarinet.mp3) | 13.4 s | -20.6 dBFS |
| 37 | PSS 36 Oboe | [037-pss-36-oboe.mp3](Docs/audio/037-pss-36-oboe.mp3) | 12.4 s | -29.1 dBFS |
| 38 | PSS 37 Basson | [038-pss-37-basson.mp3](Docs/audio/038-pss-37-basson.mp3) | 12.9 s | -26.8 dBFS |
| 39 | PSS 38 Piccolo | [039-pss-38-piccolo.mp3](Docs/audio/039-pss-38-piccolo.mp3) | 14.6 s | -31.0 dBFS |
| 40 | PSS 39 Flute | [040-pss-39-flute.mp3](Docs/audio/040-pss-39-flute.mp3) | 12.4 s | -28.0 dBFS |
| 41 | PSS 40 Panflute | [041-pss-40-panflute.mp3](Docs/audio/041-pss-40-panflute.mp3) | 13.9 s | -22.5 dBFS |
| 42 | PSS 41 Recorder | [042-pss-41-recorder.mp3](Docs/audio/042-pss-41-recorder.mp3) | 11.6 s | -28.1 dBFS |
| 43 | PSS 42 Ocarina | [043-pss-42-ocarina.mp3](Docs/audio/043-pss-42-ocarina.mp3) | 13.4 s | -28.2 dBFS |
| 44 | PSS 43 Woodwind Ensemble | [044-pss-43-woodwind-ensemble.mp3](Docs/audio/044-pss-43-woodwind-ensemble.mp3) | 15.5 s | -18.1 dBFS |
| 45 | PSS 44 Bagpipe | [045-pss-44-bagpipe.mp3](Docs/audio/045-pss-44-bagpipe.mp3) | 11.2 s | -27.3 dBFS |
| 46 | PSS 45 Harmonica | [046-pss-45-harmonica.mp3](Docs/audio/046-pss-45-harmonica.mp3) | 15.0 s | -23.9 dBFS |
| 47 | PSS 46 Jug | [047-pss-46-jug.mp3](Docs/audio/047-pss-46-jug.mp3) | 12.8 s | -17.8 dBFS |
| 48 | PSS 47 Kazoo | [048-pss-47-kazoo.mp3](Docs/audio/048-pss-47-kazoo.mp3) | 15.7 s | -26.4 dBFS |
| 49 | PSS 48 Samba Whistle | [049-pss-48-samba-whistle.mp3](Docs/audio/049-pss-48-samba-whistle.mp3) | 13.4 s | -28.6 dBFS |
| 50 | PSS 49 Acoustic Guitar | [050-pss-49-acoustic-guitar.mp3](Docs/audio/050-pss-49-acoustic-guitar.mp3) | 15.0 s | -7.6 dBFS |
| 51 | PSS 50 Classic Guitar | [051-pss-50-classic-guitar.mp3](Docs/audio/051-pss-50-classic-guitar.mp3) | 18.0 s | -11.1 dBFS |
| 52 | PSS 51 Hawaiian Guitar | [052-pss-51-hawaiian-guitar.mp3](Docs/audio/052-pss-51-hawaiian-guitar.mp3) | 12.1 s | -19.2 dBFS |
| 53 | PSS 52 Jazz Guitar | [053-pss-52-jazz-guitar.mp3](Docs/audio/053-pss-52-jazz-guitar.mp3) | 11.5 s | -11.3 dBFS |
| 54 | PSS 53 Rock Guitar 1 | [054-pss-53-rock-guitar-1.mp3](Docs/audio/054-pss-53-rock-guitar-1.mp3) | 12.7 s | -26.4 dBFS |
| 55 | PSS 54 Rock Guitar 2 | [055-pss-54-rock-guitar-2.mp3](Docs/audio/055-pss-54-rock-guitar-2.mp3) | 11.6 s | -18.2 dBFS |
| 56 | PSS 55 Rock Guitar 3 | [056-pss-55-rock-guitar-3.mp3](Docs/audio/056-pss-55-rock-guitar-3.mp3) | 13.1 s | -22.5 dBFS |
| 57 | PSS 56 Pedal Steel Guitar | [057-pss-56-pedal-steel-guitar.mp3](Docs/audio/057-pss-56-pedal-steel-guitar.mp3) | 12.4 s | -24.7 dBFS |
| 58 | PSS 57 Tremolo Guitar | [058-pss-57-tremolo-guitar.mp3](Docs/audio/058-pss-57-tremolo-guitar.mp3) | 16.8 s | -12.3 dBFS |
| 59 | PSS 58 12String Guitar | [059-pss-58-12string-guitar.mp3](Docs/audio/059-pss-58-12string-guitar.mp3) | 14.0 s | -12.7 dBFS |
| 60 | PSS 59 Electric Bass | [060-pss-59-electric-bass.mp3](Docs/audio/060-pss-59-electric-bass.mp3) | 12.0 s | -14.8 dBFS |
| 61 | PSS 60 Mute Bass | [061-pss-60-mute-bass.mp3](Docs/audio/061-pss-60-mute-bass.mp3) | 12.8 s | -14.2 dBFS |
| 62 | PSS 61 Picked Bass | [062-pss-61-picked-bass.mp3](Docs/audio/062-pss-61-picked-bass.mp3) | 11.3 s | -16.4 dBFS |
| 63 | PSS 62 Slap Bass | [063-pss-62-slap-bass.mp3](Docs/audio/063-pss-62-slap-bass.mp3) | 13.0 s | -23.1 dBFS |
| 64 | PSS 63 Wood Bass 1 | [064-pss-63-wood-bass-1.mp3](Docs/audio/064-pss-63-wood-bass-1.mp3) | 13.2 s | -15.1 dBFS |
| 65 | PSS 64 Wood Bass 2 | [065-pss-64-wood-bass-2.mp3](Docs/audio/065-pss-64-wood-bass-2.mp3) | 12.3 s | -13.2 dBFS |
| 66 | PSS 65 Bowed Bass | [066-pss-65-bowed-bass.mp3](Docs/audio/066-pss-65-bowed-bass.mp3) | 14.5 s | -17.8 dBFS |
| 67 | PSS 66 Banjo | [067-pss-66-banjo.mp3](Docs/audio/067-pss-66-banjo.mp3) | 15.6 s | -18.0 dBFS |
| 68 | PSS 67 Ukulele | [068-pss-67-ukulele.mp3](Docs/audio/068-pss-67-ukulele.mp3) | 13.2 s | -10.8 dBFS |
| 69 | PSS 68 Mandolin | [069-pss-68-mandolin.mp3](Docs/audio/069-pss-68-mandolin.mp3) | 12.7 s | -12.9 dBFS |
| 70 | PSS 69 Harp | [070-pss-69-harp.mp3](Docs/audio/070-pss-69-harp.mp3) | 13.0 s | -10.7 dBFS |
| 71 | PSS 70 Sitar | [071-pss-70-sitar.mp3](Docs/audio/071-pss-70-sitar.mp3) | 12.1 s | -24.8 dBFS |
| 72 | PSS 71 Shamisen | [072-pss-71-shamisen.mp3](Docs/audio/072-pss-71-shamisen.mp3) | 10.9 s | -19.1 dBFS |
| 73 | PSS 72 Jamisen | [073-pss-72-jamisen.mp3](Docs/audio/073-pss-72-jamisen.mp3) | 11.5 s | -22.1 dBFS |
| 74 | PSS 73 Koto | [074-pss-73-koto.mp3](Docs/audio/074-pss-73-koto.mp3) | 12.8 s | -18.9 dBFS |
| 75 | PSS 74 Violin 1 | [075-pss-74-violin-1.mp3](Docs/audio/075-pss-74-violin-1.mp3) | 12.5 s | -26.6 dBFS |
| 76 | PSS 75 Violin 2 | [076-pss-75-violin-2.mp3](Docs/audio/076-pss-75-violin-2.mp3) | 11.5 s | -26.5 dBFS |
| 77 | PSS 76 Cello | [077-pss-76-cello.mp3](Docs/audio/077-pss-76-cello.mp3) | 13.4 s | -19.5 dBFS |
| 78 | PSS 77 Strings | [078-pss-77-strings.mp3](Docs/audio/078-pss-77-strings.mp3) | 14.2 s | -13.1 dBFS |
| 79 | PSS 78 Synth Brass | [079-pss-78-synth-brass.mp3](Docs/audio/079-pss-78-synth-brass.mp3) | 13.9 s | -18.1 dBFS |
| 80 | PSS 79 Synth Bass | [080-pss-79-synth-bass.mp3](Docs/audio/080-pss-79-synth-bass.mp3) | 10.5 s | -22.4 dBFS |
| 81 | PSS 80 Synth Tom | [081-pss-80-synth-tom.mp3](Docs/audio/081-pss-80-synth-tom.mp3) | 12.9 s | -16.1 dBFS |
| 82 | PSS 81 Carillon | [082-pss-81-carillon.mp3](Docs/audio/082-pss-81-carillon.mp3) | 17.1 s | -22.9 dBFS |
| 83 | PSS 82 Chimes | [083-pss-82-chimes.mp3](Docs/audio/083-pss-82-chimes.mp3) | 17.1 s | -23.0 dBFS |
| 84 | PSS 83 Hand Bell | [084-pss-83-hand-bell.mp3](Docs/audio/084-pss-83-hand-bell.mp3) | 15.6 s | -28.6 dBFS |
| 85 | PSS 84 Tubular Bells | [085-pss-84-tubular-bells.mp3](Docs/audio/085-pss-84-tubular-bells.mp3) | 18.4 s | -25.7 dBFS |
| 86 | PSS 85 Timpani | [086-pss-85-timpani.mp3](Docs/audio/086-pss-85-timpani.mp3) | 14.8 s | -10.1 dBFS |
| 87 | PSS 86 Steel Drum 1 | [087-pss-86-steel-drum-1.mp3](Docs/audio/087-pss-86-steel-drum-1.mp3) | 13.3 s | -22.5 dBFS |
| 88 | PSS 87 Steel Drum 2 | [088-pss-87-steel-drum-2.mp3](Docs/audio/088-pss-87-steel-drum-2.mp3) | 12.5 s | -16.7 dBFS |
| 89 | PSS 88 Glockenspiel | [089-pss-88-glockenspiel.mp3](Docs/audio/089-pss-88-glockenspiel.mp3) | 14.6 s | -19.7 dBFS |
| 90 | PSS 89 Marimba 1 | [090-pss-89-marimba-1.mp3](Docs/audio/090-pss-89-marimba-1.mp3) | 14.6 s | -8.3 dBFS |
| 91 | PSS 90 Marimba 2 | [091-pss-90-marimba-2.mp3](Docs/audio/091-pss-90-marimba-2.mp3) | 15.8 s | -9.4 dBFS |
| 92 | PSS 91 Vibraphone | [092-pss-91-vibraphone.mp3](Docs/audio/092-pss-91-vibraphone.mp3) | 11.9 s | -14.3 dBFS |
| 93 | PSS 92 Human Chorus | [093-pss-92-human-chorus.mp3](Docs/audio/093-pss-92-human-chorus.mp3) | 13.5 s | -14.9 dBFS |
| 94 | PSS 93 Human Voice 1 | [094-pss-93-human-voice-1.mp3](Docs/audio/094-pss-93-human-voice-1.mp3) | 15.5 s | -26.4 dBFS |
| 95 | PSS 94 Human Voice 2 | [095-pss-94-human-voice-2.mp3](Docs/audio/095-pss-94-human-voice-2.mp3) | 16.6 s | -28.4 dBFS |
| 96 | PSS 95 Whistle | [096-pss-95-whistle.mp3](Docs/audio/096-pss-95-whistle.mp3) | 16.2 s | -22.1 dBFS |
| 97 | PSS 96 Ice Block | [097-pss-96-ice-block.mp3](Docs/audio/097-pss-96-ice-block.mp3) | 12.7 s | -26.8 dBFS |
| 98 | PSS 97 Musical Saw | [098-pss-97-musical-saw.mp3](Docs/audio/098-pss-97-musical-saw.mp3) | 12.4 s | -24.4 dBFS |
| 99 | PSS 98 Music Box | [099-pss-98-music-box.mp3](Docs/audio/099-pss-98-music-box.mp3) | 11.6 s | -28.6 dBFS |
| 100 | PSS 99 Sine Wave | [100-pss-99-sine-wave.mp3](Docs/audio/100-pss-99-sine-wave.mp3) | 11.1 s | -17.8 dBFS |

<!-- audio-demos-end -->

## Version history

### Unreleased — 0.1.0 — engine, Rack prototype and plug-in front end

- Two-operator FM engine with the 100 `PSS` factory voices and an Init sine, sibling-circuit output stage, Studio and Recorded chorus, White and Circuit noise, and clock variation.
- Reason Rack Extension prototype 0.1.0b7, built outside this repository.
- First JUCE plug-in: all 65 controls as parameters, Init plus the 100 voices as programs, and a working editor; the Rack panel design is not yet ported to it.

## Downloads

<!-- build-download-begin -->
<!-- build-download-end -->

---

## How it works

### Engine

Both operators expose ratio, fine/coarse detune, four waveform families, raw envelope rates, key scaling and AM. Additional controls cover feedback, velocity, LFO phase/depth/delay, twelve-voice allocation, pitch bend, mod wheel, clock variation, analog output, tone, drive, chorus, stereo width and noise. The Rack adapter adds separate MIDI/CV note ownership and Note/Gate/FM/Level CV inputs. All 65 controls have explicit Reason automation mappings, frozen in `Assets/rack-automation.json`; Volume/Tone retain MIDI CC7/74.

The port preserves the frozen Python raw-FM behavior. It adds fixed-storage voice management, short voice-stealing tails, continuous-control smoothing and host-rate conversion. The internal 48 kHz timebase, floating-point operators, envelope laws and detune mappings are modeling choices, not recovered chip internals. Nominal reconstruction latency is 32 internal samples, rounded up to host frames for reporting. Clock controls also scale that physical delay; upward clock shifts can alias near-Nyquist energy. Clock drift and noise are controllable scenarios, not measurements of aged hardware. Memory faults and random digital bit corruption are not introduced as normal vintage behavior.

### Output circuit

The enabled-by-default output circuit is the six-section small-signal transfer from the researched **PSS-480** circuit, used explicitly as a sibling surrogate. It is not a recovered PSS-780 board, a verified YM3420 DAC transfer, or a transistor-level model. Drive is a separate creative saturation control.

### Chorus

Two realtime chorus modes are available. **Studio** preserves the original creative delay effect. **Recorded** implements the frozen v3 effective stereo transfer from the PSS-780 recording: roughly 0.49–1.51 ms delay, a continuous 0.954647 Hz LFO, second-harmonic motion and direct mid leakage. It adds no whole-output latency. The rate and depth remain editable. This is a recording-derived approximation, not an identified MN3206 circuit. The offline v4 branch correction remains a reference because an exact causal port would need about 21.83 ms lookahead compensation at 48 kHz.

### Noise

The optional **Circuit** noise mode uses the PSS-480 resistor/opamp network and its stereo covariance: 300 K resistor thermal noise and independent 10 nV/√Hz white opamp input sources, represented by twelve states and fourteen sources. Noise level scales output relative to one fixed 11.96866768 µVrms continuous 20–20 kHz reference, before master volume. Bilinear discretization retains its high-frequency warping: at 48 kHz the predicted 20–20 kHz level is about 0.9228 times that reference, with no per-rate or per-clip normalization. It is a sibling-circuit scenario; absolute PSS-780 noise in dBFS is not known. White noise remains available. Rack Real defaults to Circuit noise at 0.002; the portable engine constructor keeps zero added noise. Neither mode claims recovered YM3420 conversion noise, BBD noise, capacitor aging or memory corruption.

### Startup profile and factory bank

The Rack Init and all 100 factory patches now use the **Real** startup profile: related-hardware output circuit on, Recorded chorus at its captured rate/depth and full reference side level, Circuit noise at 0.002 before master gain, and a slow ±20 ppm clock excursion at 0.1 Hz (about ±0.035 cents). Clock offset stays zero. Noise amplitude and clock excursion are explicit modeling choices, not recovered PSS-780 calibration. The creative Drive control remains zero. All values stay editable and persist with patches; existing saved songs retain their stored values. The portable engine constructor retains its earlier defaults for reference-tool compatibility. Model selectors and fine calibration are on the rear.

Init is an independently defined sine patch. The public development bank contains the 100 original parameter presets as `PSS 00 …` through `PSS 99 …`. Loading/editing a Rack patch retimbres held voices while preserving their oscillator/envelope state. The standalone engine also offers future-voices-only program snapshots.

### Plug-in front end

The plug-in's parameter IDs are the control ids in `Assets/controls.json`, the same names as the Rack properties; `Source/PluginControls.h` is generated from that file by `Tools/generate_plugin_controls.py`. `Source/ControlMapping.h` maps the controls to the engine's patch and controls for both the plug-in and the demo renderer. Program 0 is Init and programs 1–100 are the factory voices; a program change sets the 36 sound controls and leaves performance and output controls alone, and editing a sound control retimbres held voices, as the Rack does. Pitch bend scales by Pitch bend range; the mod wheel adds its position times Wheel to vibrato to Pitch depth (this mapping is the plug-in's own choice; the Rack adapter's is not in this repository). The editor is a working one-control-per-parameter layout; the designed Rack panel below is not yet ported to it.

### Panel design

Open [the interactive design preview](Assets/Design/index.html). Layout study 07 compacts the panel from twelve to eight rack units with consistent section padding and puts 35 main sound/performance controls on the front, with 30 detailed sound, calibration and configuration controls on the rear. It combines the canonical Protocodus logo, YouKnow's DIN lettering and recessed groups with charcoal ABS, cyan, lavender, coral and ivory inspired by the PSS-780 moodboard. Doubled pointer arrows remain clear of the knob number wells. The preview has editable operator controls and all 100 factory voices. It demonstrates layout and parameter relationships, without audio. [Design notes](Assets/Design/README.md) describe the front, rear and folded panels. Both native GUI asset sets and the native local/universal builds carry this styling. Level now increases clockwise while preserving the original raw attenuation values; clearer envelope/unit labels and value arcs improve editing.

### Repository layout

| Path | Purpose |
| --- | --- |
| `Source/DSP` | Fixed-storage polyphonic engine and generated circuit/preset tables (JUCE-free, C++17) |
| `Source/Plugin*`, `Source/ControlMapping.h` | JUCE plug-in front end and its control mapping |
| `Assets/controls.json` | Canonical 65-control parameter contract, shared with the Rack adapter |
| `Assets/rack-automation.json` | Frozen Reason automation IDs |
| `Assets/FactoryBank` | 100 imported parameter patches, all named with `PSS` prefix, plus provenance |
| `Assets/Design` | Panel geometry, SVG/PNG panels and the interactive HTML wireframe |
| `Tools/reference` | Frozen research implementation used as the comparison oracle |
| `Docs/research/migration.json` | Original source location and file hashes |
| `Tests/results` | Native validation, Python parity, circuit and timing evidence |

## Known gaps

A focused [Human Voice 1 release audit](Docs/research/human-voice1-release-audit.md) confirms a tail deficit in the reused recording. At 150–220 ms after the clearest inferred note-off, its tracked carrier component falls about 16 dB in the recording versus 60 dB in the model. The preset import is correct and the baseline has no target-voice steals. The separate [Reverb performance effect](Docs/research/reverb-release-evidence.md) is not modeled; its exact envelope behavior remains unidentified. The [release A/B report](build/release-analysis-20261018T0905/report.html) includes carrier-only RR6/RR5 experiments, with timing, overlap and allocation caveats. These are diagnostic candidates, not factory or DSP changes.

- The plug-in has only passed the checks CI runs; it has not been tried in a DAW. Its editor is a plain control grid, not the designed panel.
- The Rack adapter lives in a local SDK workspace, not in `protocodus/reason-rack-extensions`, and its DSP directory is a generated snapshot of this repository (`Tools/sync_rack_dsp.py`) rather than the pinned submodule the portfolio standard asks for. The b5 Rack patch exporter uses the SDK’s canonical XML declaration after Recon rejected the earlier declaration during default Init loading. All 101 patch sound parameter maps are preserved. The b6 native display formatter also fixes a subsequent Recon drawing crash caused by concatenating host-formatted text; independent regression tests cover all 50 numeric readouts, with 444 passing cases and an explicit reproduction of the prior failure.
- The native evidence, sanitizer runs, hardware comparison and Rack prototype validation are recorded in [native evidence, 2026-10-18](Docs/validation/native-evidence-2026-10-18.md). They establish agreement with the research model, not with Yamaha hardware.
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

Every test is `Press78.<Suite>` with one tier label: `unit`, `audio` (`Press78.AudioDemos` renders every voice's demo twice and compares the bits), `render` (`Press78.EditorRender`, the editor screenshot) or `fuzz` (`Press78.DspFuzz`, and `Press78.ParameterMatrix` in the plug-in build). `-DPRESS78_ENABLE_SANITIZERS=ON` builds everything under ASan + UBSan, and `-DPRESS78_BUILD_LIBFUZZER=ON` with Clang builds the libFuzzer target.

`press78_render --raw <66 hexadecimal digits>` renders a decoded 33-byte voice. `--transparent` disables the output circuit, creative tone filter, DC removal and output protection and sets unity gain for reference comparisons. Other options include gain, chorus mix, drive, noise, clock offset and clock drift. See `Tools/NativeRender.cpp` for the complete bounded CLI.

Numerical comparison tools additionally require NumPy and SciPy; Numba accelerates the frozen Python renderer when available.

```sh
python3 Tools/generate_factory.py --check
python3 Tools/generate_analog.py --check
python3 Tools/check_python_parity.py --help
python3 Tools/check_analog_runtime.py --help
python3 Tools/check_chorus_runtime.py --help
python3 Tools/check_circuit_noise.py
```

To regenerate the Rack parameter declarations, mappings and 101 local development patches:

```sh
python3 Tools/generate_rack.py /path/to/SDK-worktree/Examples/Press78
python3 Tools/sync_rack_dsp.py /path/to/SDK-worktree/Examples/Press78
python3 Tools/check_rack_contract.py /path/to/SDK-worktree/Examples/Press78
```

[Shop copy](Docs/release/shop-copy.md) and its [metadata](Docs/release/shop-metadata.json) follow the same format as the other Protocodus synths; they are generated from the Rack adapter's authored `SHOP.md`.

## Licensing

Press78's source code is MIT-licensed; see [LICENSE](LICENSE). The plug-in builds with JUCE (AGPLv3 or a commercial JUCE licence) and clap-juce-extensions; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The factory voice parameters are not covered by the MIT licence and their redistribution rights are unresolved; the notices file explains why.
