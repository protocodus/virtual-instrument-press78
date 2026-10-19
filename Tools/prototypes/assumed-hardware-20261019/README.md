# Assumed-hardware auditions

Research only, explicitly requested as estimates. A is the unchanged native
engine under the frozen controls; each B changes exactly one mechanism.

- `EnvelopeHypothesis.h`: assumed carrier-triggered release knee, through the
  actual native envelope, with native operator-specific RR4/RKS ceilings.
- `OutputHypothesis.h`: chosen zero-centered asymmetric shared headroom inside
  the native mono output path. No added noise or claimed converter bit depth.
- `Renderer.cpp` / `run.py`: generate strictly checked native source variants,
  compile, test and export raw plus whole-file RMS-matched WAVs. No recordings
  are read and no constants are fitted.
- `ResetContracts.cpp`: separate post-excitation reset check against the same
  generated variants; no PCM/WAV output.

The completed one-time audition lives under ignored
`build/assumed-hardware-20261019/run-02/`. Preserve it; do not refresh the
renders merely because later engine code changes. Its `index.html` has all
four audio pairs, with a separate `key.md` for each set. Input source snapshots
and earlier failed checks remain alongside the results.

For a genuinely new experiment, review the frozen protocol and use a new path:

```sh
python3 Tools/prototypes/assumed-hardware-20261019/run.py \
  build/assumed-hardware-20261019/new-experiment
```

The [report](../../../Docs/research/assumed-hardware-auditions-2026-10-19.md)
defines the evidence, chosen values, scalar metrics, validation and limits.
The public result receipt describes the completed run; files added afterward
(this README and the supplemental reset probe) are not falsely represented as
inputs to that original run. No shipping version/default or listener verdict
is changed.
