# YM3420 converter resolution from PSS-680 recordings — 20 October 2026

Three PSS-680 single-note recordings (the PSS-780's YM3420) were tested against
quantising converter candidates. The analysis scripts ran outside this
repository (Python with NumPy) and are not committed; the recordings are
third-party and are identified by hash only. No DSP, control or version changes
follow from it. Tags: **SIB-MEAS** measured on a PSS-680; **SIB** a sibling
value; **CALC** calculated; **INVENT** no source.

## Verdict

No coarse-converter signature; every 9-bit candidate is contradicted. Above a
resolution floor the recordings cannot tell bit depth or alignment, so no
converter model ships on this evidence.

| Candidate | Verdict | Main numbers |
| --- | --- | --- |
| YM2413-style 9-bit sign-magnitude with offset (Nuked-OPLL law) | Contradicted at every alignment | Predicts odd harmonics at −11.6 to −15.7 dB re h1 in the end windows and h1 +3.0 to +3.4 dB. Measured odd content, all causes: −43.6 / −40.5 / −35.2 dB |
| YM3438-style 9-bit two's complement (floor) | Contradicted | Odd −13.2 to −18.0 dB |
| YM2612 9-bit ladder (−7 on negative codes) | Contradicted | h1 plateau +11.6 to +13.7 dB, odd −8.9 to −10.0 dB |
| 9-bit sign-magnitude truncation (dead zone) | Contradicted | h1 −3.7 to −7.3 dB, odd −6.8 to −10.9 dB |
| 9- and 10-bit linear, rounding | Contradicted | 10-bit: odd −26.0 dB on synth_bass (z 387), −35.9 dB on saw_synth (z 9.5) |
| 11-bit and finer linear | Consistent | — |
| Sign-magnitude or offset formats at 12–13 bits | Contradicted (crossover) | 13-bit synth_bass: z 30.7 (dead zone), 21.5 (offset) |
| Same at 14 bits | Borderline | z 2.8 and −0.1 |
| Same at 15 bits | Consistent | — |
| Floating, 10-bit mantissa + 3-bit exponent (YM3012-like) | Consistent | Indistinguishable from ideal |

- Alignment cannot be separated from bit depth; the recordings bound only the
  step relative to a note's own peak (6 dB of headroom per bit).
- Robust bound (distortion): step ≤ 2⁻¹⁰ of the note's DAC-domain peak.
- Conditional bound (12.5–20 kHz noise): about 2⁻¹², only if the PSS-680
  loses no more treble than the PSS-480 one-pole.
- A 9-bit converter would pass only if the voice overdrove full code by
  ≥ 12 dB, which is contradicted: on synth_bass notes 36–58 attack RMS still
  differs by 3.9 dB and the tail law by 3.7 dB (clipping would leave ~0.5 dB).
- Abrupt note endings are not a converter effect: all 63 notes end at one
  output level (h1 median −56.37 dBFS, IQR −56.65 to −56.07) with the same
  4–5 ms fade, whatever the decay rate (24–306 dB/s). The end follows output
  level, not envelope time (slope of end level on attack level 0.02–0.21).
  It fits a per-voice total-attenuation end plus a fast damp
  ([DAC endpoint evidence](dac-endpoint-evidence-2026-10-19.md); YM2413 clamps EG+TL+KSL).

## Material

| File | sha256 | Length | Content |
| --- | --- | --- | --- |
| `synth_bass_1.wav` | `d8200250a990f5dc56fe3898b7ef2a3420bbce26b12310b254a6f94819f6a7dc` | 44.42 s | 21 notes, MIDI 36–96 |
| `saw_synth.wav` | `68a1c962f5cf4d9294504c04fe78ca7c6b178fb630fe704593d144894fa6b59a` | 32.42 s | 21 notes |
| `chiptune_esq.wav` | `404f7c29825d8ce547c96352acbe525e9c3964494074d8cb4b00860926311d4c` | 28.04 s | 21 notes |

44.1 kHz/16-bit mono, background −73 to −75 dBFS, no gating or normalisation,
all small codes present. Chip rate measured 57,283.1 Hz on the recorder clock.
Candidate laws from Nuked `opll.c` (`d486915d…`) and `ym3438.c` (`8fa38554…`).

## Method

Measured harmonic tracks (≥ 10 dB above floor, 20 ms smoothing) divided by the
PSS-480 7.23 kHz one-pole (SIB) give an ideal note at the converter; h1's tail
is its fitted exponential (rms 0.09–0.17 dB). Each candidate quantises it,
passes the one-pole, is resampled to 44.1 kHz and gets the file's own
background. Pooled coherent power at k·f0 in an end window (250 ms synth_bass,
40 ms fast releases), minus the background estimator's mean, relative to h1. A
candidate is contradicted if the odd power it adds exceeds the recording's own
odd content by 3 null standard deviations, or it moves h1 by > 1 dB.

## Side observations

- No YM2413-type 0.375 dB envelope staircase (76 Hz line 0.002–0.013 dB where
  it would be 0.119 dB); 0.1875 dB steps also absent. The YM3420 envelope is
  finer than the YM2413's.
- An unexplained 2f0 line at a constant −85 dBFS, not produced by any
  candidate; not used.

## What this licenses

Dropping the YM2413, YM3438 and YM2612 9-bit per-voice models, any 9- or
10-bit linear converter at a non-clipping alignment, and sign-magnitude or
offset formats through 13 bits (as far as the PSS-780's YM3420 is the same
part). It does not license any bit depth or alignment; picking one inside the
bound would be INVENT, and no listening test can choose (all surviving
candidates are inaudible against the ideal control).

## Capture that would settle it

1. Probe YM3420 TB (pin 42) before the averaging filter at ≥ 2 MS/s, ≥ 12 bits,
   with one slow-decaying pure carrier.
2. Line out at ≥ 96 kHz/24-bit, constant gain, the same decay at carrier TL
   0/+12/+24 dB and two volume settings.
3. The weak-plus-strong pair from the [DAC endpoint evidence](dac-endpoint-evidence-2026-10-19.md) for
   per-voice versus post-mix conversion.
