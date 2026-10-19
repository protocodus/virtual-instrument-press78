# Drive, feedback and output separation

Research-only native public-API experiment. The adjacent frozen design fixes
72 cases before execution: six mechanisms, two raw carrier levels, two master
gains, and two single notes plus their simultaneous chord. No factory payload
is used and no production code is modified.

Run from the repository root with the existing C++17 compiler and NumPy:

```sh
mkdir -p build/drive-output-separation-20261019
clang++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Werror \
  -I Source/DSP \
  Tools/prototypes/drive-output-separation-20261019/Probe.cpp \
  Source/DSP/Press78Engine.cpp \
  -o build/drive-output-separation-20261019/probe
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 \
  Tools/prototypes/drive-output-separation-20261019/analyze.py \
  build/drive-output-separation-20261019/probe \
  build/drive-output-separation-20261019/result.json
```

The native executable emits float32 to a Python subprocess pipe. Python keeps
it in memory long enough to analyze the predeclared window and then discards
it. Results contain every case's hash, metrics, source/executable bindings,
superposition residuals and failed contracts. No audio file is saved.

The common frequency vector orders harmonics1–12 of MIDI45 first, then
harmonics1–12 of MIDI51, then six named intermodulation witnesses. For a
single MIDI51 tone its fundamental is index12, not index0. The six witness
amplitudes used for shared nonlinearity are measured from the **chord minus
the two corresponding single-note renders**, rather than declaring every
extra partial in an FM voice to be output distortion.

These are software-mechanism measurements, not THD/IMD specifications of the
PSS-780. Plugin MasterGain is not an identified implementation of hardware
MELODY VOLUME. Raw carrier TL is not the front-panel loudness display. See
[the report](../../../Docs/research/drive-output-separation-2026-10-19.md).
