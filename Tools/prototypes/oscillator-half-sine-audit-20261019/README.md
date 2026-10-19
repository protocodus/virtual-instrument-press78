# HALF waveform: operator mean and DC-placement probe

This is research evidence, separate from the shipping engine. The prospectively
written [protocol](design-frozen.json) binds the unchanged engine sources and
the retained PSS-680 waveform measurements. It neither fits a hardware constant
nor changes a waveform, default, preset, output circuit, or noise path.

From the repository root:

```sh
mkdir -p build/oscillator-half-sine-audit-20261019
clang++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Werror \
  Tools/prototypes/oscillator-half-sine-audit-20261019/HalfSineProbe.cpp \
  -o build/oscillator-half-sine-audit-20261019/probe
build/oscillator-half-sine-audit-20261019/probe
```

The committed [native receipt](native-validation.json) is the first execution.
The C++ file includes the unchanged production implementation and uses its
existing friend test seam. No production visibility or test hooks are added.

The probe establishes mathematical/current-source contracts only:

- Half sine has mean `1/pi`, fundamental amplitude `1/2`, even cosine partials
  `-2/[pi*(n*n-1)]`, and no odd partials above the fundamental.
- The actual `Voice::next` passes the unipolar modulator into the carrier phase
  lookup. It does not subtract the half-sine mean.
- Adding a constant to a carrier-only held waveform is unobservable after the
  output DC filter has settled. This does not cover a known envelope transient.
- At zero feedback, subtracting the modulator mean rotates the carrier lookup
  by `8*g` radians under the current engine's `8*pi` scale. For constant `g`
  this is not a frequency shift. For varying `g`, the phase derivative changes
  by `(4/pi)*dg/dt` Hz. These factors describe the current implementation,
  not identified physical OPU scaling.
- Mean subtraction before the carrier lookup and DC filtering after it are
  different operations. Their noncommutation is demonstrated using a fixed
  arbitrary synthetic fixture, not scored as a hardware improvement.

No numerical OPU clock, ROM/phase/DAC precision, DC compensation, phase reset,
or feedback law is identified by these tests. The full evidence and next
separating measurement are in the
[audit](../../../Docs/research/oscillator-half-sine-audit-2026-10-19.md).
