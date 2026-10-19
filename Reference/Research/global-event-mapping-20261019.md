# Held-out global audible-event mapping - 19 October 2026

The fixed corrections improve average timing prediction on the new observations, but **none passes the frozen adoption criteria**. Jazz Guitar 52 has two clear audible transitions 55.7-68.1 ms earlier than the old MIDI mapping, while Vibraphone 91 and Music Box 98 are 31.5-54.5 ms later. One global offset or affine correction does not resolve that local variation. The three corrected maps have near-equivalent aggregate errors and remain an unresolved sensitivity family; their exact coefficients are preserved for later fixed-map comparisons.

No existing alignment, spectral benchmark score, DSP, preset, package or host state was changed. This is held-out timing validation within the already reused PSS-780 tour, **not a fresh recording**. The [JSON report](global-event-mapping-20261019.json) preserves the calibration/validation separation, frozen rules, all selected notes, failures, map scores and hashes.

## Freeze and equal-weight calibration

The previous [18 onset observations](midi-alignment-audit-20261018.md) from Toy Piano 5, Celesta 18, Glockenspiel 88 and Sine Wave 99 are **calibration only**. No new onset observation chooses a map parameter. Simultaneous notes first contribute one median residual at their shared onset. Each patch then contributes its median source-MIDI time and median unique-onset residual. Its summary audible time is the old affine prediction at that median MIDI time plus the median residual. All four patch summaries receive equal weight; the nine Sine notes cannot dominate the other patches.

This aggregation is explicitly different from a median over the 18 individual notes. The resulting four residual summaries are 23.222,33.762,53.292 and 50.452 ms for 5,18,88,99 respectively. There are 16 calibration onset groups. The summary is a robust prediction fixture, not a recovered hardware clock.

The protocol and every candidate coefficient were saved before measuring new onsets: SHA256 `13c20f46868af731914e5d5bfdd9c88b30d4958b159804f2d3f8b655fa595dd2`.

For `audible_seconds = a + b * MIDI_seconds`:

| Candidate | a, seconds | b |
|---|---:|---:|
| Unchanged |0.8906462238832541|0.9998070138348876|
| Old scale + median offset |0.9327535031570672|0.9998070138348876|
| Nominal scale 1 + median intercept |0.9129181334157996|1.0|
| Equal-patch robust affine |0.9158456466155656|0.9999670078976708|

The offset candidate adds the median of four patch residuals to the old offset. The nominal-scale candidate takes the median of four (summary audible time minus summary MIDI time). The robust affine scale is the median of six pairwise slopes between the four summary points; its intercept is the median of four (summary audible time minus fitted scale times summary MIDI time). These rules and results were frozen together, with input hashes.

## Fixed validation and acceptance

Metadata selects the remaining both-operator rawAR63 patches with modulator TL≥40, a sine carrier and the voice Vibrato flag off: 19 Glass Celesta, 52 Jazz Guitar, 91 Vibraphone and 98 Music Box. The original guards remain MIDI≥72, at least 0.1 s after the inferred program boundary, and at least 0.25 s since the previous same-pitch source MIDI note-off.

Glass Celesta 19 yields **zero eligible notes**: every note in that program interval is below 72. That absence remains explicit; its guards were not relaxed and no other patch was substituted. Jazz Guitar contributes two notes, Vibraphone three and Music Box two, all at different onset times. This leaves seven validation groups in three usable patches, spanning approximately 93-175 s. It supplies no new early-performance check.

The estimator is the same as the previous audit: arithmetic stereo mid, nominal-carrier complex demodulation with centered 12/24/48 ms Hann windows. Old-mapped-onset [-120,-70] ms and [+70,+110] ms medians define the amplitude step; 10%,50%,90% crossings are searched over [-80,+140] ms. A crossing must persist above the threshold for more than 90% of the next 2 ms of samples. Primary 24 ms /50% observations require positive amplitude change, after/before contrast≥2 and an observed crossing. Candidate maps never move these measurement windows. No synthesized attack, waveform correlation, local alignment search, pitch fit or spectral-error optimization is used.

For each map, group residual is measured audible onset minus its fixed mapped source-MIDI onset. Each usable patch contributes the median absolute group residual; the primary score is the equal-weight mean of those patch errors. The frozen acceptance rules require:

- At least three usable validation patches, each with at least two valid onset groups, and at least six groups total.
- At least 20% primary-score reduction against the unchanged map.
- No patch's median absolute error worsening by more than 5 ms.
- At least 3 ms primary-score separation from every other improved eligible map before selecting one uniquely.

Coverage passes, with three usable patches and seven groups. The remaining conditions were not changed after measuring the new notes.

## Held-out results

All seven primary 24 ms measurements pass the fixed contrast/crossing test. Every 12 ms Vibraphone measurement fails contrast; all those early false crossings remain in the JSON. The corresponding 48 ms observations pass. Maximum primary-versus 48 ms half-crossing difference is 3.78 ms. Jazz Guitar's early transitions remain early with all three window lengths, so that sign reversal is not a short-window accident.

| Candidate | Equal-patch median-absolute error | Reduction vs unchanged | Largest patch worsening |
|---|---:|---:|---:|
| Unchanged |48.819 ms|—|—|
| Old scale + offset |40.245 ms|17.56%|42.107 ms|
| Nominal scale 1 |42.171 ms|13.62%|40.088 ms|
| Robust affine |40.404 ms|17.24%|39.969 ms|

These are the stated timing errors on seven validation groups, not whole-performance errors or hardware-accuracy percentages. All corrections improve the average numerically, but every reduction is below 20%, and every correction substantially worsens Jazz Guitar. None satisfies the frozen acceptance test.

Signed median residuals show the conflict:

| Validation patch | Unchanged | Old scale + offset | Nominal scale 1 | Robust affine |
|---|---:|---:|---:|---:|
|52 Jazz Guitar|-61.889 ms|-103.997 ms|-101.977 ms|-101.859 ms|
|91 Vibraphone|+40.372 ms|-1.735 ms|-12.934 ms|-10.556 ms|
|98 Music Box|+44.195 ms|+2.088 ms|-11.601 ms|-8.798 ms|

A signed median is different from a median absolute error when residuals straddle zero; the JSON preserves both. For example, the offset map's Vibraphone signed median is -1.735 ms, but its median absolute error is 10.649 ms.

The offset and robust maps differ by only 0.159 ms in primary score. All three corrected scores span just 1.925 ms, within the declared 3 ms uniqueness margin. They therefore remain a near-equivalent predictive family for sensitivity analysis, rather than identifying one exact mapping. This observation does not waive their failed 20% and per-patch-regression gates. The old map is also visibly imperfect; leaving it unchanged is preservation of a frozen comparison protocol, not evidence that it is physically correct.

## Timing and measurement limits

The Jazz Guitar observations are consistent with the old chroma audit's negative local residual around 90 s; the newly measured steps were not selected from that chroma score. The known MIDI file has one constant tempo, duplicated at tick 0 in its two tracks, and no listed controller events. That file does not reveal the real sender's scheduling, articulation or transformations, nor prove that every delivered gate matches its event list.

Carrier AR63 constrains the intended attack, but frequency-selective observations include output/capture latency, key scaling, modulation, prior voices, Chorus and possible harmonic overlap. The selected validation patches are not a continuous grid through the performance. Time and patch identity remain partly confounded. The clean early Jazz Guitar steps oppose a simple globally late-onset story; the more contaminated Vibraphone cases warrant the retained window diagnostics. No actual MIDI-edge log or sample-accurate program command was recovered.

The appropriate downstream use is to keep these fixed maps as labeled timing-sensitivity conditions when checking an envelope conclusion, without choosing a local shift to improve a synthesis metric. An exact replacement alignment still needs stronger dense event evidence or direct sender/MIDI timestamps. This experiment does not justify changing release constants, defining chip latency from the fitted intercept, or treating scale 1 as a measured oscillator clock.

## Reproduction and verification

`Tools/audit_global_event_mapping.py` separates `freeze` from `measure`, refuses to overwrite completed artifacts and verifies all frozen input hashes before reading the validation audio. Use a new output directory:

```sh
python3 Tools/audit_global_event_mapping.py freeze \
  --reference-root /path/to/original/pss780-experiment \
  --output build/global-event-mapping-new-run
python3 Tools/audit_global_event_mapping.py measure \
  --output build/global-event-mapping-new-run
```

The preserved run is `build/global-event-mapping-20261019`. Its result SHA256 is `96d43f3772eb72a787139df8a482719da305bb9db48f37d3d461e96de810ccd0`. An independent scalar/statistics verification recomputes every map coefficient and equal-patch score, checks every source hash and confirms all corrected maps fail the frozen adoption rules while remaining within the 3 ms score margin. Protocol, tool snapshot, result, source hashes, validation receipt and both plots are retained. Audio was read in place and is not distributed with the product.
