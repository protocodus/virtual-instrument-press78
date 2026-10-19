# Independent hardware recording audit — 18 October 2026

The existing PSS-780 preset tour remains useful regression material, but it cannot answer every remaining FM question. This pass obtained a genuinely separate waveform experiment on a PSS-680, a controlled parameter demonstration on a PSS-480, and a longer PSS-580 preset tour containing Human Voice 1, Bowed Bass and Musical Saw. The waveform evidence supports the engine's current table identities. The envelope evidence exposes a substantial timing discrepancy, but does **not** uniquely identify a replacement global envelope law.

Measurements, source hashes, exact local paths and limitations are in [the accompanying JSON](recording-holdout-audit-2026-10-18.json). Copyrighted recordings and frames remain in the ignored `build/recording-audit-20261018` directory; they are not factory resources.

## What the original PSS-780 video can establish

[AndrewsVintageKeyboards' PSS-780 recording](https://www.youtube.com/watch?v=ONfIvtDOog0) is the already analyzed polyphonic *Eugenia* performance. Every preset has been inspected and scored. Its three difficult voices are diagnostic/training material, not independent holdouts. Reverb, Chorus and Vibrato are visibly on; Musical Saw additionally has Sustain on. MIDI-file note gates and one global affine alignment are known, but the sender, exact gate delivery, effect algorithm, routing and capture chain are not independently documented. A visible program number is not a sample-accurate program command. Existing detailed provenance remains in `native-hardware-benchmark.md` and the historical experiment's `research/recordings-v2.md`.

## Independent waveform experiment: PSS-680

[Kevin's recording](https://www.youtube.com/watch?v=KAHq65dWzG4) accompanies his [original Arduino experiment](https://diyelectromusic.com/2023/08/02/arduino-pss-680-synth-editor-part-1/). The procedure starts with the Sine Wave voice and changes only the carrier SIN TBL field through 0, 1, 2 and 3. His description explicitly excludes feedback, modulation and frequency multiplication. The physical keyboard and bank changes are visible. The first sound around a dump/program change can retain the previous table; the windows below avoid that transition.

Each window contains the same approximately C5 starting note. Hann-weighted least squares estimates 12 harmonic sine/cosine pairs plus DC, with a bounded fundamental search from 521 to 525 Hz. These are capture measurements, without EQ or separate harmonic gain fitting.

| Table | Source window | Fundamental | H2/H1 | H3/H1 |
|---|---:|---:|---:|---:|
| 0 | 10.50–10.85 s | 523.0664 Hz | −35.42 dB | −46.85 dB |
| 1 | 29.85–30.20 s | 523.0677 Hz | −37.71 dB | −13.95 dB |
| 2 | 39.12–39.32 s | 523.1209 Hz | −2.73 dB | −43.72 dB |
| 3 | 47.38–47.68 s | 523.0807 Hz | +1.05 dB | −12.74 dB |

Table 1 has a strong third harmonic and very little second harmonic. This supports `sin(phase) * abs(sin(phase))`; its ideal H3/H1 is −13.9794 dB. It contradicts substituting OPL2's half-wave/rectified table numbering merely because both chips are Yamaha FM devices. Table 2's even harmonics and suppressed third support half sine. Table 3 combines even harmonics with a third harmonic, consistent with half sine squared.

The exact partial amplitudes are **not** recovered ROM coefficients. Unknown speaker/capture response, note transitions, channel processing and the lossy stream affect them. In particular, the strong second harmonic in tables 2/3 must not be used to increase engine distortion or fit a DAC. The four fundamental estimates are consistent with one pitch but do not calibrate the oscillator clock. Waveform residuals are about4–7% of capture RMS. This experiment validates topology, not bit accuracy.

Artifacts: `kevin-waveform-analysis.json`, `analyze_kevin.py`, `kevin-overview.png`, `kevin-contact.jpg`, and the exact source media listed in the JSON.

## Independent envelope evidence: PSS-480

[Keen On Keys' synth-editor demonstration](https://www.youtube.com/watch?v=2TfpcAmaPGg) contains a particularly useful pure-carrier sequence around9:09–9:36. The editor visibly has modulation level0, carrier Sine/ratio1, AR41, D1R0, D2R20, RR8, SRR3 and RKS0. The note is approximately C4. It contrasts held and decaying notes by changing D1L.

The editor's D1L readout is inverted relative to the raw dump nibble. The [panel author's 2022 implementation](https://ctrlr.martintarenskeen.nl/yamaha-pss480-20220225.bpanelz) serializes raw D1L as `15 - displayed value`; its AR/D1R/D2R/RR values are direct. This later panel is a corroborating implementation, not the exact 2021 executable. Frames and the audible behavior independently agree: displayed D1L14/raw1 with D1R0 holds at peak; displayed15/raw0 enters D2. This supports checking the zero-distance D1 endpoint before applying a D1 increment.

The following measurements fit log amplitude against time. They use positive C4 cycle peaks from the decoded waveform, selected from music-only interiors, without onset or gain optimization. STFT4096/hop240 measurements independently give the same D2 result.

| Condition | Source fit window | Measured slope | Existing analytic prediction |
|---|---:|---:|---:|
| D1R0, raw D1L1 hold | 553.25–554.45 s | −0.014 dB/s | 0 dB/s |
| D2R20, raw D1L0 | 564.30–565.30 s | −21.241 dB/s | −64 dB/s |
| RR8 release | 554.55–554.70 s | −233.353 dB/s | −724.077 dB/s |
| RR8, repeated note | 569.90–570.03 s | −230.126 dB/s | −724.077 dB/s |

The two release regressions have R²>0.9995; the D2 regression has R²0.99985. Alternate D2 windows give approximately −21.1 to−21.3 dB/s. Formal regression errors describe the smooth captured curve, not uncertainty about the hardware law.

A roughly threefold slowdown of the analytic decay/release equations would predict these slopes much better. It is **not yet an identified hardware correction**: an undisclosed 3:1 compressor can also divide dB slopes, and the uploader gives no explicit unprocessed/ungated capture guarantee. The editor does not expose global hardware Reverb. The observed tail abruptly disappears near48 dB relative attenuation; this could be an instrument endpoint or a capture gate. It does not prove a48 dB chip envelope range or justify changing the96 dB model cutoff.

Three short AR41 attack fits using the model's attenuation-exponential form yield k≈627–636 s⁻¹ versus the model's1051.49 s⁻¹, with approximately1.5% waveform residual. Their short duration, few carrier cycles, analog transients and uncertain envelope shape prevent using them as a recovered attack law. They also do not show a simple threefold playback-time change.

No matched pure-carrier static TL-step series, second independently known D2 rate, or hardware Reverb toggle was recovered in this pass. A global timing change therefore needs another controlled measurement. The current Human Voice1 recording mismatch must not be declared solved by these examples.

Artifacts: `keen3-release-d1-corner-485.wav`, `keen3-d1corner-narrow.png`, `keen3-rr8-tails.png`, `keen3-ar41-attack-preliminary.json`, and the JSON's measured regressions. The later `build_audit.py` script recreates the tracked metadata from the locally retained sources.

## New longer target recordings: PSS-580

[KeyboardKrazy49's 100-voice tour](https://www.youtube.com/watch?v=NXPbPr4yrgA) is independent of Andrews' PSS-780 capture. Its physical program display and owner's ordered list identify the relevant sibling voices. The published list counts1–100; the keyboard display counts0–99. Useful guarded intervals, with about0.5 s uncertainty, are:

| Voice | PSS-580 program | Public-video interval | PSS-780 counterpart |
|---|---:|---:|---:|
| Bowed Bass | 35 | 19:33.0–19:58.8 | 65 |
| Human Voice1 | 94 | 54:16.3–54:47.5 | 93 |
| Musical Saw | 98 | 56:23.3–57:12.3 | 97 |
| Sine Wave | 99 | 57:12.3–57:48.0 | 99 |

These are longer manually played phrases, not a newly controlled dry MIDI test. A slow continuous pitch transition, consistent with Portamento, is observed in the Sine demonstration, and other effect states have not been fully transcribed. Their audio has now been used only to inspect a candidate frozen from the earlier PSS-780 recording, as described below. It did not choose the candidate rate/depth values. Preserve the full decoded source and transcribe notes/gates/effects before attempting a full-synth comparison.

Both the target-voice stream-copy excerpts contain approximately10 s of keyframe preroll. Its filename's requested53:00 start is **not** its time origin. Cross-correlation against the separately acquired full audio gives3170.020 s for excerpt sample0. The separate Bowed Bass excerpt starts at original1160.020 s. Use the full original audio for sample-accurate analysis; `kk49-offset.json`, `kk49-program-windows.json`, and `kk49-bowed-program-window.json` preserve the corrections. An exploratory Sine tail is much slower than the old RR8 prediction, but overlapping notes, portamento and capture effects make it unsuitable for a new calibration constant.

## Independent LFO validation after freezing the candidate

Before inspecting these target pitch curves, `lfo-holdout-preregister.json` froze the proposed5.24 Hz triangle LFO and binary peak-depth table `[0, 3.125, 6.25, 12.5, 25, 50, 100, 200]` cents, which root derived from the earlier PSS-780 recording. No new rate/depth value was adopted from the PSS-580 material.

A narrowband partial is extracted with a zero-phase5th-order Butterworth filter after resampling to8 kHz. Hilbert phase differentiation estimates pitch; a41-sample/order3 Savitzky–Golay filter smooths the derivative, sampled at400 Hz. The candidate comparison keeps rate and peak depth fixed and estimates a constant pitch center and one phase within each passage. Separate free rate/depth fits are descriptive diagnostics.

| PSS-580 passage | Fixed5.24 Hz triangle | Previous6.1 Hz sine | Free triangle diagnostic |
|---|---:|---:|---|
| Saw,2351 Hz partial,57:08.30–57:09.60 | 9.552 cents RMS at100-cent peak | 64.128 cents RMS at40-cent peak | 5.24998 Hz,103.75-cent peak;9.184 cents RMS |
| Human Voice1,1568 Hz partial,54:31.35–54:33.55 | 4.963 cents RMS at12.5-cent peak | 10.753 cents RMS at10-cent peak | 5.24174 Hz,11.97-cent peak;4.954 cents RMS |
| Human Voice1,2094 Hz partial,54:45.00–54:45.60 | 2.689 cents RMS at12.5-cent peak | 5.854 cents RMS at10-cent peak | Initial unmodulated segment confounds shape fit |

Saw's late tail has nearly linear ramps and sharp corners over about6.8 cycles. With freely estimated amplitude/rate, a triangle fits better than a sine (9.184 versus11.724 cents RMS). The first attempted Saw fundamental track is unusable because competing notes produce phase slips; that failed result remains in the JSON. The short first-note third-partial attempt is also retained as a contaminated diagnostic, rather than presented as a successful holdout.

The final Human Voice1 note begins with roughly80 ms of almost constant pitch. A **posthoc**100 ms startup guard, disclosed separately, leaves54:45.10–54:45.60. Its free triangle fit is5.24852 Hz and13.88-cent peak with0.324-cent RMS, versus1.062 cents for a free sine; the unchanged fixed candidate gives0.862 cents versus5.497 cents for the old candidate. This is useful shape evidence, not a preregistered adoption score.

These independent observations support a roughly5.24 Hz triangle LFO strongly. Depth agreement is conditional: the PSS-580 raw voice dump was not recovered, and matching voice names/program lists do not prove its PMS fields equal those in the PSS-780 bank. There is also **no successful strict global-phase holdout** here. Each passage has its own nuisance phase; undocumented edits, onsets and the long gap between programs prevent claiming one continuous global phase has been validated. The frozen protocol and this deviation both remain explicit in the JSON. `lfo-saw-last-high.png`, `lfo-human-held.png` and `lfo-human-final-startup-guard-posthoc.png` show the actual extracted curves.

## Next discriminating capture

A decisive rate fixture needs a pure carrier with a recorded33-byte patch, RKS0, known MIDI velocity and gates, and independently disabled Reverb/Sustain/Chorus/Vibrato. Several D2 and RR values at one pitch, together with a static TL-step sequence, separate instrument rates from compression and gating. Reverb/Sustain should then be toggled individually at a fixed Human Voice1 gate. This would test the unresolved tail without silently replacing its factory RR or copying a TX81Z mechanism.
