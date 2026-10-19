# SIN symmetry and observability probe

This research-only tool reads the already retained PSS-680 carrier-only
recording. It does not model a Yamaha chip or write audio. The adjacent
`design-frozen.json` fixes the window, subdivisions, original frequency,
nuisance fits, and 99 synthetic symmetry examples before this new execution.

From the repository root, with NumPy and SciPy already available:

```sh
mkdir -p build/oscillator-sine-audit-20261019
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 \
  Tools/prototypes/oscillator-sine-audit-20261019/probe.py \
  build/oscillator-sine-audit-20261019/result.json
```

Do not download a substitute source or adjust windows if the original retained
PCM is absent. Its hash is required. Source recordings remain local and are
not product resources. Frozen results and interpretation are in
[the audit](../../../Docs/research/oscillator-sine-audit-2026-10-19.md).

The synthetic bit widths are deliberately arbitrary test-fixture dimensions.
They are **not** identified OPU phase/address/DAC widths. The probe tests a
static phase-domain symmetry invariant; native-update aliases, asymmetric
tables, phase-section logic, nonstationarity and capture distortion remain
outside this invariant. No production DSP inclusion is intended.
