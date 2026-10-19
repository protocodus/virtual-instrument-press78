# OPU frequency-law candidate, 19 October 2026

One fixed frequency law explains the independent PSS-680 samples much better than ideal equal temperament and also reduces errors in the older PSS-780 measurements. This supports a **behavioral oscillator-frequency candidate**, not a recovered YM3420 accumulator, divider or firmware note table. Production DSP, presets, host state and noise remain unchanged.

The candidate was proposed after seeing four pitch classes and their octave behavior. It is a posthoc explanation with subsequently frozen full-data scoring, **not a fresh holdout result**. The unused D and A-flat table entries face additional constraints from reused PSS-780 data; those measurements were also previously reported. Every measurement and outlier is retained in the accompanying JSON.

## Fixed mechanism and complete table

For integer musical MIDI note `n`, let `c=n%12` and `o=floor((n-60)/12)`:

```text
base[c] = round(Hz_equal_tempered(60+c) * 2^24 / 5,500,000)
word[n] = floor(6 * base[c] * 2^o)
Hz[n]   = 5,500,000 / (6 * 2^24) * word[n]
```

There are no fitted note-specific offsets. All twelve entries follow the same formula:

| Class | Base | Candidate frequency at MIDI60+class, Hz | Cents from equal temperament |
|---|---:|---:|---:|
|C|798|261.604785919|−0.137507|
|C♯|846|277.340412140|+0.985193|
|D|896|293.731689453|+0.394476|
|E♭|949|311.106443405|−0.114298|
|E|1005|329.464673996|−0.855687|
|F|1065|349.134206772|−0.466173|
|F♯|1129|370.115041733|+0.564294|
|G|1196|392.079353333|+0.370578|
|A♭|1267|415.354967117|+0.209540|
|A|1342|439.941883087|−0.228683|
|B♭|1422|466.167926788|+0.015469|
|B|1507|494.033098221|+0.525011|

The characteristic low E-flat result comes from `word[39]=floor(5694/4)=1423`, whereas `word[51]=2847`. Thus 39→51 exceeds an exact octave by **0.608197459 cents**. The sampled C/G/B-flat classes have exact octave replication over36–96. Fixed interval predictions include67→75=−0.484876612 cents,75→79=+0.484876612 cents and39→79=+1.093074071 cents relative to equal-tempered intervals.

The [manufacturer-drawing audit](opu-sibling-clock-circuit-20261019.md) verifies a nominal5.5MHz crystal at PSS-480 YM3420BF oscillator pins and a nominal5.5MHz ceramic resonator in the PSS-780 parts list. It does **not** document the factor6, a24-bit phase register, the rounding order, an FM sample clock or a DAC cadence. Those are not established by this fit. Equivalent scalings of a frequency word and its timebase can produce identical frequencies; `word` here is a mathematical coordinate. The frozen engine's48kHz simulation rate remains a separate numerical choice.

## Independent-source PSS-680 evaluation

The [source audit](isolated-source-search-20261019.md) supplies63 original-author sample interiors, of which62 qualify under its existing estimator-agreement rule. The sole rejected Chiptune endpoint is preserved, including its octave-detection failure; it is not relabeled or included in the score. The source is Jon Jungle's [PSS680 sample packs](https://www.pss680.com/samplepacks.php). Three packs may share one physical unit and capture chain, so they are not three independent hardware replicates.

For each pack, each model receives **one common log-frequency offset**: the median of the per-note mean FFT/phase errors across all source-qualified rows. Both estimators then use that same offset. There is no per-note adjustment, trimming, changed qualification or selected estimator. The equal-tempered comparator receives the same number of nuisance parameters.

| All62 qualified notes | Equal-tempered RMS, cents | Candidate RMS | Candidate maximum absolute error |
|---|---:|---:|---:|
|Hann/partial estimator|0.274009|0.002970|0.009983|
|Independent phase estimator|0.274505|0.002947|0.008508|

The candidate's descriptive common ratios are−127.968ppm for Chiptune,−150.017ppm for Saw Synth and−159.738ppm for Synth Bass. These combine instrument tuning, capture-clock error and possible upstream resampling. They are **not measured crystal offsets** and should not become product defaults. Their differences also rule out reporting a single measured−150ppm value for all three files.

This agreement is strong evidence against ideal equal temperament as a complete description of these samples. It remains conditional on inferred musical labels, unknown upstream editing and the four available classes. Those same classes and their octave feature helped generate the hypothesis, so the exceptionally small residual is a descriptive fit, not independent proof of its internal mechanism.

## Old PSS-780 data, with only G calibration

The [existing pitch-grid audit](pitch-grid-audit-20261019.md) supplies the unchanged19 original windows. For each model, only the two long G67 Opus-mid-phase12 observations, event IDs1760 and1770, set one shared offset. That offset is applied unchanged to all notes, methods, channels and encodes. The candidate offset is−1.852739 cents versus−1.482161 cents for equal temperament; these are capture/tuning nuisances, not isolated master-clock measurements.

| Opus arithmetic-mid phase12 set | Equal-tempered RMS, cents | Candidate RMS | Candidate maximum absolute error |
|---|---:|---:|---:|
|All19 original windows|0.314729|0.041035|0.107100|
|17 noncalibration windows|0.332728|0.043379|0.107100|
|Five D62/A♭68 windows, unfitted classes|0.127972|0.052913|0.107100|

The benefit is not confined to one estimator. Using the same two-anchor offset, AAC-mid RMS falls from0.311589 to0.033271 cents for phase12 and from0.316450 to0.046548 cents for Hann. Every one of the five existing mid estimators improves its all19 RMS in both encodes. The encodes share an upload master and are not independent hardware captures. All left/right measurements and the original control outputs remain in the JSON; none was used to refit the offset.

D62 is the weaker cross-class result: its two phase12 residuals are−0.010613 and+0.107100 cents. A-flat68's three are−0.008267,+0.009376,+0.047537 cents. Other preserved primary residuals exceeding0.05 cents are short G67 at+0.053568 and E-flat87 at+0.087468. These short/polyphonic/effect windows are not all precision-qualified by the later, stricter pattern audit; the table is a transparent descriptive comparison, not a replacement for its gates.

An additional retained constraint deserves caution. The [broader pattern audit](pitch-pattern-audit-20261019.md) found a conditional56→62 phase6 contrast of+0.2965…+0.3410 cents; this law predicts+0.184936 cents. That difference of about0.112…0.156 cents is not silently fitted away. The same audit's conditional68→72 contrasts of−0.4563…−0.2888 cents bracket the predicted−0.347048 cents. These reused, single-family constraints neither establish exact reproduction nor negate the much stronger all-sample pattern; they are useful targets for an isolated cross-class recording.

The separately frozen [PSS-780 final-tail cross-source test](cross-source-pitch-prediction-20261019.md) also supports the sign and approximate scale of the G/E-flat and low-E-flat features. Its low-note intervals sit somewhat below the central producer prediction and only pass within that test's declared0.10-cent envelope. This candidate was not retuned to those measurements.

## Implementation boundary and falsifiable next checks

The ignored `build/opu-frequency-hypothesis-20261019/FrequencyHypothesis.h` implements the formula with integer shifts and no allocation, randomness, mutable table or render-time fitting. Its405 analytic C++ checks cover all128 MIDI notes, integer-versus-floating formula agreement, monotonicity, clamping and the stated octave predictions. Python independently verifies all128 emitted words/frequencies exactly. These validate software arithmetic, not hardware identity. The complete frozen protocol, source hashes, row ledger, compiler probe and residual figure remain beside it.

A bounded integration would add an explicit selectable frequency law, with current equal temperament as the compatibility setting, and use this helper only for the integer note's base frequency. Operator ratios, detune and expressive pitch controls would initially keep their current laws and be identified as unverified composition choices. The existing clock control must scale the result once, rather than recalculate the rounded seeds or add a second clock correction. No precision reduction, DAC quantization, envelope change, noise or aging fault follows from this evidence.

Documented `c.00` MIDI reception36–96 is not proof that the internal oscillator is restricted to that range. Producer coverage is36–96 in four classes; the old qualified roots add limited D/A-flat information. The complete twelve-class law, detuned/operator-multiplied cases, and the helper's0–35/97–127 extrapolation are not verified. Lower-range truncation becomes relatively larger. Do not silently clamp the plugin's musical range or present these extrapolations as factory behavior.

The highest-value separating capture is an effects-off, isolated chromatic sequence across several octaves, especially C♯/E/F/F♯/A/B, then fine-detune and nonunit-operator-ratio pairs. A common capture-clock offset can be eliminated by interval ratios. The current law predicts those classes in advance; a systematic mismatch should reject or revise it under a new protocol, not prompt twelve arbitrary corrections.

Production integration is therefore **recommended for an explicitly labeled behavioral candidate after review**, while “exact OPU frequency arithmetic recovered” is not supported. All model constants in this pass stayed frozen, and no production file was modified.
