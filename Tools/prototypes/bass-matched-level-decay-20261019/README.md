# Bass matched-level decay diagnostic

This bounded research experiment reads **saved H1-amplitude JSON only**. It
does not decode, download or render audio and runs no PM-envelope method.
The original source curves and their acquisition limits are described in
[the earlier report](../../../Docs/research/opu-envelope-independent-2026-10-19.md).

Three distinct stages remain frozen:

1. `design-frozen.json` / `analyze.py`: all 16 curves at fixed −26…−22 dBFS,
   one crossing and a fixed 50 ms local-slope neighborhood. This is a numerical
   diagnostic; its synthetic controls do not bound interpolation error for
   **every** differentiable monotonic scalar map.
2. `traversal-design-frozen.json` / `traversal.py`: separate posthoc
   crossing-bracket duration experiment, proposed after reviewing that limit.
   V1 uses direct floating timestamp subtraction. Its result is retained as
   a numerical-comparison failure because epsilon-only separations occur.
3. `traversal-sample-centers-design-frozen.json` /
   `traversal_sample_centers.py`: a separately frozen implementation correction.
   The original H1 extractor rounded timestamp×44100 to integer PCM centers;
   the corrected runner reproduces those 220/221 sample hops and makes every
   interval/comparison decision in integer samples, with denominator 44,100.
   All levels, notes, crossings and comparisons remain the same.

From the repository root:

```sh
mkdir -p build/bass-matched-level-decay-20261019
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 \
  Tools/prototypes/bass-matched-level-decay-20261019/analyze.py \
  build/bass-matched-level-decay-20261019/result.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 \
  Tools/prototypes/bass-matched-level-decay-20261019/traversal.py \
  build/bass-matched-level-decay-20261019/traversal-result.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 \
  Tools/prototypes/bass-matched-level-decay-20261019/traversal_sample_centers.py \
  build/bass-matched-level-decay-20261019/traversal-sample-centers-result.json
```

The final runner also requires the hash-bound historical extractor source and
its frozen JSON protocol at the paths in its design, to verify the actual
measurement-center convention. It reads their text/JSON, never their WAV.
Missing/mismatched artifacts are a failure, not permission to substitute a
different recording or guessed sample rate. Do not overwrite completed frozen
receipts during later research; use another output directory and bind the
historical v1 input explicitly if repeating the experiment.

The [current report](../../../Docs/research/bass-matched-level-decay-2026-10-19.md)
and JSON preserve all 80 local slopes, 160 corrected duration intervals, 640
cross-group comparisons, all 10 level-pair summaries and 74 changed
classifications versus v1. Full synthetic/v1 receipts remain in ignored build
storage with hashes; the export contains their coverage/failure summaries.
No result identifies an original RKS, release-rate or capture-distortion law.
