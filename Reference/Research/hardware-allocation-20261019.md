# Original allocation: fixed recording comparison, 2026-10-19

The command-accurate native allocator **fails its frozen audio-promotion gates**. It substantially reduces Bowed Bass's joint-band error, but slightly worsens the all-voice mean and regresses the short Sine99 diagnostic on every timing map. Shipping b15 remains unchanged. The tested code is preserved as an [applicable research patch](../Prototypes/original-allocation-20261019/README.md), rather than retuned or discarded.

## Comparison and controls

The [frozen v3 protocol](allocator-recording-protocol-20261019.json) fixes four existing event maps, all 100 voice windows and two previously selected Sine99 supports. Three lanes distinguish the historical raw-MIDI-channel owner tags, merged-MIDI Legacy, and merged-MIDI Original. [Original CPU witnesses](opu-mode00-midi-ownership-20261019.md) support the shared MIDI domain, conditional on actual reception; normal plugin MIDI/CV inputs remain separate.

The earlier [recording-state audit](recording-mode-effects-audit-20261019.md) supplies direct sampled support for Keyboard Assign `c.00`: it is visible at 300 preset snapshots and six later Sine99 frames. Reverb and Chorus are on at every sampled preset; the six later Sine99 snapshots also show them on. This is stronger than guessing a mode from MIDI channel count, while continuous state, receive masks, actual sender delivery and arrival order remain unverified. The missing chip-Reverb envelope behavior is therefore a known model gap in this reference, rather than an unidentified switch position.

All four Historical Legacy WAVs match their retained complete hashes. All four merged Legacy WAVs match separately compiled unchanged b15 baselines. The candidate's default and explicit Legacy branches had already matched 330 controlled cases / 9,392,040 bytes per stream, with another independent 108-case / 4,808,592-byte proof. Thus Original-minus-merged-Legacy isolates the allocation-policy change in this renderer. The source-mapping correction is reported separately; its all-voice metric differences here are about `10^-11` dB, not evidence of general routing equivalence.

The existing envelope, phase configure, immediate key delivery, 48-tick steal fade, pitch, operator levels, analog path and Recorded chorus remain unchanged. No EQ, pitch, timing, phase, channel gain or model constant is fitted. Scoring uses the frozen stereo-pair RMS normalization; audition clips use the declared pair gains and common safety. No artificial noise is introduced.

## Results

These are **Original minus merged Legacy** errors; negative is better. They describe reused recording comparisons, not accuracy percentages.

| Fixed timing scenario | All100 joint-band error delta | All100 log-STFT error delta |
| --- | ---: | ---: |
| Unchanged | +0.024105 dB | +0.021489 dB |
| Old scale, median offset | +0.015124 dB | +0.023849 dB |
| Nominal scale, median intercept | +0.008222 dB | +0.020963 dB |
| Equal-patch affine | +0.023091 dB | +0.022053 dB |

The unchanged-map all-voice joint-band mean moves from 3.143844 to 3.167949 dB. The required improvement of at least 0.01 dB is not achieved. Band-error regressions occur on 51, 48, 45 and 43 of the 100 voice supports respectively; the full signed differences remain in the [machine-readable report](hardware-allocation-20261019.json).

| Target | Joint-band delta across four maps | Log-STFT delta across four maps |
| --- | ---: | ---: |
| Bowed Bass | −1.732287 to −1.482770 dB | −0.054408 to −0.037466 dB |
| Human Voice 1 | −0.000044 to −0.000014 dB | Approximately 0 to +0.000002 dB |
| Musical Saw | −0.226647 to −0.029562 dB | +0.176630 to +0.210202 dB |

Bowed Bass improves on both listed metrics. Musical Saw's spectral distribution improves while its time-frequency error worsens. Human Voice 1 is essentially unchanged; this experiment does not resolve its release discrepancy. The focus-band regression gate and all-voice STFT bound pass, but that does not override the other failed gates.

The short Sine99 support, 181.55–182.20 s, regresses by **+0.929335, +2.170834, +0.506250 and +0.613211 dB** respectively, exceeding the +0.1 dB bound on every map. The full 176.1–184.2 s support also exceeds that bound on the old-scale/median-offset scenario at +0.136208 dB. These supports are internal diagnostic IDs 199/200 in the data, not additional numbered factory presets.

## Event-order constraint and interpretation

A separate event-only analysis was frozen before recording scores. It finds 17/17/11/37 shared-key duplicate ons across the four maps. All but one per map are one-sample inferred overlaps; the sole longer overlap is approximately 0.441 s at voice 53, note 62. The three focus windows contain no duplicate ons, but each has seven command-cache reuses, including one from an earlier program. No command-held-slot replacement occurs in this trace. That does not measure pressure from audible release tails.

One-sample ordering can reverse whether Mode00 accepts a retrigger. Actual sender timing is unknown, so these inferred boundaries cannot prove physical behavior. However, nominal and affine Sine99 supports have no duplicate ons and still regress. **Coalescing uncertainty cannot uniquely explain the failure.** Retained-slot reuse also interacts with the renderer's existing phase, envelope and release-tail hypotheses. The CPU commands do not establish those chip behaviors, and this comparison cannot identify a replacement law.

In particular, removing stacked release voices could expose an envelope/Reverb mismatch that stacking had partly masked. That is a testable interpretation, not an established explanation of these scores. No slower-release or Reverb constant is selected from it.

The next investigation traces exact original MIDI ticks and message order through the note-pairing/frame exporter, without altering this completed experiment. Chip-phase, same-note retrigger and envelope measurements remain distinct requirements. A joint verified-command candidate may be studied separately; none is selected by these scores.

That [subsequent MIDI audit](midi-event-order-audit-20261019.md) now establishes the fixture artifact directly. The retained file has 193 same-channel contiguous retriggers with explicit OFF-before-ON order and no same-channel overlaps. Separate onset/gate rounding introduces 16/16/10/35 one-frame overlaps across the maps; pitch-sorted note lists also reverse 492 within-track chord ON/ON pairs in each map. All eight old event files reproduce exactly. The [independent validation](midi-event-order-validation-20261019.json) checks the raw file and metadata without rerendering or revising this completed experiment. A new fixture must preserve raw tick/message order rather than fitting boundaries to improve these scores; actual sender delivery remains unknown.

Four new metadata fixtures from the [reference-event exporter](midi-reference-export-20261019.md) have since passed 41,553 independent checks. They preserve source order and all contiguous boundaries while retaining the old onset times and inferred program rows. They have not been rendered in an audio comparison. The results and promotion failure in this report still refer exclusively to the original frozen fixtures.

## Reproducibility and decision

An independent audit passes 34,341 checks: all source/fixture and eight complete identity targets; 1,224 score objects, 3,264 deltas and 144 aggregate values; every gate/regression list; 30 fresh metric computations with zero difference; and 20 exact float32 four-part audition reconstructions. The reconstructed auditions are finite and stay at or below 0.900001 peak. New WAV storage peaks at 652,449,832 bytes, below the prospective 800 MB limit.

The [local audition page](../../build/allocator-recording-comparison-v3-20261019/audition.html) plays Hardware → Historical Legacy → Merged Legacy → Original for all three targets and both Sine supports on every timing scenario. WAVs and original media remain ignored research artifacts. The public report retains every score, adverse outcome, source binding and audition hash. The original source-policy v1 and optional-diagnostic/reporting v2 designs remain superseded pre-audio records; v3 changes no sound parameter or adoption limit.

The native component passes its command, allocation-safety, Legacy-identity and memory gates. The current audio embedding does **not** pass promotion. No production/native Rack/property/GUI/preset/version/default change follows. SDK target/host playback, persistence, measured chip behavior and fair market accuracy comparisons remain unproven by these component results.

A separate [paired native runtime probe](allocator-native-performance-20261019.md) passes its mean-time sanity limit but fails its zero wall-deadline requirement: 103 elapsed-time misses, zero paired thread-CPU misses. Its fixed 65-row run retains every block and makes no host-performance or speed-ranking claim. Functional/byte-identity passes must not be read as realtime acceptance.
