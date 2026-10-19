# Assumed hardware auditions, 2026-10-19

The user explicitly authorized estimates after the unsuccessful manual/sample
recovery. Two research-only candidates now produce audible native-engine
comparisons: a sibling-inspired release knee and shared asymmetric output
headroom. Their constants and placement are chosen hypotheses. They do not
identify the YM3420 or establish an improvement against calibrated hardware.
Production DSP, defaults, presets and the Rack adapter remain unchanged.

## Release hypothesis

Yamaha's [TX81Z manual, printed p.23](https://usa.yamaha.com/files/download/other_assets/9/316769/TX81ZE.pdf)
describes carrier-triggered envelope pseudo-reverb. The retained
[evidence review](reverb-release-evidence.md) distinguishes that OPZ precedent
from the undocumented PSS-780 implementation. The PSS-780 owner documentation
and recordings motivate examining the tail, but do not recover its law.

Candidate B assumes Reverb is enabled. Once the carrier's absolute internal
envelope attenuation reaches 18 dB during release, both operators use the slower
of their ordinary release and their own native RR4 rate, including their
existing note/RKS law. A single carrier snapshot is taken before either
operator advances. Operator TL, velocity and output gain do not enter that
trigger. This assumes the TX81Z-style trigger/coupling architecture and chooses
RR4; neither is recovered for the PSS-780.

The helper temporarily caps the actual native envelope's coefficient for its
actual native tick and restores it afterward. It changes no attack, held decay,
waveform, feedback, allocator or retirement endpoint. It does **not** reuse the
previous threefold timing multiplier. Native RR4 at RKS0 is 45.254834 dB/s;
the old 15.084945 dB/s figure included that multiplier. Earlier unfavorable
whole-bank results remain preserved and are not overturned by these auditions.

Three sparse sets use the existing factory Bowed Bass 65, Human Voice 1 / 93 and
Musical Saw 97 with the front Sustain switch off. Each plays two 1.5 s held notes,
one octave apart, with enough space for both tails. Only one voice is active
at any time, avoiding the old polyphony-pressure confound.

| Preset | A: current tail | B: assumed tail | B listening trim |
| --- | ---: | ---: | ---: |
| Bowed Bass |0.30 s|0.82 s|−0.005797 dB|
| Human Voice 1 |0.12 s|0.54 s|−0.003965 dB|
| Musical Saw |0.22 s|0.58 s|−0.003272 dB|

These are the **last-above −40 dB, 20 ms RMS window endpoints** after the first MIDI
note-off, relative to that note's held reference measured from 1.25–1.65 s.
They include the unchanged 32-frame native latency. They measure the model's
behavior, not the real instrument's release time or a perceptual audibility
threshold. Raw held audio through note-off plus latency is bit-identical.

## Output hypothesis

Candidate B inserts a deterministic, zero-centered biased soft-headroom curve
inside the native shared mono path, immediately before the existing sibling
analog filter. All voices feed that one curve. Existing creative Drive is off.

```
t = tanh(x / H)
y = H * t / (1 + tanh(b) * t)
```

The chosen normalized headroom is H=1, shape bias b=0.14. They are not volts,
component tolerances, a measured converter transfer or fitted parameters.
The sign of asymmetry and insertion point are also choices. The curve has
unity small-signal slope, exact zero output at zero input, unequal positive
and negative headroom, and increasing compression with level. This is a
plausible output-stage hypothesis, not a detailed recovered transistor circuit
or a DAC bit-depth model. Rationale and limits are beside the
[implementation](../../Tools/prototypes/assumed-hardware-20261019/output-notes.md).

The output audition plays existing Sine Wave 99, Synth Bass 79 and Human Voice 1
at individual/chord levels. Unmatched peak changes 0.329690→0.309860; whole-file
RMS matching trims A by −0.385899 dB. The raw difference RMS is −24.009264 dB
relative to A. These are software contrasts, not improved-fidelity scores.
The H2/H3 figures in the implementation notes are leading-order analytical
expectations only; this run did not numerically measure transfer harmonics.

No hiss, hum, dither, random faults, memory corruption, startup bias, supply
sag, new clock modulation or converter quantizer is added. The curve runs at
the existing output rate; hard-drive aliasing is a numerical limitation, not
identified YM3420 behavior. Real voltage-to-sound coupling remains unknown.

## Protocol, preservation and checks

The [frozen protocol](../../Tools/prototypes/assumed-hardware-20261019/design-frozen.json)
declares 48 kHz, 14 s stereo float audio and 64-frame processing. Each A/B set uses
identical MIDI, controls and source. A compiles the native engine text without
substitutions. The B translation units are generated with exactly one asserted
insertion point for the corresponding mechanism. No offline envelope/output
substitute is used. No real recording is read, scored or fitted in this run.

Native output circuit is enabled; tone filtering, chorus, creative Drive,
clock variation and output limiting are disabled; DC blocking is enabled.
Master gain is 0.5, pitch/sustain models are Original. A therefore means the
unchanged shipping implementation **under these controlled settings**, not
the startup bass preset at its ordinary defaults.

Original raw WAVs and separate matched copies are retained under ignored
`build/assumed-hardware-20261019/run-02/`. Each listening pair is matched on
whole-file stereo RMS to its quieter member, followed by the same peak safety
factor. All common factors are 1. Filenames are A.wav/B.wav; separate key.md
files disclose mechanisms and gains. There is no selected listener verdict.
The local index.html exposes all four pairs with HTML audio controls.

The [result receipt](assumed-hardware-auditions-2026-10-19.json) binds source,
generated source, raw PCM, raw WAV, matched WAV and gain values. All 11 production
DSP files retain their pre-experiment hashes. Checks passed for:

- Exact native Reverb-off state and complete Human Voice 1 audio parity;
  correct knee gate, native rate scaling, coefficient restoration and
  preservation of already slower rates.
- Exactly silent fresh no-note renders for baseline and both candidates;
  finite audio; monotonic, bounded, zero-centered output with unity slope.
- Exact 64/257-frame processing equivalence on representative native cases;
  identical held portions in all three release sets.
- Repeated fresh output instances producing identical audio. The original
  receipt names this `output_reset_determinism_exact`; its actual scope is
  fresh-instance reproducibility, not an already-excited reset.
- A separate post-excitation reset contract for baseline and both candidates:
  reset while voices/effects are active, 1024 frames of exact silence, then
 131072 frames matching a fresh instance. Its supplemental receipt is retained
  under `run-02/reset-contracts.json`.

The envelope helper also passed optimized and ASan/UBSan native-envelope
contracts across all note/RKS/RR combinations; those check the code, not the
chosen hardware assumptions. Independent artifact review is recorded in
[the validation receipt](../validation/assumed-hardware-independent-review-2026-10-19.json).

Failures remain available. Run01 stopped before audio because its test wrongly
expected a native envelope already in release stage 3 to stop releasing when a
direct caller passed released=false. The corrected test distinguishes held
stage 2 from entered release stage 3; no model/helper changed. All seven original
input source snapshots were reconstructed and verified against their recorded
hashes. Run02 also retains all seven hash-bound input snapshots. The first
supplemental reset fixture waited until its voices had already retired; its
failed probe/logs remain under `reset-first-attempt/`, and the corrected fixture
shortens the pre-reset wait to exercise active state. No audition was rerendered
to refresh a score or obtain a different result.

The tools, assumptions and receipts can be reviewed independently. No version
bump, product adoption, Recon installation, host test or hardware-matching claim
is licensed by this experiment. A by-ear preference can guide a later model
choice, recorded explicitly as a preference.
