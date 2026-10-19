# Sine99 mixed-note IMD qualification

Research only. The frozen estimator failed its controls; captured source PCM was never opened. Do not use its fitted sideband coefficients as hardware distortion evidence.

`design-frozen.json` fixes supports, frequencies, nuisance lines and all gates. `analyze.py` generates synthetic controls and compiles `NativeProbe.cpp` against an ignored snapshot of the current DSP. If every gate passed it would stop for review; after the actual failure it preserves a complete result and never reaches source access. No download, codec decode, failed PM-method rerun or production edit occurs.

Original run:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python3 Tools/prototypes/sine-crossnote-imd-20261019/analyze.py
```

The completed `build/sine-crossnote-imd-20261019` is immutable; the script refuses its existing result. For reproduction copy the capsule and recorded DSP snapshot to a new isolated worktree/output path, retain the frozen design and do not change thresholds or supports after seeing results.

`NativeSuperpositionProbe.cpp` is a separate postfailure diagnostic. Its original run was posthoc. A redundant unchanged repeat is retained under ignored artifacts and supplies no independent/prospective evidence. Neither run retries the estimator or opens source PCM.

See [the report](../../../Docs/research/sine-crossnote-imd-2026-10-19.md) and its complete JSON ledger for source/executable/audio hashes and identification limits. No control audio is shipped.
