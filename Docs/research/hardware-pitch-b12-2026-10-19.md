# b12 Original pitch-law comparison — 19 October 2026

The Original pitch option passes the predeclared compatibility and regression limits. **All four Equal full-performance WAVs are byte-identical to their historical b11 counterparts.** Original preserves the known producer pitch pattern without refitting. Its average recording-band errors improve by less than 0.003 dB, while both STFT metrics worsen slightly on every timing map. This supports a bounded pitch option; it does not demonstrate a broad timbre improvement.

The design was frozen before candidate compilation, rendering or scoring. It uses the four existing [Mode 00 timing maps](mode00-benchmark-2026-10-19.md), exactly 100 unchanged absolute windows, and 1,761 retained notes: 3,622 events including 100 program changes. The 18 out-of-range notes remain excluded. Only `pitchModel` changes. Raw factory parameters, operator detune, internal modulation, envelopes, Recorded chorus, analog output, twelve-voice allocation and the 32-frame delay/chorus epoch correction remain fixed. There is no new tuning, retiming, noise, release or Reverb fit.

## Fixed comparisons

The primary gate permits at most 0.03 dB worsening in the all-100 mean joint stereo band error on each map, plus at most 0.1 dB worsening for **each** focus voice on **each** map. Lower is better; signed deltas below are Original minus Equal. All maps pass.

| Timing map | Equal joint band error, dB | Original, dB | Change, dB | Band-error regressions |
|---|---:|---:|---:|---:|
|unchanged|3.145007|3.143844|-0.001163|50/100|
|old_scale_median_offset|2.893976|2.893221|-0.000755|48/100|
|nominal_scale_median_intercept|2.882409|2.879825|-0.002584|49/100|
|equal_patch_robust_affine|2.884220|2.881928|-0.002292|48/100|

| Timing map | Bowed Bass 65 change, dB | Human Voice 1 93 change, dB | Musical Saw 97 change, dB |
|---|---:|---:|---:|
|unchanged|-0.005792|+0.001406|-0.030678|
|old_scale_median_offset|+0.001170|+0.004078|+0.005851|
|nominal_scale_median_intercept|+0.015578|+0.003999|+0.023689|
|equal_patch_robust_affine|+0.016449|+0.004499|-0.004703|

The largest band regression anywhere is patch 9 on `old_scale_median_offset`: +0.144015 dB. It is outside the focus set, so it does not fail the frozen per-focus gate, but it is retained and disclosed. The greatest focus regression is Musical Saw 97 on the nominal-scale map, +0.023689 dB.

| Timing map | Mean mid-band error change, dB | Mean STFT convergence change | Mean STFT log-error change, dB |
|---|---:|---:|---:|
|unchanged|+0.000207|+0.000366|+0.003046|
|old_scale_median_offset|-0.000384|+0.000082|+0.003067|
|nominal_scale_median_intercept|-0.002791|+0.000271|+0.003390|
|equal_patch_robust_affine|-0.002501|+0.000330|+0.003466|

The complete [JSON report](hardware-pitch-b12-2026-10-19.json) retains all 800 model-window scores, all signed deltas, every regression, full render hashes, peaks and timing metadata. These are reused recording windows, not a new holdout. The three alternative timing maps previously failed their own timing-adoption criteria; their better absolute scores here do not adopt or validate them.

## Pitch and implementation checks

The [recovered firmware command path](opu-pitch-command-path-2026-10-19.md) supplies the FNUM values. The downstream expression `floor(FNUM × 2^(block−3)) × 5,500,000 / (6 × 2^24)` remains a behavioral conversion hypothesis: these results do not identify native phase width, internal divider, envelope clock or exact silicon arithmetic. Extended keyboard/bend behavior outside the verified hardware domain is a plugin extension.

The same 62 previously qualified producer notes retain their **original per-pack nuisance offsets**, with no new fitting. RMS errors are 0.002970 cents for the FFT estimates and 0.002947 cents for phase estimates, below the frozen 0.011-cent limit. Maximum absolute errors are 0.009983 and 0.008508 cents. All 63 source rows, including the excluded row, remain in the report. Their four pitch classes informed the earlier hypothesis; this is consistency on reused evidence, not a fresh validation population. The fitted capture/tuning offsets are not shipped.

A separate compiled command-helper check passed 49,152 converter cases and 147,456 individual writes against the independently reconstructed functional model, which had previously been checked by executing all three identified firmwares. This benchmark does not rerun firmware. The exact helper hash and validation receipt were bound before rendering. The core receipt also reports six release and six sanitizer test targets, a separate 19.66 MB Equal sample-identity check, and native performance workloads with no deadline misses. Those native checks do not establish Reason host or packaged-target performance; wrapper and packaging review remain separate.

## Local audition and reproduction

Twelve three-way auditions cover the focus voices on every timing map in the order **hardware → Equal → Original**. Each model has one RMS gain for its stereo pair; a shared safety gain applies across all maps and models for that focus voice. No channel-wise gain, EQ, phase, pitch or timing fit is applied. Audition peaks are at most 0.9. The unnormalized full float renders deliberately use master gain 1 with no limiter and have peaks about 2.18–2.24; they are finite, not constrained to unit range. Their high peaks are preserved rather than clipped by PCM conversion.

Open ignored `build/pitch-model-b12-20261019/benchmark/audition.html` for the clips. Four Original full WAVs plus the clips occupy about 304.1 MB. Newly rendered Equal files were deleted only after full historical hash equality; earlier artifacts remain untouched. Original media, firmware and render files are not distributed with the research note.

The [runner](../../Tools/benchmark_pitch_model.py) has three separate stages. With the required historical local artifacts available, choose a new ignored output directory and run:

```sh
python3 Tools/benchmark_pitch_model.py freeze --output build/pitch-model-new-run
python3 Tools/benchmark_pitch_model.py bind --output build/pitch-model-new-run
python3 Tools/benchmark_pitch_model.py run --output build/pitch-model-new-run
```

`freeze` records source data, timing maps, windows and gates. `bind` snapshots the final candidate, runner and command-helper receipt before compilation. `run` verifies every hash before generating audio and refuses to overwrite an existing run. Exact reproduction requires the bound source version and command validation receipt; a later source revision is a new candidate.

Design SHA256: `8d08b01b3128d2a406e6321c221d37b11d8484d94156eafad9f88fd8c5e3c21a`. Candidate-binding SHA256: `b400299718b2b69b816def588197cf3681ede6c8faedbb132ed36a297ccc9d97`. Full result SHA256: `f0f1c384228bb9d64d1e4afe3894b653477b6d7d775860b10d5f5e2f3fb599a8`. No production file is edited by this benchmark.
