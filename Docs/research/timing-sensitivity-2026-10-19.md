# Timing × release/Reverb sensitivity — 19 October 2026

This bounded research experiment compares exactly **four frozen event maps × three fixed DSP states** against the same reused [PSS-780 tour](https://www.youtube.com/watch?v=ONfIvtDOog0). It asks whether previous release/Reverb conclusions depend on uncertain event timing. It does not select an alignment from spectral error or establish physical MIDI delivery times. Production remains b11, with artificial noise absent.

The [held-out timing audit](global-event-mapping-2026-10-19.md) rejected all three corrected maps under its frozen adoption criteria. They remain labeled sensitivity scenarios. Leaving the old map in place also does not prove it is accurate. The [complete JSON](timing-sensitivity-2026-10-19.json) retains all 12 outcomes, all 100 preset rows and every model/mapping contrast and regression.

## Frozen conditions and event assumptions

The protocol was written before any new scenario render or score. Its SHA256 is `78042da65eafae20be2a381d6d8b93379e7f111d9911d0ed1040d918c911cfca`. The three existing model snapshots, fixtures, factory bytes, recording, source events, timeline, v4 windows, unchanged metric, previous reports and previous full-render hashes were verified and frozen.

For `mapped_seconds = a + b * source_MIDI_seconds`:

| Scenario | a, seconds | b |
|---|---:|---:|
| Unchanged |0.8906462238832541|0.9998070138348876|
| Old scale + median offset |0.9327535031570672|0.9998070138348876|
| Nominal scale + median intercept |0.9129181334157996|1.0|
| Equal-patch robust affine |0.9158456466155656|0.9999670078976708|

Every scenario maps **all 100 inferred program commands and 1779 note-on/gate pairs consistently**. Program frames come from `round(48000 * (a + b * timeline.midi_start_seconds))`; corrected maps do not reuse the old timeline's audio-time field. The two-quarter-note program-bar inference remains an assumption. No actual sender program-command log has been recovered.

Onset frames are `round(48000*(a+b*source_start))`. Gate duration is separately `round(48000*b*source_gate)`, and note-off is onset frame plus this duration. This preserves the established benchmark exactly; rounding a transformed absolute end can differ by one sample. Events order program commands, old note-offs and new note-ons at each frame, preserving source-file order within each category. Program changes preserve already active voices and their prior patch/envelope state.

| Model | Release law | Research Reverb state |
|---|---|---|
| b11 | Existing release duration | Off; no cap |
| RR-only ×3 | Release duration ×3; held D1/D2/attack unchanged | Off; no cap |
| RR-only ×3 + carrier-trigger cap | Same release duration ×3 | On from performance time 0; carrier internal EG ≥18 dB triggers both operators' raw RR4 cap |

These are exact prior frozen sources from the [release-law](envelope-law-benchmark-2026-10-18.md) and [Reverb-cap](reverb-envelope-benchmark-2026-10-18.md) experiments. No additional rate, threshold, waveform or patch optimization is introduced. The Reverb hypothesis affects release EG decrements only; it adds no echo, noise or captured audio. Absolute internal attenuation excludes TL, velocity and AM. Existing slower releases remain slower than the cap. This is a sibling-informed and reused-recording-calibrated hypothesis, not a recovered exact PSS-780 law.

All 12 renders use 48 kHz, 12 voices, the same full 8,931,705-frame sequence, 100 unchanged raw factory patches, the frozen Recorded chorus and 32-frame latency trim. Chorus epoch stays at −32/48000 s in audio time; it is not refitted or moved with events. The global 5.24 Hz triangle FM LFO starts at time 0. A timing shift consequently changes LFO/effect phase at note arrival as part of this scenario, without phase fitting. Host-rate analog output, 96 dB voice retirement, oldest replacement and 48-tick stolen fade remain fixed existing hypotheses.

Master gain is 1; tone, drive, DC blocker, limiter and all additive noise are disabled. The same100 **absolute recording-time v4 score windows** are used in every combination. No window moves with the scenario. The frozen metric uses one stereo-pair RMS normalization, 64 bands over80–14,000Hz and STFT 512/2048/8192. It performs no local timing, per-note phase, pitch or parameter fitting. RMS matching discards absolute gain evidence.

## Results across all 100 presets

Lower is better. All 12 outcomes remain visible. None is used to choose a timing map.

| Mapping | Model | Joint band, dB | Mid band, dB | STFT convergence | Log-STFT, dB |
|---|---|---:|---:|---:|---:|
| Unchanged | b11 | 3.173500 | 2.764010 | 0.553971 | 3.152216 |
| Unchanged | RR ×3 | 3.216133 | 2.791751 | 0.552685 | 3.068712 |
| Unchanged | RR ×3 + Reverb | 3.233245 | 2.823504 | 0.552497 | 3.000973 |
| Old scale + offset | b11 | 2.925535 | 2.518936 | 0.473860 | 2.890445 |
| Old scale + offset | RR ×3 | 3.022330 | 2.607004 | 0.491555 | 2.839286 |
| Old scale + offset | RR ×3 + Reverb | 3.095914 | 2.699609 | 0.492272 | 2.779493 |
| Nominal scale | b11 | 2.913863 | 2.505247 | 0.475033 | 2.893887 |
| Nominal scale | RR ×3 | 3.022311 | 2.607579 | 0.492085 | 2.834401 |
| Nominal scale | RR ×3 + Reverb | 3.094309 | 2.697791 | 0.492839 | 2.773615 |
| Robust affine | b11 | 2.915858 | 2.507482 | 0.474463 | 2.889925 |
| Robust affine | RR ×3 | 3.019881 | 2.605312 | 0.491415 | 2.830617 |
| Robust affine | RR ×3 + Reverb | 3.091868 | 2.695405 | 0.492109 | 2.769490 |

The joint- and mid-band ordering is stable across these four scenarios: **b11, then RR ×3, then RR ×3 plus Reverb**. The three corrected scenarios lower the absolute mean error for all three models, but that spectral result does not override their failed held-out timing tests. Release ×3 adds 0.042633 dB joint-band error against b11 under the old map; the added error becomes 0.096796–0.108448 dB under the corrected scenarios. Adding the Reverb cap to the matched RR ×3 model costs 0.017112 dB under the old map and 0.071987–0.073584 dB in the corrected scenarios.

**STFT-convergence ordering reverses.** The old map weakly favors Reverb over RR ×3 over b11, whereas each corrected scenario favors b11 over RR ×3 over Reverb. The log-STFT metric favors Reverb over RR ×3 over b11 throughout. A single metric or average cannot identify the hardware envelope.

| Mapping | RR ×3 vs b11: improve / regress | Reverb vs b11: improve / regress | Reverb vs RR ×3: improve / regress / same |
|---|---:|---:|---:|
| Unchanged | 58 / 42 | 60 / 40 | 53 / 44 / 3 |
| Old scale + offset | 48 / 52 | 46 / 54 | 52 / 45 / 3 |
| Nominal scale | 46 / 54 | 46 / 54 | 53 / 44 / 3 |
| Robust affine | 48 / 52 | 46 / 54 | 53 / 44 / 3 |

Counts use a 1e−6 dB tolerance. Corrected scenarios expose substantial regressions: Reverb adds 3.76–3.80 dB error on Kazoo 47, while RR ×3 adds 3.64–3.69 dB on Hand Bell 83. Their old-map regressions were already 3.419387 and 3.107068 dB respectively. Every per-patch delta remains in the JSON.

## Focus voices and ranking stability

| Mapping | Model | Bowed Bass 65 | Human Voice 1 93 | Musical Saw 97 | Target mean |
|---|---|---:|---:|---:|---:|
| Unchanged | b11 | 5.074640 | 5.259832 | 3.194993 | 4.509822 |
| Unchanged | RR ×3 | 3.174110 | 5.167125 | 2.138073 | 3.493103 |
| Unchanged | RR ×3 + Reverb | 2.952059 | 5.103087 | 2.138163 | 3.397770 |
| Old scale + offset | b11 | 4.430285 | 3.047601 | 3.014010 | 3.497299 |
| Old scale + offset | RR ×3 | 3.173022 | 3.153277 | 2.257568 | 2.861289 |
| Old scale + offset | RR ×3 + Reverb | 3.002984 | 3.108246 | 2.257532 | 2.789587 |
| Nominal scale | b11 | 4.399180 | 2.872304 | 2.858313 | 3.376599 |
| Nominal scale | RR ×3 | 3.171003 | 3.043378 | 2.105312 | 2.773231 |
| Nominal scale | RR ×3 + Reverb | 2.997158 | 2.969520 | 2.105325 | 2.690668 |
| Robust affine | b11 | 4.410611 | 2.838638 | 2.963845 | 3.404365 |
| Robust affine | RR ×3 | 3.167603 | 3.000579 | 2.230526 | 2.799569 |
| Robust affine | RR ×3 + Reverb | 2.989792 | 2.939324 | 2.230497 | 2.719871 |

**Human Voice 1 reverses its joint-band conclusion.** Under the old map, slower release and the cap each improve against b11. Under every corrected scenario, b11 has the lower error. For example, the nominal scenario yields 2.872304 dB for b11, 3.043378 for RR ×3 and 2.969520 for Reverb. This does not prove the original short release is correct; it shows that its apparent spectral improvement from slowing release is not robust to these fixed timing assumptions.

Bowed Bass and Musical Saw retain their band-error improvement from RR ×3 in all four scenarios, and the three-target mean continues to favor the Reverb candidate. Their target STFT-convergence mean nevertheless changes ordering: old-map RR ×3 / Reverb / b11 is 0.596981 / 0.597495 / 0.622233, while all three corrected scenarios favor b11 over RR ×3 over Reverb. The target average cannot be substituted for Human Voice 1’s actual release-tail measurement.

## Timing × model interaction

For each patch and metric, interaction is `(candidate − comparator) under scenario − (candidate − comparator) under unchanged map`. A strict ranking reversal requires opposite signs and both contrasts exceeding the 1e−6 tolerance. The following counts refer to joint-band error against the unchanged map; the complete JSON retains every interaction and all metric families.

| Corrected scenario | RR ×3 vs b11: strict patch reversals | Reverb vs b11 | Reverb vs RR ×3 |
|---|---:|---:|---:|
| Old scale + offset | 26 | 16 | 17 |
| Nominal scale | 22 | 16 | 16 |
| Robust affine | 22 | 16 | 16 |

There are 22–26 per-patch RR ×3/b11 reversals despite the stable all-100 band ordering. This is material timing interaction. Some reversals can involve small individual contrasts; the complete old/new deltas are retained instead of treating the count as an effect-size measure. The stable aggregate band ordering and unstable convergence/individual results both remain evidence. No production model change is justified by this experiment.

## Interpretation limits

These windows and the original recording have been reused during development. The four timing maps were frozen without these new spectral scores, but the model family and target patches were already examined; this is not a fresh hardware holdout. The map audit measures audible transitions with capture and synthesis latency included. Its offset/scale coefficients are not measured oscillator errors.

Jointly moving program commands, note onsets and gate durations can change carried-over patches, phase and voice allocation. This experiment does not isolate those dimensions or show which one explains a regression. No physical allocator, delivered key-off timestamp or simultaneous dry/Reverb hardware pair was recovered. A stable model ordering would support only robustness to these four scenarios, not uniqueness or hardware authenticity; an ordering reversal exposes uncertainty rather than choosing a convenient map.

## Verification and reproduction

The unchanged-map 3,658-event file is byte-identical to both prior experiments. Each of its three fresh full WAVs matches the corresponding previous WAV hash exactly; all 100 metrics also match within 1e−12. A separate verifier parses all mapped event files, checks every program command/onset/gate and independently recomputes all aggregate means, per-patch model contrasts and interaction reversal counts. All 12 full renders are finite with 32-frame declared latency.

Artifacts stay under ignored `build/timing-sensitivity-20261019/`. Source-derived recordings and demos remain local and are not shipped. The local `audition.html` provides the three focus voices for every map, in **hardware → b11 → RR-only ×3 → RR-only ×3 with Reverb** order. Listening files use one gain per stereo pair and one common peak-safety gain across all 12 candidates for each voice. Readback validates hashes, finite samples and peak ≤0.85; no live-browser or listening-study validation is claimed.

`Tools/envelope_timing_sensitivity.py` freezes a fresh directory, verifies original input hashes, compiles only copied research snapshots and refuses to overwrite a started experiment:

```sh
python3 Tools/envelope_timing_sensitivity.py freeze \
  --reference-root /path/to/original/pss780-experiment \
  --output build/timing-sensitivity-new-run
python3 Tools/envelope_timing_sensitivity.py run \
  --output build/timing-sensitivity-new-run
```

Use `--prior-law` and `--prior-reverb` for the preserved prior snapshot directories if they are stored elsewhere. The tool downloads nothing and does not edit production, native adapter, UI, presets, version, package or host state. No mapping or DSP is adopted from this comparison.
