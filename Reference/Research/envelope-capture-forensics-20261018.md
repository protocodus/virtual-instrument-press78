# Envelope capture forensics — 2026-10-18

The recorded fast release is real and repeatable; its cause is not fully identified. A common output compressor or AGC alone does not explain the exact PSS-780 passage where a held sine stays level while another sine releases. The PSS-780 also has a separate, much slower late tail with its physical Reverb indicator on. These findings support investigating the envelope and Reverb behavior separately. They do not recover an OPU timing table or justify applying a universal 3× multiplier.

This pass changes research documents only. It does not change DSP, factory patches, timing alignment, host state, or production constants. The [machine-readable record](envelope-capture-forensics-20261018.json) contains all channel/window results, exact source paths, sizes and SHA-256 hashes. Third-party media and extracted frames remain ignored local analysis artifacts.

## Controlled PSS-480 evidence

The primary source is Keen On Keys' [PSS-480 synth editor demonstration](https://www.youtube.com/watch?v=2TfpcAmaPGg), published in 2021. The uploader describes an editor demonstration; the available description does not establish a recording chain without compression, gating, AGC or effects. Treat that chain as unknown.

The pure-carrier passage around 553–575 seconds visibly has modulator Level 0, carrier ratio 1, sine, AR 41, D1R 0, D2R 20, RR 8, SRR 3 and RKS 0. Carrier Level displays 92. The editor changes D1 Level between 14, which holds, and 15, which decays. Direct positive waveform peaks show the decaying note reaches approximately the same −7.1 dBFS maximum as the neighboring flat notes and then decays. There is no missing initial 18 dB drop in this note.

The panel author's [2022 panel file](https://ctrlr.martintarenskeen.nl/yamaha-pss480-20220225.bpanelz) serializes AR, D1R, D2R and RR directly, D1L as `15 − display`, and TL as `max(99 − display, 0)`. This supports raw D1L 1 versus 0 and carrier TL 7. It is a later panel version, so it corroborates the UI interpretation; it does not reveal the actual SysEx bytes sent in the 2021 recording.

All following times are original full-video seconds. The analysis PCM excerpt starts at exact source 485 seconds. Direct positive local maxima avoid filtering and Hilbert-envelope smearing; the minimum peak separation is 160 frames at 48 kHz. Regressions use dB of each positive peak.

| Case | Fixed source window | Recorded slope | R² |
| --- | --- | ---: | ---: |
| Flat note | 553.25–554.45 s | −0.0139 dB/s | 0.0314 |
| D2R 20 | 564.30–565.30 s | −21.2405 dB/s | 0.99985 |
| D2R 20, alternate interior | 564.60–565.80 s | −21.0890 dB/s | 0.99969 |
| RR 8, first release | 554.55–554.70 s | −233.3526 dB/s | 0.99957 |
| Repeated flat note | 568.95–569.80 s | +0.0431 dB/s | 0.1116 |
| RR 8, repeated release | 569.90–570.03 s | −230.1256 dB/s | 0.99970 |

An independently computed 4096-frame STFT gave D2R 20 slopes around −21.26 dB/s in three nearby one-second windows. The former heuristic DSP predicts 64 dB/s for D2R 20 and approximately 724 dB/s for RR 8/RKS 0. The roughly 3× discrepancy is therefore not a peak-detector artifact. The former formula is not a manufacturer timing specification.

The repeated flat levels and repeated release slopes show stability within this recording. They do not establish its transfer curve. No clean static carrier-TL sweep with otherwise identical patch and known gain was recovered. No second nonzero D2R or RR value was established in an equally isolated, unchanged pure-carrier setting. Other RR demonstrations include modulation, feedback or RKS; the later D1R 63/D2R 63 case demonstrates a very short event rather than another usable slow slope. These examples cannot supply the missing independent timing point.

The known RR 8 examples lose their coherent sine abruptly near 48 dB below their plateau, around −54/−55 dBFS. A hardware endpoint, upstream gate, global effect, or codec behavior can produce an apparent disappearance. This observation does not identify a hardware cutoff. There is no recording-level evidence sufficient to prescribe a noise gate or quantized tail in the instrument.

Three repeated AR 41 attacks fit the previously assumed exponential-in-attenuation attack form with factors 626.6–635.5 s⁻¹ versus the former model's 1051.5 s⁻¹. Only about a dozen cycles inform each fit, and the true attack form and recording dynamics are unknown. This is descriptive evidence, not a recovered attack law. A static compressor above one knee can rescale log-amplitude without changing the exponential time factor, so neither a universal 3× time stretch nor simple fixed 3:1 compression explains all observations under that assumed form. Dynamic processing and the model form remain confounds.

## Exact PSS-780: independent estimator and simultaneous-note control

The original [AndrewsVintageKeyboards PSS-780 recording](https://www.youtube.com/watch?v=ONfIvtDOog0) is reused here. This is independent analysis of the same source, not an independent recording holdout. Program 99 is visibly selected. At source 182.5 seconds the effect column shows Reverb and Chorus on, with Vibrato, Sustain and Portamento off. This identifies the physical panel state, not the external recording chain.

The recovered factory patch has carrier ratio 1, TL 13, RKS 0, AR 63, D1R 1, D2R 0, D1L 0 and RR 8. Its modulator is at minimum level. The carrier also has nonzero raw level-key-scaling byte `0xB9`; no calibrated attenuation is inferred from it here. All MIDI event times use the frozen affine mapping:

```
source seconds = 0.8906462238832541 + 0.9998070138348876 × MIDI seconds
```

These are inferred sender times, not recorded hardware arrivals. The actual audible note changes lag this mapping by tens of milliseconds. No local time shift was fitted in this pass. Event-relative early windows describe the visible waveform branch; they do not measure an exact hardware key-off latency.

The independent estimator simultaneously solves sine/cosine amplitudes for fixed equal-tempered MIDI pitches 39, 46, 58, 59, 67, 75, 79 and 87, plus DC. Both design matrix and audio receive a 20, 40 or 60 ms Hann taper, giving a squared-Hann least-squares objective. Frames advance by 2 ms. Left, right and arithmetic mid are measured separately. No pitch, gain, timing or envelope parameter is optimized against the engine.

The final chord's inferred off is frame 8,744,591 at 48 kHz, or 182.178979167 seconds. With the 40 ms taper on arithmetic mid:

| Partial | Window after inferred off | Recorded slope | R² |
| --- | --- | ---: | ---: |
| MIDI 79 | 50–120 ms | −229.990 dB/s | 0.99948 |
| MIDI 75 | 50–120 ms | −230.753 dB/s | 0.99976 |
| MIDI 79 | 200–350 ms | −13.670 dB/s | 0.94697 |
| MIDI 75 | 200–350 ms | −13.874 dB/s | 0.89395 |

These independently corroborate the early/late branches in the [separate fixed-frequency lock-in audit](exact-sine-release-20261018.md). Shorter and longer tapers and separate channels are retained in JSON. Individual left/right amplitudes exchange substantially with Chorus; individual channel slopes can differ greatly or briefly rise. The arithmetic-mid slopes above describe the combined recorded signal. Chorus, partial interference and short windows make individual late fits less linear; do not interpret their final decimals as chip constants.

A stronger gain control occurs earlier in the same program. MIDI 67 and 75 release at inferred source 180.414625 seconds while new MIDI 58 and 46 begin. The new notes remain held for approximately 220.5 ms. Once the new MIDI 58 settles, its partial can reveal a large common output gain change while the old MIDI 75 releases.

With the 40 ms taper, in the 70–100 ms window, held MIDI 58 varies only 0.378 dB peak-to-peak, with a −0.55 dB/s regression and negligible linear trend. Released MIDI 75 simultaneously falls at −232.55 dB/s, R² 0.99869. In the 140–200 ms window, held MIDI 58 remains near −19.8 dBFS with 0.753 dB peak-to-peak variation while the released MIDI 75 has reached approximately −39.7 dBFS and falls only −10.03 dB/s. The 60 ms taper gives the latter −10.97 dB/s, R² 0.8848. MIDI 67 also slows but is more affected by interference and is not used as a precise late-slope estimate.

Subject to the held source having a constant envelope and the separated partials representing their own voices, a common postmix gain cannot alone turn a much faster release into the observed slow branch: the required gain rise would also lift the held sine. Likewise the held-partial control limits a gain-only explanation of the approximately 233 dB/s fast branch. This argues against treating a shared capture compressor/AGC as the complete explanation. It does not locate the behavior inside the keyboard. Internal key-off shaping, external reverberation, per-band/per-voice processing, or another upstream process remain possible. Actual dry/effect-isolated capture is still needed.

The Reverb indicator being on is evidence that an effect-enabled release should be measured separately from a dry release. It does not establish that the extra tail is implemented by an acoustic-style delay network, an envelope-rate cap, a fixed attenuation threshold, or any particular raw RR substitution.

## Extended PSS-780 tail endpoints

The same independent estimator was extended to original source 185.8 seconds. The source ends at 185.991854 seconds. No new notes follow the final chord. Each measured partial becomes abruptly incoherent at a different time, so these endings are not a single end-of-file edit.

The descriptive departure is the first frame after 1.25 seconds that remains at least 12 dB below an extrapolated earlier late branch for all of the next 80 ms. That branch is fit over 0.30–1.25 seconds after the inferred off. This definition measures a recorded disappearance, not a physical hardware event. With the 40 ms Hann taper on arithmetic mid:

| Partial | Departure after inferred off | Source time | Level 50 ms before departure | Loss relative to pre-release level at that earlier point |
| --- | ---: | ---: | ---: | ---: |
| MIDI 87 | 1.314 s | 183.492979 s | −60.62 dBFS | 38.57 dB |
| MIDI 79 | 1.682 s | 183.860979 s | −61.53 dBFS | 40.41 dB |
| MIDI 75 | 1.736 s | 183.914979 s | −61.63 dBFS | 41.39 dB |
| MIDI 39 | 1.804 s | 183.982979 s | −61.85 dBFS | 38.71 dB |

The final loss spans tens of dB over tens of milliseconds. MIDI 87 can contain MIDI 75's second harmonic, and the short-window bass estimate has fewer cycles; those are diagnostic partials rather than independent voice proofs. Separate channels and tapers show the same broad extinction, but threshold times vary when a channel is weak or cancelling. All 12 arithmetic-mid combinations satisfy the persistent-departure detector; the weak right-channel 20 ms bass estimate does not, so only 35 of 36 combinations yield a qualified departure. For example, MIDI 79's 40 ms left/right descriptive departures are 1.670/1.734 seconds versus 1.682 seconds in mid.

The approximately −61 dBFS cluster is an arithmetic-mid recording measurement, not a calibrated internal attenuation. Recording gain, stereo phase and Chorus all affect it. Nonzero carrier LKS `0xB9` also means that even intrinsic truncation based on total per-voice attenuation would not imply one fixed envelope-generator attenuation. The differing relative losses explicitly do not establish a 48 dB EG cutoff.

A separate [AAC/Opus codec audit](codec-tail-audit-20261018.md) independently reproduced the four endings in YouTube format-140 AAC after a global 627-frame alignment against format-251 Opus. The four relative-50-dB crossing times agree within 0.46 ms. Float-decoded Opus also agrees with the original PCM16 reference. This rules out an Opus-transcode-specific or final-PCM16-only explanation. Both transcodes share the same upload master: earlier shared processing, recording gates and hardware remain possible. Neither audit identifies the location or numerical rule of the extinction.

## PSS-580 independent-source negative comparison

KeyboardKrazy49's [PSS-580 demonstration](https://www.youtube.com/watch?v=NXPbPr4yrgA) is a separate unit and uploader. This is an independent-source negative comparison, not a fresh or strictly unseen holdout: the earlier recording audit had already explored its Sine99 tails and portamento. The new joint-LS endpoint analysis was not used to tune the frozen candidates. Program 99 is visible at approximately source 3464 seconds. Its raw patch, actual gates and physical effect states are not recovered, so a shared voice name or number is not evidence of an equal RR/RKS setting. The initial program-99 demonstration contains a large portamento-like pitch sweep; this pass inspects the late stable chord only.

Audio was decoded from the full source with exact original 3160-second start. The old stream-copy excerpt whose name says `3180` retained preroll and actually begins at 3170.020 seconds; that filename was not used as the numerical audio origin.

A 40 ms joint estimator on the late chord, using inferred pitches 46, 53, 58, 65, 70, 77 and 82, shows these slopes over original source 3464.23–3464.38 seconds:

| Inferred pitch | Recorded slope | R² |
| --- | ---: | ---: |
| MIDI 46 | −199.45 dB/s | 0.99884 |
| MIDI 53 | −200.01 dB/s | 0.99959 |
| MIDI 58 | −199.40 dB/s | 0.99909 |
| MIDI 65 | −230.42 dB/s | 0.99973 |
| MIDI 77 | −220.45 dB/s | 0.99843 |

The coherent partials then disappear sharply near 3464.43 seconds. There is no clear bend after 18–20 dB of attenuation into the approximately 15 dB/s tail observed on the effect-enabled 780; the inspected 580 chord continues falling through roughly 35–40 dB first. This is a bounded negative result. Different patch parameters, physical effect states and capture processing prevent an equal-rate claim or a direct refutation of the 780's slow tail. The unknown actual key-off also prevents timing-law recovery.

## Consequence for the next hardware pass

The evidence supports keeping dry envelope timing and effect-enabled late release as distinct research questions. The approximately 230 dB/s fast branch now has repeatable recorded support, including exact PSS-780 evidence, and the simultaneous held-note control weakens a common-gain-only explanation. One known D2 rate, one RR setting and one AR setting still cannot identify the complete OPU timing function.

The [optional capture protocol](hardware-capture-protocol-20261018.md) provides the missing controls: unprocessed constant-gain line capture, static TL steps, several pure-carrier AR/D2R/RR settings, and separate documented physical Reverb/Sustain states. Until that evidence exists, the 3× rate scale, 18–20 dB late-tail transition and abrupt endpoint remain hypotheses or observations with explicit capture confounds. The AAC check removes two specific codec/quantization explanations while leaving the shared master and hardware unresolved. This report adopts none as production constants.
