# Fixed Reverb envelope-cap experiment — 18 October 2026

This is a **research-only exploratory comparison**. It tests whether a two-stage release hypothesis improves the already reused PSS-780 tour while preserving all regressions and voice-allocation effects. No production DSP, adapter, package, version, preset or UI was changed. Artificial noise remains absent.

The [complete result](reverb-envelope-benchmark-2026-10-18.json) records all 100 score windows, all seven model rows, the extended final Sine99 comparison, frozen sources/protocols, commands, hashes, local auditions and voice pressure.

The cap improves every measured metric on the extended final Sine99 chord: joint-band error falls from12.772365 dB in b11 to12.574526 with release ×3 alone and10.659349 with the cap. That is useful agreement with the observed two-stage tail. Across all100 presets, however, release ×3 plus carrier-trigger cap worsens the band mean from3.173500 to3.233245 dB and causes a3.419387 dB Kazoo regression. The all-decay/cap variant has a better overall mean but barely changes its matched no-cap mean. Nearly every note arrives at full model voice capacity. **The specific tail mechanism gains support; a globally correct production implementation is not established.**

## Calibration and what remains unidentified

The final Sine Wave99 chord in the reused [exact PSS-780 tour](https://www.youtube.com/watch?v=ONfIvtDOog0) supplied calibration evidence: the [fixed-window investigation](exact-sine-release-2026-10-18.md) found a fast early decay around −229 dB/s followed by a much slower tail around −14.5 dB/s. This is **the same recording used for scoring**, not an independent holdout. The −18 dB threshold was suggested by the official TX81Z envelope-Reverb analogy documented in [the earlier evidence review](reverb-release-evidence.md); it was not originally recovered independently from this PSS recording.

The bounded candidate uses the previously proposed threefold release duration, an 18 dB internal envelope threshold and rawRR4 cap. With the current RR/RKS mapping and RKS0, its RR8 slopes are 241.359 dB/s before the threshold and 15.0849 dB/s after it. Those values are predictions of a fixed model, not fitted replacements for the observed slopes. Other rates, exact quantization/divider, trigger domain, reset policy and operator coupling remain unresolved.

The calibration does not establish that a discrete echo or captured-noise layer should be added. This experiment changes only release-envelope decrements.

## Frozen candidates and controls

| Candidate | Base duration law | Reverb trigger |
|---|---|---|
| RR ×3 + carrier trigger | Release only ×3 | Carrier internal EG≥18 dB gates both operators |
| RR ×3 + independent triggers | Release only ×3 | Each operator’s own internal EG≥18 dB |
| D1/D2/RR ×3 + carrier trigger | D1/D2/release ×3 | Carrier internal EG≥18 dB gates both operators |

A global research-only `Controls::researchReverbEnabled` flag defaults false in the isolated snapshots. The new benchmark fixture enables it from performance time0 to match the observed Reverb-on tour state. It is not a patch byte, undocumented raw flag, shipping parameter or audio echo.

Capping applies only during release. It selects the smaller of the ordinary release decrement and a rawRR4 decrement computed through the unchanged `4*RR+2` transform and each operator’s existing rate-key scaling. Already-slower releases are preserved. The threshold checks absolute internal EG attenuation **before** the current tick, excludes TL/velocity/AM, and applies immediately at note-off if the EG is already below −18 dB. Held attack/decay behavior is unaffected except for the third candidate’s explicitly declared D1/D2 slowdown.

Voice retirement stays at the existing96 dB carrier endpoint. The12-voice oldest-replacement allocator and48-internal-tick stolen-voice fade remain unchanged hypotheses. They are not silently altered to make the new tail behave well.

Freeze SHA256: `9bdc32cb9d95ac1d13a8a050896c5179db0848a2799a01b4b5258391864a0b0a`. All three new source snapshots, the Reverb-on fixture, pressure fixture, original fixture, absolute events and metric source were frozen before new renders or scores. Every candidate’s **Reverb-off full WAV exactly reproduces its corresponding prior ×3 model**, and its read-only pressure render exactly reproduces its scored Reverb-on WAV.

The four preserved comparison models are selected b11, D1/D2/RR ×3 without Reverb, the same plus slower attack, and RR-only ×3 without Reverb. Their source/audio/report hashes were verified; their completed metrics are reused rather than refitted. See [the prior fixed-law report](envelope-law-benchmark-2026-10-18.md).

All models share the original full absolute 8,931,705-frame sequence, 3,658 events,1,779 note-ons,12 voices,48 kHz,32-frame declared latency trim, frozen Recorded chorus and negative32/48000s chorus epoch. Factory bytes and Vibrato/Sustain flags,5.24 Hz global triangle LFO and host-rate analog stage remain unchanged. Gain is1; tone, drive, DC blocker and limiter are disabled. No per-preset parameter, timing, pitch or phase fit is performed.

The unchanged metric uses one RMS gain per stereo pair,64 logarithmic bands over80–14,000 Hz and STFT512/2048/8192. This removes absolute gain evidence. All100 preset windows were already observed during development.

## All100 results

Lower is better.

| Model | Joint band, dB | Mid band, dB | STFT convergence | Log-STFT, dB |
|---|---:|---:|---:|---:|
| Selected b11 | 3.173500 | 2.764010 | 0.553971 | 3.152216 |
| D1/D2/RR ×3, Reverb off | 3.162154 | 2.787294 | 0.516629 | 2.985180 |
| D1/D2/RR ×3 + attack ×5/3, off | 3.217987 | 2.849354 | 0.512643 | 2.981334 |
| RR ×3, Reverb off | 3.216133 | 2.791751 | 0.552685 | 3.068712 |
| RR ×3 + carrier trigger | 3.233245 | 2.823504 | 0.552497 | 3.000973 |
| RR ×3 + independent triggers | 3.234718 | 2.824004 | 0.552513 | 3.004367 |
| D1/D2/RR ×3 + carrier trigger | 3.162954 | 2.798478 | 0.516822 | 2.929907 |

| New candidate vs b11 | Band improve / regress | STFT improve / regress | Log-STFT improve / regress |
|---|---:|---:|---:|
| RR ×3 + carrier trigger | 60 / 40 | 66 / 34 | 94 / 6 |
| RR ×3 + independent triggers | 60 / 40 | 65 / 35 | 94 / 6 |
| D1/D2/RR ×3 + carrier trigger | 52 / 48 | 73 / 27 | 79 / 21 |

Counts use1e−6 tolerance; the JSON retains unchanged counts too. The isolated Reverb comparison holds each candidate’s base timing law fixed:

| New candidate | Matched Reverb-off band mean | Reverb-on band mean | Improve / regress vs off |
|---|---:|---:|---:|
| RR ×3 + carrier trigger | 3.216133 | 3.233245 | 53 / 44 |
| RR ×3 + independent triggers | 3.216133 | 3.234718 | 53 / 44 |
| D1/D2/RR ×3 + carrier trigger | 3.162154 | 3.162954 | 58 / 39 |

Largest joint-band regressions against selected b11 remain visible:

| Candidate | Preset | Added error, dB |
|---|---|---:|
| RR ×3 + carrier trigger | 47 Kazoo | +3.419387 |
| RR ×3 + carrier trigger | 83 Hand Bell | +3.103856 |
| RR ×3 + carrier trigger | 70 Sitar | +2.505068 |
| RR ×3 + carrier trigger | 72 Jamisen | +1.803391 |
| RR ×3 + carrier trigger | 86 Steel Drum 1 | +1.365981 |
| RR ×3 + independent triggers | 47 Kazoo | +3.419514 |
| RR ×3 + independent triggers | 83 Hand Bell | +3.103856 |
| RR ×3 + independent triggers | 70 Sitar | +2.505068 |
| RR ×3 + independent triggers | 72 Jamisen | +1.803391 |
| RR ×3 + independent triggers | 86 Steel Drum 1 | +1.365981 |
| D1/D2/RR ×3 + carrier trigger | 83 Hand Bell | +3.646131 |
| D1/D2/RR ×3 + carrier trigger | 47 Kazoo | +3.425246 |
| D1/D2/RR ×3 + carrier trigger | 70 Sitar | +2.551276 |
| D1/D2/RR ×3 + carrier trigger | 72 Jamisen | +1.950121 |
| D1/D2/RR ×3 + carrier trigger | 40 Panflute | +1.533753 |

## Three focus voices

Joint stereo band error:

| Model | Bowed Bass65 | Human Voice1 93 | Musical Saw97 | Target mean |
|---|---:|---:|---:|---:|
| Selected b11 | 5.074640 | 5.259832 | 3.194993 | 4.509822 |
| D1/D2/RR ×3, Reverb off | 3.656395 | 5.139574 | 2.138080 | 3.644683 |
| D1/D2/RR ×3 + attack ×5/3, off | 3.831976 | 4.844306 | 2.042045 | 3.572776 |
| RR ×3, Reverb off | 3.174110 | 5.167125 | 2.138073 | 3.493103 |
| RR ×3 + carrier trigger | 2.952059 | 5.103087 | 2.138163 | 3.397770 |
| RR ×3 + independent triggers | 2.952773 | 5.103087 | 2.138163 | 3.398008 |
| D1/D2/RR ×3 + carrier trigger | 3.575584 | 5.090533 | 2.154777 | 3.606965 |

These target windows do not identify operator-trigger coupling. Bowed Bass has modRR4/carrierRR6; Human Voice1 has modRR3/carrierRR7; Musical Saw’s enabled Sustain uses modSRR1/carrierSRR4. Their audible modulator releases are already at or slower than the raw4 cap. Sine99 has a muted modulator. Independent and carrier triggers therefore cannot be separated by these patches’ own capped-release paths. Any target-window differences in the full sequence may come from earlier presets’ tails and allocation history.

A smaller preset-window error does not by itself prove that Human Voice1’s gate-off tail is correct. All metric families and history effects must remain visible; no isolated exact-device Reverb-off/on pair was recovered here.

## Extended final Sine99 chord

The interval was fixed before candidate scoring: frames8723419–8816591, or 181.737895833–183.678979167s. It starts at the last inferred chord onset and ends1.5s after the final note-off. It includes MIDI75/79/87/39 and captures much more release than the original short preset window.

| Model | Joint band, dB | Mid band, dB | STFT convergence | Log-STFT, dB |
|---|---:|---:|---:|---:|
| Selected b11 | 12.772365 | 12.876311 | 0.462936 | 2.312000 |
| D1/D2/RR ×3, Reverb off | 12.574526 | 12.652171 | 0.389978 | 2.037889 |
| D1/D2/RR ×3 + attack ×5/3, off | 12.574526 | 12.652171 | 0.389978 | 2.037889 |
| RR ×3, Reverb off | 12.574526 | 12.652171 | 0.389978 | 2.037889 |
| RR ×3 + carrier trigger | 10.659349 | 10.589754 | 0.359385 | 1.393543 |
| RR ×3 + independent triggers | 10.659349 | 10.589754 | 0.359385 | 1.393543 |
| D1/D2/RR ×3 + carrier trigger | 10.659349 | 10.589754 | 0.359385 | 1.393543 |

This whole-stereo comparison is separate from the root’s fixed-window lock-in analysis. The latter uses gate-relative pre[−0.10,−0.03], early[0.05,0.12], transition[0.12,0.20], late[0.20,0.35] and later[0.35,0.50]s windows with12/20/30ms Hann widths; MIDI79 is the cleanest line because75→87 is an octave/harmonic pair. No fitted frequency, threshold, rate or per-window gain was added by this benchmark. The chord remains polyphonic with chorus, uncertain exact gate delivery and unknown recording dynamics.

## Allocation and limits

| Model | Oldest replacements /1,779 ons | Bowed Bass | Human Voice1 | Musical Saw |
|---|---:|---:|---:|---:|
| Selected b11 | 251 | 0 | 0 | 5 |
| D1/D2/RR ×3, Reverb off | 855 | 17 | 3 | 17 |
| D1/D2/RR ×3 + attack ×5/3, off | 855 | 17 | 3 | 17 |
| RR ×3, Reverb off | 814 | 17 | 3 | 13 |
| RR ×3 + carrier trigger | 1759 | 17 | 18 | 17 |
| RR ×3 + independent triggers | 1759 | 17 | 18 | 17 |
| D1/D2/RR ×3 + carrier trigger | 1767 | 17 | 18 | 17 |

A slow raw4 cap plus the unchanged96 dB endpoint keeps release voices active for several seconds. Nearly every new note can then arrive at the12-voice limit. The pressure fixture merely reads model state and reproduces audio exactly; it does not observe the hardware allocator. Score changes may therefore reflect different overlapping notes, prior-program tails and voice stealing. A two-slope measured tail can be real while this endpoint/allocation/effect combination remains wrong.

Unresolved dimensions include dry base timing, otherRR/RKS/pitch settings, absolute versus note-off-relative threshold, per-operator coupling, effect-toggle/reset policy, Sustain interaction, true endpoint and allocation rules. No threshold/cap/endpoint search was performed to rescue regressions.

## Auditions and reproduction

Local artifacts are under `build/envelope-reverb-benchmark-20261018/`. Four contexts are exported:65,93,97 and`99-final`. Each combined`*-eight-way.wav` orders **hardware → selected b11 → D1/D2/RR ×3 off → plus slower attack off → RR ×3 off → RR ×3 carrier trigger → RR ×3 independent triggers → D1/D2/RR ×3 carrier trigger**.

Each model receives one stereo-pair RMS gain and one common safety gain is then applied per context. All36 files were read back, hash checked, finite and peak≤0.85. The local`audition.html` player page references those files; no live-browser or listening-study validation is claimed. Source-derived audio stays ignored and is not distributed.

The result JSON records native compile/render commands, executable/source/audio hashes and the preserved off/on contracts. The frozen protocol and complete snapshots make the experiment reproducible; the run script refuses to overwrite a completed result. Keep this directory immutable and use a fresh unique artifact directory for follow-up work.

**Production remains selected b11.** These exploratory results justify more separated hardware measurements and model work, not a bit-exact, market-superiority or percentage-authenticity claim.
