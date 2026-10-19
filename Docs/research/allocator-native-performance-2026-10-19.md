# Paired native allocator runtime probe — 2026-10-19

**The mean-time research sanity gate passes; the zero wall-deadline gate fails.** One fixed native run covered 65 rows and 285,389 blocks through the full `Press78OutputBus`. It recorded 103 elapsed-time deadline misses and zero thread-CPU deadline misses. Every failed block remains in the raw paired CSV. There was no rerun, subtraction of timing overhead, source optimization or production change.

This is a development-machine component measurement, not Reason scheduling, translated-target CPU, a realtime guarantee or evidence of hardware fidelity. The allocator’s separate functional/byte-identity gates remain separate from this failed wall-deadline gate. The [complete machine-readable report](allocator-native-performance-2026-10-19.json) retains every row’s mean, median, p95, p99, maximum, misses, paired CPU measurements, output checks, comparisons and source bindings.

## Frozen comparison

The prospective design (`build/allocator-native-performance-20261019/design-frozen.json`, SHA-256 `aad1a189bbc72baf4c5af9e4321a2190c8f8a2ffbdb02f8638851756cff490e8`) was written before compilation or measurement. It binds the unchanged b15 baseline’s 11 DSP files and all 12 frozen candidate DSP files from `candidate-validation.json` (`1eb807dcfe2d34330d37710271b81cd962ae243c627a7710287cce55fe5583e6`). Source snapshots were checked again after the run. Only compiler namespace substitution separates the two implementations in the executable; source bytes are unchanged.

Each row uses 64-frame blocks, two seconds of fixed preroll and three seconds of measured audio, rounded up to complete blocks. The run orders 44.1, 48, 88.2, 96 and 192 kHz. Within each workload, implementation order rotates every block. Idle, one sustained note and twelve sustained FM voices compare baseline Legacy, candidate Legacy and candidate Original under identical Real controls: original pitch/sustain policies, the existing circuit model, Recorded chorus, 20 ppm slow clock variation, fixed .25 gain, output protection and no additive noise. The exact patch/control assignments, order and thresholds are source-bound in the JSON.

Two further candidate-only cases hold CV note 127 after natural envelope retirement or immediate TL muting, then request the opposite allocator policy. Both directions remain pending throughout the measured interval and switch after the held input is released. These cases compare with the same candidate’s ordinary idle workload; they are not described as baseline-equivalent.

Each block has nested monotonic-wall and thread-CPU timestamps around the same processing call. Timer overhead is retained. Audio hashing, finite checks and output inspection occur outside the timed interval. Per-row mean wall time divided by its audio deadline had to remain below .5; zero wall misses and zero CPU misses were separate declared gates.

## Observed timings

The table reports twelve-voice FM means as fractions of realtime, expressed as percentages. Miss counts include all three ordinary workloads in that lane; pending misses are separate because the baseline has no corresponding policy-handover path.

| Host rate | Lane | 12-voice mean wall | 12-voice mean thread CPU | Ordinary wall misses | Pending wall misses |
| --- | --- | ---: | ---: | ---: | ---: |
| 44.1 kHz | baseline legacy | 7.919% | 7.868% | 0 | — |
| 44.1 kHz | candidate legacy | 7.707% | 7.658% | 0 | 0 |
| 44.1 kHz | candidate original | 7.655% | 7.603% | 0 | 0 |
| 48 kHz | baseline legacy | 5.696% | 5.654% | 0 | — |
| 48 kHz | candidate legacy | 5.714% | 5.667% | 0 | 0 |
| 48 kHz | candidate original | 5.650% | 5.616% | 0 | 0 |
| 88.2 kHz | baseline legacy | 9.083% | 9.040% | 0 | — |
| 88.2 kHz | candidate legacy | 9.087% | 9.041% | 0 | 0 |
| 88.2 kHz | candidate original | 9.021% | 8.976% | 0 | 0 |
| 96 kHz | baseline legacy | 12.469% | 9.496% | 31 | — |
| 96 kHz | candidate legacy | 11.110% | 9.493% | 21 | 6 |
| 96 kHz | candidate original | 11.249% | 9.437% | 21 | 10 |
| 192 kHz | baseline legacy | 13.269% | 13.165% | 6 | — |
| 192 kHz | candidate legacy | 13.255% | 13.159% | 6 | 0 |
| 192 kHz | candidate original | 13.162% | 13.064% | 2 | 0 |

The largest row mean is 13.269% of realtime. The largest elapsed block is 7.720 ms in the 96 kHz baseline twelve-voice row, whose 64-frame deadline is 0.667 ms. Its row has 31 misses; the matched candidate Legacy/Original rows have 17/20. Across ordinary rows the lanes have 37/27/23 misses; the additional pending cases contribute 6/10 candidate misses. These are descriptive observations from one interleaved run, not an implementation speed ranking.

At 48 kHz, pending ownership scans take about 1.962–1.974 times their own idle mean thread CPU, while still averaging approximately 1.30% of realtime. This measures the intended scan when a silent held CV input prevents the transition. It does not warrant changing the held-input semantics or making an optimization claim.

All 103 elapsed-time misses have paired thread CPU below the same deadline. That establishes a difference between elapsed and charged thread time in those blocks; it does not identify a particular process, scheduler action or cause. All prior unmeasured runs remain outside this evidence.

## Load, output and resources

The machine is an Apple M1 Max (10 reported CPUs), macOS 26.5.1 arm64, compiled with Apple clang 21 at `-O3` without fast-math or LTO. Concurrent work was left running. Ten process/load snapshots, taken every two seconds, show Python processes reaching 100% CPU and other desktop processes active; the one-minute load report moves from 8.11 to 6.87. The PM task owner separately confirms that observed PID 31589 was the still-running original PM v2 suite; other Python task identities are not inferred from executable names. Neither that confirmation nor the snapshots attribute individual missed blocks to a process. The monitoring itself is part of this experiment’s environment.

Every row passes finite/bounded output, zero counted render `new`/`new[]` calls, expected active-voice and effective-policy state, and the requested post-release handover. All 15 candidate-Legacy ordinary output hashes equal the paired baseline hashes. This compact custom-seeded FNV-1a-style check supplements, rather than replaces, the separately retained exhaustive byte-identity receipts; its exact nonstandard seed is recorded in the JSON. The peak reaches 1 under existing output protection; this is not an unclipped-output claim.

Measured instance sizes are 177,352/178,584 bytes for baseline/candidate engine and 193,816/195,048 bytes for their full output buses. The previously bound complete wrapper sizes are 194,848/196,080 bytes against the unchanged 196,608-byte project ceiling, leaving the candidate 528 bytes before any new wrapper metadata. The wrapper was not remeasured in this timer. Whole-process peak RSS is 8,404,992 bytes and includes the paired instances, both linked source namespaces and measurement storage.

The ignored raw report SHA-256 is `08ac0cb786956313f48895d6a756a6e0e198ebd842432f0355850198389c90c4`; raw `blocks.csv` SHA-256 is `ae941cb6cc5d800c29f86f0000799a0b5edad03857be4516455bbb7602e434ba`. The new JSON binds these artifacts, executable, environment, compile logs and all frozen sources. **The failed deadline gate remains a release limitation, not an excuse to rerun until green.**
