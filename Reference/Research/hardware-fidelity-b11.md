# b11 hardware comparison and selected synthesis model

The selected engine keeps the D1 endpoint correction and the recording-supported **5.24 Hz triangle/global LFO with binary PMS depth**, while retaining the existing analog stage. The proposed fourfold analog integration was **rejected as an instrument default**: it improves the numerical integration of a related-model circuit surrogate but worsens most scores against the actual PSS-780 recording. It remains an independent component research model and tool, unused by the selected instrument engine.

The [complete result](../../Tests/results/hardware-fidelity-b11.json) records all 100 per-preset metric rows, model/source/executable/audio hashes, declared latencies, decision, regressions and local audition paths. The combined experiment is preserved unchanged under `build/hardware-benchmarks/fidelity-b11-20261018T191954Z`; no result was removed after the regression appeared. This is descriptive reuse of the old [PSS-780 tour recording](https://www.youtube.com/watch?v=ONfIvtDOog0), not an independent hardware holdout or a claim of complete OPU identification.

## Compared models

| Model | FM modulation | Analog calculation | Declared latency at 48 kHz | Disposition |
|---|---|---|---:|---|
| D1/old LFO | 6.1 Hz sine, per-note phase, previous PMS table | Existing48 kHz PSS-480 surrogate | 32 frames | Controlled pre-LFO baseline |
| LFO-only | 5.24 Hz triangle, continuous global phase, PMS `[0,3.125,6.25,12.5,25,50,100,200]` cents | Existing48 kHz surrogate | 32 frames | **Selected instrument behavior** |
| Combined experiment | Same new FM modulation | Same surrogate integrated at192 kHz, causal halfband up/downsampling | 112 frames | Rejected default; component research only |

All three retain the D1 correction, existing10 ms/raw-VDT delay law, factory vibrato/sustain flags and existing Recorded chorus. The LFO depth table is an empirical hypothesis supported at the inspected PMS3/PMS6 levels; the other levels are not all identified. The [pitch audit](lfo-pitch-audit-20261018.md) supplies that evidence and its uncertainty. No additive noise is generated.

The final selected production source was independently snapshotted, compiled and rendered after the analog rollback. Its entire **8,931,705-frame WAV is byte-identical** to the already-scored LFO-only render, SHA256 `b8ddf10584fb3f734fa9779658f9cddb939d4fb1b15e67a8f7e6683793f94c28`. Thus the selected scores and auditions apply to the actual final source, rather than merely to a similar prototype. Selected `Press78Engine.cpp` SHA256 is `76c9f2bff45743c1c26ba7cf30efd208814290a6ad8292b203e17bd442cd23e4`; header SHA256 is `ddab76c7e5f548c15bee1cfa115f903fdcd49e71611a302e29bad52dc4d1b6c7`. The source differs from the earlier LFO-only candidate only in comments and the nonfinite-rate sanitizer fallback, neither exercised by the valid fixture inputs.

## Fixed protocol

The unchanged `Tools/HardwareSequence.cpp` replays the full absolute performance from time 0, including all prior program changes, notes and release tails. It uses the existing inferred affine MIDI alignment and exact100 original v4 score windows. At equal frames, programs precede prior note-offs and new note-ons. Programs affect future voices. Both arrangement channels use the selected program and retain separate note-off identities.

The fixture runs48 kHz with12 voices, gain 1, tone/drive/DC blocking/limiter disabled, circuit enabled and full Recorded chorus at the previously frozen capture rate/depth. D1/old LFO resets FM LFO phase per note; the two new-LFO variants use unfitted continuous global phase 0 at performance time 0. There is no local onset, phase, pitch, rate, per-preset envelope or harmonic fit. In particular, this run does not apply the Voice93 pitch-fit phase to the entire recording.

Only declared nominal latency is removed:32 frames for the selected/baseline engines and112 frames for the rejected experiment. The existing Recorded-chorus fixture sets its epoch to negative declared latency/sample rate before rendering, preserving the capture-time chorus origin after the trim. The80-frame FIR delay is therefore accounted for explicitly, not absorbed into a fitted offset.

The established metric removes channel means and applies one RMS gain to each stereo pair. It compares64 logarithmic bands over80–14,000 Hz and STFT sizes 512/2048/8192. Listening exports similarly use one RMS gain per stereo pair and one common safety gain. There is no independent left/right normalization. Level matching removes absolute gain evidence. All 100 rows were already observed during earlier development and must not be called fresh holdout results.

## Selected result: substantial Saw improvement, remaining mixed errors

Joint stereo band error, lower is better:

| Voice/group | D1/old LFO | Selected LFO-only | Rejected combined experiment |
|---|---:|---:|---:|
| 65 Bowed Bass | 5.140637 dB | 5.074640 dB | 5.201937 dB |
| 93 Human Voice1 | 5.256885 dB | 5.259832 dB | 5.259390 dB |
| 97 Musical Saw | 4.932207 dB | **3.194993 dB** | 3.215778 dB |
| Three-target mean | 5.109910 dB | **4.509822 dB** | 4.559035 dB |
| Six immediate neighbors | 3.622499 dB | 3.566080 dB | 3.700502 dB |
| All 100 mean | 3.202288 dB | **3.173500 dB** | 3.258092 dB |

Against the D1-controlled baseline, selected joint-band error improves on 27 presets, worsens on 14 and is unchanged on 59 within1e−6 dB. The largest selected regressions are57 Tremolo Guitar +0.050885 dB,45 Harmonica +0.036845 dB and38 Piccolo +0.016564 dB. Human Voice1's +0.002947 dB is a small regression, not an improvement hidden by the target mean.

| Selected three-target mean metric | D1/old LFO | Selected LFO-only |
|---|---:|---:|
| Midpoint band error | 4.993442 dB | 4.374452 dB |
| STFT convergence | **0.598653** | 0.622233 |
| Log-STFT error | 3.642891 dB | **3.588453 dB** |

The new modulation produces a large Saw spectral improvement and more credible measured pitch behavior. It does not improve every metric. STFT convergence worsens on the three-target mean, even though joint-band, midpoint and log-STFT errors improve. The still-unmatched Human Voice1 release/performance effect remains a separate problem; this change does not claim to solve it.

## Why the fourfold analog integration was rejected

The isolated analog comparison holds the new FM engine and Recorded chorus fixed and compares the selected LFO-only source with the combined experiment. No new recording calibration is involved.

| All 100 isolated analog result | Existing analog | Fourfold analog |
|---|---:|---:|
| Joint-band mean | **3.173500 dB** | 3.258092 dB |
| Midpoint-band mean | **2.764010 dB** | 2.849235 dB |
| STFT convergence mean | **0.553971** | 0.554066 |
| Log-STFT mean | **3.152216 dB** | 3.260923 dB |

Joint-band error worsens on 75/100 presets and improves on 25. This is not only tiny numerical changes:57 presets worsen by more than0.01 dB,37 by more than0.05 dB and29 by more than0.1 dB. Median worsening is 0.017179 dB and mean worsening0.084592 dB. Log-STFT error worsens on 80/100, with50 exceeding0.01 dB.

| Largest isolated analog joint-band regressions | Added error |
|---|---:|
| 16 Harpsichord2 | +0.532052 dB |
| 33 Tenor Sax | +0.462637 dB |
| 44 Bagpipe | +0.450925 dB |
| 66 Banjo | +0.424402 dB |
| 17 Funky Clavi | +0.377196 dB |

There are counterexamples:25 Electric Trumpet improves0.173865 dB,78 Synth Brass0.092761 dB and22 Trumpet0.041617 dB. They do not outweigh the broad regression for the selected instrument default. Harpsichord2's isolated log-STFT regression is 2.953097 dB and remains visible in the full result.

This does not invalidate the independent circuit-response/integration tests. Those tests establish a better numerical approximation of the same PSS-480 volume-pot-top surrogate. They cannot prove that this surrogate is the correct PSS-780 output path or compensate for unknown FM/envelope/capture behavior. The actual target-recording comparison therefore takes priority for the instrument decision. The failed variant, full source, executable, protocol, metrics and audio remain preserved for further diagnosis.

## Auditions and verification

Local files for65/93/97 are under `build/hardware-benchmarks/fidelity-b11-20261018T191954Z/focused-ab`:

- `NN-selected-three-way.wav`: hardware → D1/old LFO → **selected final sound**.
- `NN-four-way.wav`: hardware → D1/old LFO → selected final sound → rejected fourfold analog experiment.
- Individual reference and model clips are retained alongside them.

All 18 focused files have been read back, SHA256 checked, and verified finite with peak≤0.85. Their exact one-pair gains, common safety gains, timing and playback orders are recorded in the JSON. The full continuous native WAVs are finite float audio and may exceed1 because the benchmark intentionally bypasses the limiter; the audition exports are unclipped. No captured-noise bed or artificial noise is added. These reference-derived WAVs stay ignored/local because no source redistribution license was found.

The source recording, events, all 100 windows, source snapshots, native executable hashes, continuous WAV hashes and inherited audition hashes were checked. The new selected-source full-render identity separately verifies that the retained LFO-only scores apply after rollback. Raw-core parity was not rendered in this recorded-only run. The independent observed-mid-to-side Recorded transfer is unchanged; its target mean NRMSE remains0.403529 and is not evidence of an FM/analog improvement.

Reproduce the rejected combined run using unchanged `Tools/hardware_benchmark.py` with its preserved `source` directory, `--modes recorded --all-presets`, the external experiment root and a **new unique** artifact directory. For the selected model use the preserved `selected-source`; its verification receipt includes the exact compile and render commands. `summarize_fidelity.py` and `finish_decision.py` preserve the derived summary and audition procedure in the ignored artifact directory. The original completed run must not be overwritten.

Remaining uncertainties include the exact PSS-780 analog circuit/DAC, unobserved PMS depths, reset/delay law, oscillator arithmetic, release/performance state and capture processing. No percentage of hardware authenticity, bit-exact emulation or market-superiority conclusion follows from these reused recording scores.

Generate the local audio-player page with `python3 Tools/build_fidelity_report.py`. It verifies the selected clips against their frozen hashes and finite/unclipped receipt, then writes `audition.html` beside the benchmark artifacts. The page labels every comparison and retains the mixed metrics; it is not a live-browser or listening-study validation.
