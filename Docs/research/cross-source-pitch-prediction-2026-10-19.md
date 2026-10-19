# Cross-source long-tail pitch prediction — 19 October 2026

A separately frozen prediction from three author-provided PSS-680 WAV packs is compatible with the exact PSS-780 tour's final Sine99 tail under the declared **producer range ±0.10-cent tolerance**. The upper 75→79 contrast agrees tightly, near +0.485 cents beyond its nominal interval. The two contrasts involving low MIDI 39 are systematically 0.04–0.10 cents below the pack centers and pass only the expanded tolerance; they do not reproduce the packs' narrow unexpanded ranges.

Each pair passes the frozen rule through qualified 12 Hz phase endpoints plus Hann/Blackman spectral methods in arithmetic mid. Two 6 Hz comparisons fail their hypothetical-native control gate and remain excluded. These are conditional **captured-component frequency constraints**, not identified chip arithmetic, exact clock, FNUM width or a recovered note table. No production tuning change is adopted.

The [complete ledger](cross-source-pitch-prediction-2026-10-19.json) retains every source/control/channel result, disqualification and prediction residual. No production, preset, prior pitch artifact, score, alignment, native package, host or git state changed. No media was acquired or artificial noise added by this pass.

## Independent source prediction

The [producer's frozen inventory](isolated-source-search-2026-10-19.md) analyzes the three continuous WAV packs linked by [Jon Jungle's original PSS-680 sample page](https://www.pss680.com/samplepacks.php): Saw Synth, Chiptune Esq and Synth Bass1. These were analyzed directly at their original 44.1 kHz rate without a sampler or transposition. The author describes ascending C/E♭/G/B♭ notes, and matching [front-panel recipes](https://www.pss680.com/patches.php) use base voice 99 with carrier multiplier1. Musical MIDI/octave labels are inferred from that sequence and the measured frequencies; there is no recorded MIDI/root-key metadata or proof of the exact recorded raw patch/effect state.

The producer retains all 63 notes and accepts 62 conditional stationary-pitch references. Its sole rejected Chiptune C7 detector ambiguity lies outside the pitches used here. All 39/75/79 rows in all three files qualify under both supplied estimators: Hann dominant-partial frequency divided by an ACF-derived harmonic number, and a separate bandpass/Hilbert phase regression on the same frozen note interiors. The producer supplied a measurement-READY receipt before these values were used.

Three files from one author are not three independent hardware units. Original tuning, effects, sample-rate calibration, editing/retuning and shared capture chain remain undocumented. Their relative ratios cancel one uniform clock/tuning multiplier, but they cannot prove silicon origin or rule out upstream note-dependent processing. No source audio is redistributed or imported into product resources.

Predictions use all matched **same-pack, same-estimator** low/high frequency tuples. All three packs and both estimators contribute to every pair. The descriptive center is the median of within-pack two-method medians, giving equal pack weight. The acceptance envelope uses the full six-value range expanded by the **0.10 cents declared before reading these predictions**. No estimator or pack was selected to match the PSS-780.

| Captured-component interval | Nominal interval | Equal-pack prediction, cents excess | Full producer range | Frozen expanded envelope |
|---|---:|---:|---:|---:|
|39→75|3600 cents|+0.609311|+0.603429…+0.615193|+0.503429…+0.715193|
|75→79|400 cents|+0.484608|+0.481633…+0.486273|+0.381633…+0.586273|
|39→79|4000 cents|+1.093919|+1.087932…+1.099906|+0.987932…+1.199906|

All expanded envelopes exclude equal-tempered zero. The three contrasts are algebraically dependent: the first two sum to the third. They supply only two independent interval constraints, not three independent replications.

## Target and methods frozen before extraction

The [exact PSS-780 tour](https://www.youtube.com/watch?v=ONfIvtDOog0) target starts at the continuous old mapped final off, 182.178989328624 s, plus 0.20 s. Its fixed window is **182.378989328624–183.426497213754 s**, lasting exactly `1 / 0.9546467517767424 = 1.0475078851301263 s`. This is one assumed RecordedChorus period, chosen before any new tail frequency measurement. The rounded benchmark off is 182.178979166667 s, about 10.2 microseconds earlier; their frame conventions are not silently equated or realigned.

This is a new cross-source prediction on already reused PSS-780 audio, not a fresh exact-device recording. It does not revise the [failed short/lower-note pattern experiment](pitch-pattern-audit-2026-10-19.md), its gates or its results. Prior endpoint observations place 39/75/79 extinction after this window; 87 is measured only as a nuisance component.

The design froze first, before producer READY, with SHA256 `6664159f147397545c5f97c705375c053e8222c75ba3e27d9d4ab22e6b461920`. After READY, the producer hashes, matched predictions and operational rules were bound in a final protocol, SHA256 `9cd0586e288a666d672d5e068090257a475b2f8848c9f632cbd160f838634a8c`. No window, method or threshold changed between those stages.

Four estimators run on mid, left and right for PCM16, float Opus 251, float AAC 140 and a hypothetical finite-tail DSP control:

- Fixed 6/12 Hz fourth-order zero-phase complex demodulation at nominal MIDI centers, with actual 0.5 s context on each side. Full-rate unwrapped phase is linearly interpolated at the exact endpoints; frequency comes from endpoint phase change. There is no OLS phase-slope fit or new frequency/time alignment.
- Hann and Blackman full-window spectral energy peaks, each with at least 16× zero padding, the same nominal ±75-cent search and bounded refinement within two FFT bins. Boundary failures would remain in the result.

AAC drops exactly the existing 627-frame encoding lag. The research control drops only its declared 32-frame latency. No input normalization or gain correction is applied; spectral-objective scaling changes numerical precision only.

One full assumed period can cancel strictly periodic phase under stable conditions. It does not establish the actual analog wet period or guarantee cancellation when old voices, envelopes, interference and wet/dry proportions change. Full-window spectral methods also weight the decaying amplitude and therefore need not cancel periodic phase like endpoints do.

## Fixed controls and gates

Eight clean analytical multitone controls cross stationary/exponential envelopes, common offsets 0/−2 cents and two fixed initial-phase patterns. They contain MIDI 39/46/58/59/67/75/79/87 at amplitude 0.02 per tone at the old off. Exponential slopes are fixed −14 dB/s, except 87 at −18 dB/s, continuing through the full context without gates or noise. Frequencies are known exactly and all interval errors are zero even with a common−2-cent shift.

The unchanged [RR×3 plus carrier-trigger Reverb research render](reverb-envelope-benchmark-2026-10-18.md) supplies a separate equal-tempered finite-tail composition/effect control. It is a **hypothetical DSP control**, not a hardware reference or shipping implementation. Original b11 dies before the target and cannot qualify such a control. The earlier render is read without rebuilding or changing any parameter.

For each pair/estimator, all eight analytic controls and research-control **mid** must have absolute interval bias ≤0.05 cents. Captured Opus/AAC mid must then both be valid, pass the fixed quiet checks and agree within 0.05 cents. At least one endpoint and one spectral method must qualify, and every qualified method in both encodes must fall inside the frozen prediction envelope. No qualified failure is averaged away. Support is per pair; no new overall-success criterion was invented after seeing results.

Quiet checks require the minimum demodulated amplitude to remain at least 0.2 times its window median and 20 dB above the same-filter empirical floor at old off+[2.2,2.8] s. Spectral methods use phase12 amplitude diagnostics. That post-extinction floor is an empirical reference, not proof of stationary noise; continuing real signal there could make a quiet failure inconclusive. It is not applied to the research model, whose hypothetical tail still exists in that later interval.

## Results and preserved failures

All primary captured-mid components pass the quiet checks. Their minimum level is at least 42.90 dB above the empirical floor and no lower than −7.82 dB relative to its window median. Numerical outputs are finite; no nominal search-boundary failure occurs.

| Pair | Method | Opus-mid error, cents | AAC-mid error | Gate outcome |
|---|---|---:|---:|---|
|39→75|6 Hz endpoints|+0.485487|+0.530082|**Excluded: native-control bias**|
|39→75|12 Hz endpoints|+0.530466|+0.513256|Qualified; expanded prediction passes|
|39→75|Hann|+0.566724|+0.545565|Qualified; expanded prediction passes|
|39→75|Blackman|+0.550864|+0.528903|Qualified; expanded prediction passes|
|75→79|6 Hz endpoints|+0.484740|+0.481130|Qualified; prediction passes|
|75→79|12 Hz endpoints|+0.489551|+0.484250|Qualified; prediction passes|
|75→79|Hann|+0.483257|+0.480921|Qualified; prediction passes|
|75→79|Blackman|+0.479655|+0.477385|Qualified; prediction passes|
|39→79|6 Hz endpoints|+0.970227|+1.011212|**Excluded: native-control bias**|
|39→79|12 Hz endpoints|+1.020018|+0.997506|Qualified; expanded prediction passes|
|39→79|Hann|+1.049981|+1.026486|Qualified; expanded prediction passes|
|39→79|Blackman|+1.030519|+1.006288|Qualified; expanded prediction passes|

The 6 Hz research-control biases are +0.063008 cents for 39→75 and +0.066126 for 39→79, above the predeclared 0.05 limit. Those methods would also miss one prediction endpoint; they are fully retained and excluded by the control rule established before target extraction. Their threshold was not relaxed. The other ten pair/method cells pass control, quiet and codec gates. The largest qualified control bias is about 0.003118 cents, from the remaining 6 Hz comparison; for 12 Hz/Hann/Blackman it is at most 0.000914. Captured AAC/Opus disagreement remains at most 0.024231 cents among qualified cells.

The upper contrast residual from its pack center is only about−0.0072 to+0.0049 cents. In contrast, qualified39→75 residuals are roughly−0.0961 to−0.0426 cents, and39→79 roughly−0.0964 to−0.0439. Their unexpanded producer ranges do not overlap these PSS-780 values. The AAC phase12 points sit only about 0.0098/0.0096 cents inside their lower expanded bounds. Therefore the accepted result is **conditional envelope compatibility with a systematic bass-related mismatch**, not exact cross-unit pitch-law replication.

## Channels, harmonic identity and source mode

Acceptance is specifically for the frozen arithmetic mid. Individual channels do not give a uniformly matching story. For example, phase12 left 39→75 is +0.4246…+0.4568 cents, while right is +0.6776…+0.6804. Hann left gives approximately +1.72 cents and right a negative value. All right-channel pair comparisons fail at least one component's quiet gate. These retained observations show that wet-path cancellation and interference remain consequential even over the assumed full period.

MIDI 39→75 spans exactly three octaves: the75 component can contain39's eighth harmonic. Likewise79 can contain the second harmonic of an earlier67 voice. Pure-tone controls and a correct research render cannot uniquely identify which hardware voice generated a component. Old same-pitch releases, changing mixtures, analog Chorus and unknown capture processing remain possible contributors. The three PSS-680 packs may share a unit/chain; the two YouTube encodes share one master. These are consistency checks across sources and methods, not independent silicon replications.

The [recorded-mode/effect audit](recording-mode-effects-audit-2026-10-19.md) and [separate Mode00 benchmark](mode00-benchmark-2026-10-19.md) provide context for the earlier MIDI 34 failure: the sampled `c.00` display and manual restricted receive range 36–96 can explain why that expected low component was not identified, under the published-MIDI/no-upstream-remap assumptions. There is no MIDI wire log or continuous mode trace. This is **not a frequency correction**; this test uses only 39/75/79, leaves all prior pitch measurements untouched and preserves the native instrument's extended playing range.

## Verification and use of the constraint

The result has 80 note/source/channel rows, 320 frequency estimates, 240 pair rows and 12 gate decisions. A separate arithmetic/provenance checker recomputes all 18 producer interval tuples, all pair metrics, all gates and 80 algebraic identities; source hashes remain unchanged. The [reusable tool](../../Tools/audit_cross_source_pitch.py) reproduces every numerical output bit-identically into a new directory. This is independent arithmetic plus reproduction of the same signal estimator, not independently implemented filtering.

```sh
OPENBLAS_NUM_THREADS=1 python3 Tools/audit_cross_source_pitch.py \
  --protocol build/cross-source-pitch-prediction-20261019/protocol-frozen.json \
  --out build/cross-source-pitch-reproduction-new
```

Ignored artifacts under `build/cross-source-pitch-prediction-20261019` contain both freezes, producer bindings, scripts, results, tool reproduction, validation and two inspected plots. The result SHA256 is `a2d529a79a5c9e66a769ba7f311315c8b84dbe3908623d4a2a845de2301e21fd`. No source recording is distributed.

The useful engine constraint is now stronger than a common captured tuning offset: the upper G-versus-E♭ ratio repeats across the independently hosted source packs and exact-device tour, while a positive low-E♭ octave excess has approximate cross-source support with a visible mismatch. Any proposed global pitch-generation hypothesis should predict these ratios, their residuals and failed controls without a per-note lookup fitted to this audio. Controlled effects-off notes and nonharmonic simultaneous pairs are still needed to localize that pattern to the oscillator and recover its law.
