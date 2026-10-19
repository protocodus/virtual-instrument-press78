# Signed squared sine research probe

This audits actual shipping `wave(phase,1)` and the retained, previously
analyzed PSS-680 carrier-only waveform experiment. It changes no production
DSP. `design-frozen.json` was written before this new raw-capture inspection;
the two one-second native controls were rendered once. Copyrighted media
stays at its original ignored path and is not redistributed here.

From repository root:

```sh
mkdir -p build/oscillator-signed-square-audit-20261019
clang++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Werror -I Source/DSP \
  Tools/prototypes/oscillator-signed-square-audit-20261019/Probe.cpp \
  -o build/oscillator-signed-square-audit-20261019/probe
build/oscillator-signed-square-audit-20261019/probe \
  build/oscillator-signed-square-audit-20261019 \
  > build/oscillator-signed-square-audit-20261019/native-probe.json
OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python3 \
  Tools/prototypes/oscillator-signed-square-audit-20261019/analyze.py \
  --output build/oscillator-signed-square-audit-20261019/result.json
python3 Tools/prototypes/oscillator-signed-square-audit-20261019/derive.py \
  build/oscillator-signed-square-audit-20261019/result.json \
  build/oscillator-signed-square-audit-20261019/conditional-transfer.json
OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python3 \
  Tools/prototypes/oscillator-signed-square-audit-20261019/check.py \
  build/oscillator-signed-square-audit-20261019/result.json \
  build/oscillator-signed-square-audit-20261019/validation.json
```

Do not rerender the controls merely to refresh existing evidence. The
coefficient analysis may be repeated against the same retained files; its
inputs and the engine source must match the frozen hashes.

The retained first implementation fails before writing a result because
its observation weighting accidentally broadcasts to a matrix. The three
retained verifier failures expose excessive assertions about whole-file
mono, quiet-harmonic logarithmic precision and optimized floating-point
bit identity. Their JSON notes state the actual observed values and scoped
corrections. No audio, fit, window, frequency, hardware gate or model
parameter changed to repair these checks.

The final verifier passes 111 checks; that is software/data consistency,
not evidence that the OPU ROM, arithmetic or converter has been recovered.
See [the full report](../../../Docs/research/oscillator-signed-square-audit-2026-10-19.md)
and its JSON receipt for results and conditional transfer diagnostics.
