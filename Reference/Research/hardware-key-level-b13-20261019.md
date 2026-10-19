# b13 firmware key-level comparison - 19 October 2026

The candidate **fails the frozen audio adoption gate**. Its all-100 average errors improve on every timing map, but Bowed Bass 65 worsens by 0.179-0.209 dB in joint stereo band error on every map, exceeding the predeclared +0.1 dB focus-voice limit. That failure is retained. No threshold, timing, patch, amplitude law or window was changed to make it pass, and this run makes no production/default adoption.

All four Legacy full-performance WAVs are byte-identical to the b12 **Original-pitch** baseline. This is a key-level experiment with Original pitch fixed; it is not another Equal-versus-Original pitch comparison. The [machine-readable report](hardware-key-level-b13-20261019.json) preserves the complete 100-preset scores, all four metrics, signed differences, regressions, gates, provenance and post-run checks.

## Frozen comparison

The design was frozen before candidate implementation or audio measurement. Version 1 is preserved; version 2 explicitly identifies the b12 Original WAVs as Legacy targets, correcting inherited b11 Equal lookup labels without changing events, windows, controls or gates. Frozen v2 SHA-256 is `b15889ad4a109b0d6fde8ec4c8cd49903298e0af6e57958758a287d7c41a5a13`; candidate/runner binding is `566b51e1471b3247daf5e5b984c12856bc1c1f55789a0643f3406f3c3ed1da02`.

The candidate changes only the software key-level-command construction described in the [firmware level-command audit](opu-level-command-path-20261019.md). The existing 0.75 dB per raw TL code and TL99 mute remain amplitude hypotheses. No new velocity, volume, envelope, Reverb, Sustain, filter, DAC, noise or per-patch fit is introduced.

Both modes replay the same four existing Mode 00 maps, 1,761 notes, 3,622 events and 100 inferred program changes. Exactly the prior 100 absolute recording-time windows are scored. They keep the raw factory bank, twelve-voice allocation, clock settings, Recorded chorus and its -32/48000 s epoch, and remove the same 32-frame synthesis delay before comparison. These are reused regression data, not independent hardware holdouts. The three alternate timing maps remain scenarios, not adopted alignments.

## Aggregate result and gates

Lower errors are better. Signed differences are Firmware minus Legacy, calculated on unrounded values.

| Timing map | Legacy joint band, dB | Firmware, dB | Difference, dB | STFT log difference, dB |
| --- | ---: | ---: | ---: | ---: |
| Unchanged | 3.143844 | 3.090977 | -0.052867 | -0.004346 |
| Old scale / median offset | 2.893221 | 2.839806 | -0.053415 | -0.005738 |
| Nominal scale / median intercept | 2.879825 | 2.821473 | -0.058352 | -0.006628 |
| Equal-patch robust affine | 2.881928 | 2.823850 | -0.058078 | -0.006371 |

Mean mid-band error also improves by 0.059171-0.066701 dB, and mean STFT convergence improves by 0.002759-0.003808. These descriptive score changes are not percentages of hardware fidelity or measured listening preferences.

| Required audio gate | Frozen rule | Result |
| --- | --- | --- |
| Legacy compatibility | All four complete WAV hashes equal b12 Original | Pass |
| Primary improvement | Unchanged-map all-100 joint-band difference <= -0.01 dB | Pass |
| Other maps | Each all-100 joint-band difference <= +0.03 dB | Pass |
| Focus protection | Each of 65/93/97 on each map <= +0.1 dB | **Fail: Bowed Bass on all four maps** |
| STFT log protection | Each map's all-100 mean difference <= +0.05 dB | Pass |

The aggregate `audio_gates_passed` is **false**. Separate command, core, wrapper, CPU, SDK and host checks cannot override this failed audio gate; they concern different claims.

## Focus voices and mixed regressions

| Voice | Unchanged | Old scale / median offset | Nominal scale / median intercept | Robust affine |
| --- | ---: | ---: | ---: | ---: |
| Bowed Bass 65 | **+0.209059** | **+0.183059** | **+0.179110** | **+0.180878** |
| Human Voice 1 93 | +0.030937 | -0.045412 | -0.116675 | -0.102900 |
| Musical Saw 97 | +0.068930 | +0.016243 | -0.007202 | -0.003422 |

All cells are joint stereo band-error differences in dB. Human Voice and Musical Saw remain timing sensitive; no favorable map is selected to represent them.

The four maps contain respectively 43, 45, 46 and 43 positive joint-band regressions among all 100 voices. Bandoneon 21 has the largest on each map, +0.407131 to +0.427226 dB. Every positive regression for every metric remains in JSON, including the smaller values; improved averages do not hide these losses.

This does not invalidate the independently recovered software commands. It shows that combining them with the present amplitude/envelope/output hypotheses does not satisfy the predeclared recording-regression limits. This pass does not diagnose the remaining mismatch or compensate it with hidden patch/gain changes.

## Integrity checks and auditions

The fresh compiled runner retained the four Firmware float WAVs. Each newly rendered Legacy file was deleted **only after** exact whole-file hash equality with its preserved historical b12 Original file. Historical files remain present and reverified. All eight renders are finite, 8,931,705 stereo frames at 48 kHz; their unnormalized peaks span 2.183053-2.282613 because the research fixture deliberately uses gain 1 without a limiter. No clipping was introduced to store them.

Twelve clips at ignored `build/key-level-b13-20261019/audition.html` use **hardware -> Legacy -> Firmware**, with 250 ms silence between parts. Each model uses one RMS scalar for its stereo pair; one common safety scalar per focus voice spans every map/model. There is no separate channel gain, EQ, local timing, pitch or frequency fit. All twelve stored float32 clips were reconstructed sample-for-sample from the fixed windows and reported gains. Their peak is at most 0.616181, below the frozen 0.9 bound. Newly retained WAV storage is 304,132,276 bytes, below 500 MB.

Post-run validation rechecked the ten copied candidate source files, source/snapshot/fixture/runner/command-report hashes, all four historical WAV hashes, retained render and pressure hashes, score bookkeeping over all 3,200 four-metric cells, 1,600 signed differences, independently recomputed aggregates, complete regression lists, gate decisions and all twelve clip constructions. It did not independently recompute the raw spectral metrics. These integrity checks pass; that does **not** turn the failed adoption gate into a pass. Original protocol/result files were not overwritten.

The independent command evidence was bound before rendering. Its coverage includes 640 table entries, 32,768 LKS/note offsets, 4,194,304 composed valid TL/LKS/note commands, and 131,072 freshly executed original primitive cases. The 4,194,304 combinations are compositions of original primitive-output matrices, not that many complete original builder executions. This establishes bounded software equivalence, not the chip's amplitude transfer or a complete hardware model. Core/integration/host review remains separate; no Reason playback result is claimed by this benchmark.

The ignored result, binding, snapshots, validation script/receipt, full Firmware WAVs, pressure logs and clips remain under `build/key-level-b13-20261019`. Third-party recordings are local research inputs and are not product resources. No artificial noise, outreach, hardware operation or automatic adoption occurred.

## Preserved implementation and separate raw-score check

The [research patch](../Prototypes/key-level-20261019/README.md) reproduces all eight tested source/tool/test files against the pinned b12 commit. It is separate from production and is not a b13 Rack release. A fresh temporary repository applied the patch and reproduced every recorded target hash.

A subsequent independent parent check reran the six raw unchanged-map focus comparisons, covering all four metrics for each focus voice and model. All 24 values matched exactly; see `Tests/results/key-level-raw-focus-recheck-20261019.json`. This limited check supplements the full bookkeeping audit above and preserves the failed Bowed Bass gate. It is not a rerun of all 800 comparisons or a new hardware measurement.
