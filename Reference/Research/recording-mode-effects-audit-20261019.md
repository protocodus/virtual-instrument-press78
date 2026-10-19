# Recorded MIDI mode and effect states — 19 October 2026

The reused PSS-780 tour visibly displays **c.00**, Yamaha's Keyboard Assign mode, at all 300 sampled preset frames and six additional Sine99 frames. Its documented note reception is **36–96**. The previous benchmark rendered 18 source-MIDI notes below that range. This supports a separately labeled source-input correction under the existing assumption that the published MIDI numbers reached the keyboard unchanged. It does not justify restricting the plugin engine's extended playing range.

The effect audit also checks a competing release explanation: all sampled Vibrato/Sustain indicators agree with their imported factory flags. Reverb and Chorus are on at every sampled preset. Sustain and Reverb are distinct states; replacing one with the other would contradict these observations. No effect algorithm or envelope constant is recovered.

This is new measurement of an already reused [recording](https://www.youtube.com/watch?v=ONfIvtDOog0), not a fresh recording or unseen holdout. The [JSON ledger](recording-mode-effects-audit-20261019.json) retains the protocols, all samples, raw pixel features, source hashes, manual-page provenance and exclusions. No production DSP, presets, old benchmark scores, alignment, package or host state changed. Artificial noise remains excluded.

## Frozen pixel measurement

Only the existing Harp69 and Sine99 frames at observed-LCD-start +0.8 s supplied calibration. Their LEDs were visually read first. A single shared threshold uses the median of five lit and seven unlit calibration cells. It is not fitted to the other presets or to the factory flag table.

For each of six fixed LED positions, a 9×9-pixel region supplies the mean of its five largest `R − max(G,B)` values. Calibration gives threshold86.2: ON requires more than96.2, OFF less than76.2, and the intervening band is UNKNOWN. No per-LED threshold or later adjustment is used. Each preset contributes frames at observed LCD start +0.4,+0.8,+1.2 s. All three must agree on a known state; disagreement is unresolved.

The completed protocol SHA256 is `62c5974f1a4a690e8560013ded8c598be9635358aaa8dd83224c63d4d72781b7`. It was frozen before the 300-frame measurement. Every preset resolves at its three snapshots:

| Indicator | ON presets | OFF presets | Unresolved |
|---|---:|---:|---:|
| Vibrato |37|63|0|
| Sustain |6|94|0|
| Reverb |100|0|0|
| Portamento |0|100|0|
| Stereo Chorus |100|0|0|
| Duet |0|100|0|

The six Sustain-on presets are69,70,81,82,84,97. All 200 Vibrato/Sustain comparisons agree with raw voice byte24 bits7/6. There is no raw Reverb field to compare. The 1,800 observed scores remain well separated: every ON score is at least121.6, every OFF score at most41.4. All ten contact sheets were visually checked for both preset identity and the right-hand c.00 display.

The first implementation failed to initialize ffmpeg's 300-term, left-associated selection expression. It produced zero output frames and no result. Its protocol and tool remain preserved. The completed run balances exactly the same expression terms, leaving frame selection, pixel geometry, calibration and classification unchanged. The retained evidence establishes failure before any output frame was extracted, without claiming an internal decoder stage.

## Late Sine99 coverage

The primary Sine99 snapshots stop at176.867 s, before the later pitch and release windows. A separately frozen extension therefore samples179.5,180.0,181.5,182.5,183.5,184.5 s. It reuses the original geometry, threshold and margin without recalibration. Its protocol SHA256 is `f298f66dea57184a4c5604e60c12be63afef09e34fcb03ba6cfddebee630f760`.

All six additional frames show preset99 and c.00, with Reverb/Chorus on and Vibrato/Sustain/Portamento/Duet off. These times were chosen after the previous pitch/tail analyses; they are a disclosed coverage check, not new independent validation. Neither the initial snapshots nor this extension prove uninterrupted state between samples.

## Manufacturer mode distinction

The [original owner's manual](https://www.nurykabe.com/dump/docs/PSS/manuals/PSS-780_00.pdf) was visually checked at printed31,34,45,46. Printed31 explicitly identifies c.00 as Keyboard Assign and c.99 as Sound Source mode. Printed34 says Keyboard Assign receives only the keyboard's five-octave note range and does not accept velocity. Its printed45 chart specifies recognized notes36–96. The next chart's Mode99 instead recognizes0–127 and lists24–108 as its True voice range; those two fields must not be conflated.

The published MIDI contains 1,779 notes, all velocity127 and pitches29–87. Exactly18 fall below36: MIDI29 twice,34 thirteen times and35 three times, all on zero-based channel1. A Mode00 fixture can exclude both on/off events of those notes, retaining 1,761 notes and all100 inferred program commands. Velocity adds no new difference for this maximum-velocity file.

This is conditional on the published MIDI matching the actual sender. No wire log, sender configuration, remapping or continuous transposition record is available. The display does not establish exact MIDI arrival times. The [broader pitch audit's](pitch-pattern-audit-20261019.md) inability to identify the nominal MIDI34 partial is consistent with the documented range, but does not independently prove what bytes were transmitted. No octave folding is inferred.

The [separate Mode00 benchmark](mode00-benchmark-20261019.md) freezes this source-policy branch before scoring and retains every original comparison. It changes the reference fixture, not the synth's musical range, factory parameters or release law. Existing timing, program-inference, channel ownership and capture-chain assumptions remain explicit.

## Reproduction and verification

`Tools/audit_recording_effect_states.py` separates calibration/protocol freezing from target-frame measurement and refuses to reuse a started output. It reads the existing video, timeline and bank; no audio is rendered or fitted:

```sh
python3 Tools/audit_recording_effect_states.py freeze \
  --reference-root /path/to/original/pss780-experiment \
  --output build/effect-state-audit-new
python3 Tools/audit_recording_effect_states.py run \
  --output build/effect-state-audit-new
```

Independent review reproduces all 300 source frames pixel-for-pixel, all 1,800 features/states, the threshold, 200 raw-flag comparisons and the 18 exclusions by parsing the binary MIDI independently. Video frame n/30 matches container timestamps within0.333 ms. Downloaded frames, crops, contact sheets, manual pages and failed-run artifacts stay ignored locally. Their presence is analysis provenance, not redistribution or commercial clearance of source recordings or the factory bank.
