# Fixed envelope timing hypotheses against the PSS-780 tour

**Keep the selected b11 engine for now.** Slower envelope candidates improve several target and time-frequency scores, but a blanket scalar timing change causes substantial regressions and sharply increases voice replacement. These results narrow the next hardware measurement; they do not identify the OPU envelope law.

The [complete result](envelope-law-benchmark-20261018.json) preserves every metric for all 100 presets, all source/executable/render hashes, fixed protocols, candidate deltas, voice pressure and local auditions. No production DSP, native adapter, package, version or artwork was changed in this experiment. No additive noise was introduced.

## Basis and fixed candidates

The prior [independent recording audit](recording-holdout-audit-20261018.md) measured a visible pure-carrier PSS-480 edit sequence in [Keen On Keys’ demonstration](https://www.youtube.com/watch?v=2TfpcAmaPGg). D2R20 decays at approximately −21.24 dB/s versus the existing −64 dB/s law; two RR8 releases are approximately −230 to −233 dB/s versus −724.08 dB/s. The observed AR41 attack is roughly 5/3 as long as the current curve. This is sibling evidence with unknown recording dynamics, global Reverb and gating; a compressor could also reduce dB slopes. It does not identify the PSS-780 clock, envelope range or slope constants.

Before rendering or scoring, four source snapshots were frozen at public commit `5b59007c0623bef16d572e94496d02595e530a88`:

| Candidate | D1/D2 duration | Release duration | Attack duration |
|---|---:|---:|---:|
| Selected b11 | 1× | 1× | 1× |
| D1/D2/RR ×3 | 3× | 3× | 1× |
| D1/D2/RR ×3; attack ×5/3 | 3× | 3× | 5/3× |
| RR only ×3 | 1× | 3× | 1× |

Only the declared scalar constants in `Envelope::configure` change. Decay/release factor 3 changes the denominator constant 48 to 144; attack factor 5/3 changes 8 to 40/3. The source snapshots were checked to differ only on those lines. No candidate was tuned after observing the PSS-780 scores. Instant attack at effective AR≥63, AR0 silence, rate-key scaling, release-rate remapping, D1 endpoint behavior and the 96 dB endpoint remain unchanged.

Freeze: `build/envelope-law-20261018/protocol-frozen.json`, SHA256 `0d21a630b790e95cd4b75c391e7f5274f08565c7250e406ef4f6eeddbba1e1e3`. The frozen object copied historical b11 parent metadata containing references to its rejected fourfold analog experiment. A preserved clarification explicitly labels those fields as historical: **all four actual candidates here use the unchanged host-rate analog model and 32-frame latency**. The source hashes, commands and render receipts verify this condition.

## Shared recording protocol

The recording is the already reused [PSS-780 preset tour](https://www.youtube.com/watch?v=ONfIvtDOog0). The full 8,931,705-frame absolute performance is rendered from zero, including all 3,658 events, 1,779 note-ons, previous programs and release voices. There are 12 voices; program changes affect future notes. The original inferred affine MIDI alignment and exact 100 v4 score windows are retained. None of these windows is a fresh holdout.

Every candidate runs at 48 kHz with gain 1, circuit enabled, Recorded chorus at its existing frozen rate/depth, factory Vibrato/Sustain flags, and unchanged b11 FM modulation. Tone, drive, DC blocker and limiter are disabled. Only declared 32-frame latency is removed; Recorded chorus epoch is −32/48000 s. There is no local onset, pitch, phase, envelope, harmonic or preset-specific fit.

The unchanged metric removes channel means and applies one gain to each stereo pair. It measures 64 logarithmic spectral bands over 80–14,000 Hz and STFT sizes 512/2048/8192. Pair gain matching discards absolute gain evidence. Short preset windows do not isolate a final gate-off release, and the tour includes hardware effects, uncertain gates and unknown capture processing.

The baseline render is byte-identical to selected b11, SHA256 `b8ddf10584fb3f734fa9779658f9cddb939d4fb1b15e67a8f7e6683793f94c28`; all 100 baseline metric rows also reproduce the selected b11 report within 1e−12.

## Results across all 100 presets

Lower is better for each metric.

| Candidate | Joint stereo band, dB | Mid band, dB | STFT convergence | Log-STFT, dB |
|---|---:|---:|---:|---:|
| Selected b11 | 3.173500 | 2.764010 | 0.553971 | 3.152216 |
| D1/D2/RR ×3 | 3.162154 | 2.787294 | 0.516629 | 2.985180 |
| D1/D2/RR ×3; attack ×5/3 | 3.217987 | 2.849354 | 0.512643 | 2.981334 |
| RR only ×3 | 3.216133 | 2.791751 | 0.552685 | 3.068712 |

| Candidate vs b11 | Band improve / regress | STFT improve / regress | Log-STFT improve / regress |
|---|---:|---:|---:|
| D1/D2/RR ×3 | 49 / 51 | 73 / 27 | 75 / 25 |
| D1/D2/RR ×3; attack ×5/3 | 43 / 57 | 75 / 25 | 73 / 27 |
| RR only ×3 | 58 / 42 | 68 / 32 | 93 / 7 |

Counts use a 1e−6 threshold. None is unchanged within that threshold. D1/D2/RR ×3 improves the joint-band mean by only 0.011346 dB while worsening 51 presets. Its STFT and log-STFT aggregate improvements are more substantial. Adding slower attack further improves those temporal metrics but worsens both band means. RR-only has 93 log-STFT improvements, yet its joint-band mean worsens because a few large failures outweigh many small gains. No single candidate dominates.

Largest joint-band regressions, retained rather than excluded:

| Candidate | Preset | Added band error, dB |
|---|---|---:|
| D1/D2/RR ×3 | 83 Hand Bell | +3.673308 |
| D1/D2/RR ×3 | 70 Sitar | +2.551276 |
| D1/D2/RR ×3 | 40 Panflute | +1.515779 |
| D1/D2/RR ×3 | 72 Jamisen | +1.399933 |
| D1/D2/RR ×3 | 71 Shamisen | +1.376407 |
| D1/D2/RR ×3; attack ×5/3 | 83 Hand Bell | +3.683699 |
| D1/D2/RR ×3; attack ×5/3 | 70 Sitar | +2.571697 |
| D1/D2/RR ×3; attack ×5/3 | 40 Panflute | +1.589374 |
| D1/D2/RR ×3; attack ×5/3 | 71 Shamisen | +1.474715 |
| D1/D2/RR ×3; attack ×5/3 | 72 Jamisen | +1.437993 |
| RR only ×3 | 83 Hand Bell | +3.107068 |
| RR only ×3 | 70 Sitar | +2.505068 |
| RR only ×3 | 86 Steel Drum 1 | +1.364905 |
| RR only ×3 | 82 Chimes | +0.953692 |
| RR only ×3 | 74 Violin 1 | +0.772381 |

The full JSON also preserves large regressions in other metrics, including Harpsichord 2’s +1.457310 dB log-STFT change for D1/D2/RR ×3. A favorable average does not erase these failures.

## Bowed Bass, Human Voice 1 and Musical Saw

Joint stereo band error:

| Voice/group | b11 | D1/D2/RR ×3 | Plus attack ×5/3 | RR only ×3 |
|---|---:|---:|---:|---:|
| 65 Bowed Bass | 5.074640 | 3.656395 | 3.831976 | 3.174110 |
| 93 Human Voice 1 | 5.259832 | 5.139574 | 4.844306 | 5.167125 |
| 97 Musical Saw | 3.194993 | 2.138080 | 2.042045 | 2.138073 |
| Three-target mean | 4.509822 | 3.644683 | 3.572776 | 3.493103 |

The three-target averages improve for every candidate. Human Voice 1 improves modestly with release-only or D1/D2/RR ×3; the slower attack candidate improves its band and STFT convergence scores more. **This does not establish that its release mismatch is fixed.** No new isolated PSS-780 gate-off tail was measured here, and both attack/overlap changes and effects can improve an aggregate preset window.

Bowed Bass illustrates mixed evidence: D1/D2/RR ×3 improves its band error from 5.074640 to 3.656395 dB, while its STFT convergence worsens from 0.511762 to 0.514955. Musical Saw’s band error improves with longer release, while its log-STFT error slightly worsens for the two candidates without slower attack. All metric rows remain visible.

## Voice pressure changes the comparison

A second fixture reads the public `activeVoices()` immediately before each note-on. It logs oldest-voice replacement when the fixed engine’s exact condition is true: an eligible non-silent note and active count ≥12. It does not change engine state. For **every candidate**, this diagnostic’s full rendered WAV is byte-identical to the untouched scored fixture. These are model allocation counts, not observed hardware allocation.

| Candidate | Replacements, full performance | Bowed Bass | Human Voice 1 | Musical Saw |
|---|---:|---:|---:|---:|
| Selected b11 | 251 | 0 | 0 | 5 |
| D1/D2/RR ×3 | 855 | 17 | 3 | 17 |
| D1/D2/RR ×3; attack ×5/3 | 855 | 17 | 3 | 17 |
| RR only ×3 | 814 | 17 | 3 | 13 |

Longer envelope tails increase overlap and oldest-voice replacement. In the longer D1/D2/RR candidates, all 17 Bowed Bass and 17 Musical Saw note-ons arrive at full model capacity. Consequently, a spectral improvement can arise from a different mixture of previous notes and program tails; it is not clean evidence for the physical envelope slope. The hardware voice allocator and release truncation policy require separate identification.

## Reproduction and auditions

Ignored artifacts are preserved under `build/envelope-law-20261018/`: four source snapshots, original and diagnostic fixtures, exact compile/render commands, executable hashes, continuous renders, pressure CSVs, the frozen protocol, metric source, scripts and complete result. Do not overwrite this completed experiment; copy it to a new unique directory and adjust output paths for another run. No source recording or derived media is distributed in the shipping repository.

The local `auditions/NN-five-way.wav` files use this order: **hardware → selected b11 → D1/D2/RR ×3 → plus slower attack → RR only ×3**. Each model receives one RMS gain per stereo pair, followed by one common safety gain. All 18 exports were read back, hash checked, finite and peak≤0.85. The standalone files are retained too; no captured-noise bed or artificial noise was added.

The next useful evidence is controlled direct-output recording with an independently defined pure carrier, explicit note-on/off gates, TL steps to detect capture compression, separate Reverb/Sustain states, rate sweeps and long silences. Measure absolute gate-relative slopes and attack shape before changing the production law. The existing [hardware capture protocol](hardware-capture-protocol-20261018.md) is designed for those controls.

This experiment makes no bit-exact, complete-hardware, market-ranking or percentage-authenticity claim.
