# Bass decay at matched captured levels — 19 October 2026

The previously observed low/high pitch difference persists when the saved
fundamental curves traverse the **same captured level range**. Across all 64
low/high pitch pairs, the high group passes −22→−26 dBFS sooner, with at least
**220/44100 seconds (4.989 ms)** separation between the conservative crossing-time
intervals. This is a new constraint on the saved fitted-H1 curves. It does
**not** establish a hardware rate-key-scaling law or justify a new envelope
constant.

All source hashes, frozen designs, failures and results are recorded in the
[JSON audit](bass-matched-level-decay-2026-10-19.json) and
[reproduction notes](../../Tools/prototypes/bass-matched-level-decay-20261019/README.md).
The analysis runners read existing JSON and provenance text only. Independent
review checked the retained WAV header and hash without decoding samples. No
PCM samples were decoded/analyzed or generated, no PM method was run, and no
production DSP, default, preset or host changed.

## Restricted hypothesis and retained source limits

The 16 curves are the already accepted late Synth Bass 1 fundamentals in
[the independent envelope-source audit](opu-envelope-independent-2026-10-19.md):
eight inferred pitches 36–58 and eight 60–82, one author's PSS-680 sample file.
They contain 81 saved amplitude measurements at nominal 5 ms spacing. Prior
analysis knew their whole-window slope grouping. This is a posthoc fixed-data
diagnostic, not a new source or untouched holdout.

The hypothesis under test is deliberately narrow: each intrinsic fundamental
level is `x_i(t)=a_i-r*t`, with the **same constant** positive dB decay rate `r`;
each observed fundamental is `y_i(t)=G(x_i(t))`, with the **same** time-invariant,
strictly increasing continuous scalar mapping `G`.

At an output level `L`, every note reaches `x=G^-1(L)`. Where `G` is
differentiable, its continuous local rate is `-r*G'(G^-1(L))`, independent of
starting level. More strongly,
the traversal time from higher output level `H` to lower `L` is
`[G^-1(H)-G^-1(L)]/r`, independent of starting level and of the mapping's
curvature. These are mathematical consequences of that scalar-H1 hypothesis.
They are **not** a description of all memoryless audio distortion: changing
FM/timbre can prevent H1 amplitude from following one common scalar map.

Unknown per-note normalization, frequency-dependent gain after nonlinear
processing, compression dynamics, filtering, actual patch/gates/effect history
and the relation between H1 amplitude and carrier-envelope level remain
alternative explanations. No new inference removes those limits.

## Original local-slope diagnostic and its limitation

Before extraction, the first design fixed all 16 curves, levels −26,−25,−24,−23,
−22 dBFS and a crossing-relative ±25 ms neighborhood. Every crossing had to be
unique/downward with full support; no curve was repaired or time-adjusted.
Ordinary regression at 11 fixed interpolated offsets gives:

| Captured level | Low-group median, dB/s | High-group median, dB/s |
|---|---:|---:|
|−26 dBFS|−23.997|−27.533|
|−25 dBFS|−24.131|−27.975|
|−24 dBFS|−24.708|−28.126|
|−23 dBFS|−25.211|−28.986|
|−22 dBFS|−24.798|−28.938|

All 80 neighborhoods qualify under the declared structural/support rules. All
320 level-specific low/high contrasts have faster high-pitch decline, by
3.132–5.685 dB/s; speed ratios are 1.126–1.243. Local fit R² is at least 0.99984,
with maximum residual 0.01022 dB. These are descriptive overlapping estimates,
not independent statistical observations.

All 240 declared common-map controls and 80 separating-rate controls pass;
maximum sampled-versus-analytic finite-window slope error is 0.00531 dB/s for
those fixtures. **This does not bound error for arbitrary differentiable
monotonic mappings.** Independent review supplied a sharply curved monotonic
counterexample with a larger interpolated-slope spread despite equal intrinsic
rates. Accordingly, these interpolated local slopes alone do not rigorously
reject every possible `G`. The original protocol/result remain unchanged.

## Separate traversal experiment and numerical correction

After that review, a new prospective design fixed **all 10 pairs** of the same
five output levels and all 64 cross-group note pairs. For each original
crossing, the adjacent saved samples enclose its time; no interpolated crossing
or derivative is needed. If higher-level time lies in `[h0,h1]` and lower-level
time in `[l0,l1]`, traversal lies in `[max(0,l0-h1), l1-h0]`. The derivation and
qualification rules were independently reviewed before execution. All 16 saved
curves are strictly decreasing; all 160 traversal enclosures qualify.

The first implementation subtracted absolute JSON floating timestamps. This
created some approximately 10⁻¹⁵ second nominal separations and is retained as a
**numerical-comparison failure**, not physical evidence. A separately frozen
correction followed the original extractor's actual rule:
`np.rint(saved_times * 44100)`. Retained source/header/protocol hashes and an
independent reviewer verify 44.1 kHz and all 1,296 measurement centers. Their 1,280
hops comprise 640 of 220 samples and 640 of 221 samples; physical hop length is
not exactly 5 ms. Nominal labels differ from rounded centers by at most 11.338 µs.

The corrected runner uses integer center differences and denominator 44,100 for
every duration, intersection and comparison. It changes no H1 value, level,
crossing sample position or qualification. All 74 v1→v2 classification changes
are preserved; no empirical epsilon or separation threshold was fitted.

| Higher→lower captured level | High group shorter, of 64 | Overlapping intervals | All 16 common-intersection gap, samples / 44100 |
|---|---:|---:|---:|
|−25→−26|0|64|0, intersection exists|
|−24→−26|27|37|221|
|−23→−26|60|4|441|
|−22→−26|64|0|662|
|−24→−25|2|62|1|
|−23→−25|32|32|221|
|−22→−25|64|0|442|
|−23→−24|0|64|0, intersection exists|
|−22→−24|24|40|221|
|−22→−23|1|63|1|

No comparison has a strictly longer high-group interval. At the full 4 dB span,
the **minimum across 64 cross-group separation margins is 220 samples
(4.989 ms)**. The 662 sample gap (**15.011 ms**) in the all 16 intersection is a
different quantity: maximum lower endpoint minus minimum upper endpoint. It
does not apply to every note pair. The one-sample entries in the table should
not be treated as meaningful hardware precision.

All 640 synthetic duration enclosures contain their known common duration and
all 2,560 shared-map cross-group comparisons overlap, including the sharply
curved review counterexample. Six crossing/ambiguity edge controls pass.
These controls verify enclosure arithmetic under the stipulated curve model.

## What this changes

Identical intrinsic constant H1 dB decline passed through one common scalar map
cannot reproduce the **corrected saved-curve traversal intervals** under the
stipulated continuous-monotonic, error-free-H1 interpretation. Unlike the first
derivative diagnostic, this conditional duration statement does not need a
curvature bound. It weakens one specific explanation of the captured
pitch-group difference; it does not decide its physical source.

The time brackets **do not bound error in the fitted H1 magnitudes**, estimator
smoothing, capture chain or hardware measurement. Notes and level pairs share
one recording and overlapping analysis supports. No p-values, independent-unit
replication or new timing multiplier follow. In particular, the inherited
nonzero level-key-scaling, undocumented processing and unknown Reverb history
remain relevant. The [firmware command audit](opu-envelope-command-audit-2026-10-19.md)
shows that raw rate/RKS commands are forwarded unchanged, but does not identify
the chip's internal response. No production correction is adopted here.
