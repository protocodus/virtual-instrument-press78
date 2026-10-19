# Conditional command-path recording benchmark

The complete command path reduces mean band discrepancy on all eight fixed map/order conditions, but it does not resolve the hardware mismatch. Musical Saw's STFT-log error worsens in every condition, and the short repeated-Sine support has a substantial band regression. This remains an unpromoted research path. No production DSP, default preset, host, UI or SDK changed.

The single authorized run completed with exit 0: sixteen cells, all 1,632 complete score objects, empty stderr and no run failure. The [machine-readable report](command-recording-benchmark-2026-10-19.json) preserves every original score object, contrast, positive regression and source/result binding. Older failed [allocation comparisons](midi-fixture-comparison-2026-10-19.md) remain frozen independently.

## Complete mean results

A is the unchanged shipping Engine API. B is the [one-owner command consumer](command-audio-consumer-2026-10-19.md), with twelve fixed slots and the same shipping waveform/envelope/output helpers. Values are B minus A in the unchanged scorer's discrepancy metrics; negative means smaller discrepancy. STFT convergence is unitless. These are differences of error scores, not changes in physical output level or percentages of perceived fidelity.

| Fixed map / order | Band Δ, dB | Mid Δ, dB | STFT convergence Δ | STFT-log Δ, dB | Band regressions / 100 |
|---|---:|---:|---:|---:|---:|
| Unchanged / ascending | -0.151672 | -0.165009 | -0.004508 | +0.014373 | 42 |
| Unchanged / descending | -0.149567 | -0.162296 | -0.004484 | +0.014018 | 43 |
| Offset / ascending | -0.160387 | -0.178524 | -0.007368 | +0.010340 | 38 |
| Offset / descending | -0.155876 | -0.172957 | -0.007137 | +0.009866 | 39 |
| Nominal / ascending | -0.166736 | -0.184945 | -0.007505 | +0.011014 | 39 |
| Nominal / descending | -0.161350 | -0.178297 | -0.007274 | +0.010601 | 40 |
| Affine / ascending | -0.166422 | -0.184314 | -0.007499 | +0.010904 | 38 |
| Affine / descending | -0.161216 | -0.177894 | -0.007272 | +0.010393 | 39 |

Band, mid-band and convergence means improve under every declared condition; mean STFT-log discrepancy worsens under every condition. Between 38 and 43 of the original 100 voices have positive band regressions. The largest original-voice band regression is program 30 under nominal/descending, +0.744313 dB. Every smaller regression remains in JSON; none is removed by an epsilon or a favorable subset.

## Focus voices and Sine controls

Ranges span all eight fixed map/order conditions; no condition is selected as hardware truth.

| Fixed support | Band Δ range, dB | STFT-log Δ range, dB |
|---|---:|---:|
| Bowed Bass | -1.463463 to -1.256027 | -0.037804 to -0.016506 |
| Human Voice 1 | -0.119316 to +0.031449 | -0.046006 to -0.036457 |
| Musical Saw | -0.020392 to +0.102078 | +0.297130 to +0.315300 |
| Sine 99 original window | -0.333688 to -0.174045 | +0.051275 to +0.095985 |
| Sine 99 full ending | -0.345075 to -0.270554 | +0.037312 to +0.052856 |
| Sine 99 repeated 75 | +1.188261 to +2.128144 | +0.165234 to +0.250149 |

Bowed Bass improves band and STFT-log discrepancy in every condition, while its STFT convergence worsens. Human Voice 1 remains timing sensitive in band error, including a small regression under the unchanged map, although both STFT measures improve. Musical Saw is mixed in band error and consistently worse in STFT-log error. The longer Sine supports improve band error but worsen STFT-log error; the short repeated-75 support becomes substantially worse in both band and STFT-log error.

These differences compare bundled command policy, rather than isolating an envelope calibration. They do not identify whether a discrepancy comes from service timing, phase reset, envelope rates, live-register response, Reverb or the recording chain. No audible-law correction or default promotion is selected from these results.

## Level-matched listening copies

Only the predeclared unchanged/ascending condition has retained focus PCM. The following separate listening copies use exactly the pair-RMS gain and common per-support safety already stored by the completed run. There was no new gain fit, native/DSP replay or score recalculation. The original raw scoring clips remain unchanged. A separate [key](../../build/command-recording-benchmark-20261019/listening-01/key.md) records the mapping; no listener verdict is selected.

| Support | A | B |
|---|---|---|
| Bowed Bass | [A](../../build/command-recording-benchmark-20261019/listening-01/65/A.wav) | [B](../../build/command-recording-benchmark-20261019/listening-01/65/B.wav) |
| Human Voice 1 | [A](../../build/command-recording-benchmark-20261019/listening-01/93/A.wav) | [B](../../build/command-recording-benchmark-20261019/listening-01/93/B.wav) |
| Musical Saw | [A](../../build/command-recording-benchmark-20261019/listening-01/97/A.wav) | [B](../../build/command-recording-benchmark-20261019/listening-01/97/B.wav) |
| Sine 99 original window | [A](../../build/command-recording-benchmark-20261019/listening-01/99/A.wav) | [B](../../build/command-recording-benchmark-20261019/listening-01/99/B.wav) |
| Sine 99 full ending | [A](../../build/command-recording-benchmark-20261019/listening-01/199/A.wav) | [B](../../build/command-recording-benchmark-20261019/listening-01/199/B.wav) |
| Sine 99 repeated 75 | [A](../../build/command-recording-benchmark-20261019/listening-01/200/A.wav) | [B](../../build/command-recording-benchmark-20261019/listening-01/200/B.wav) |

The maximum relative A/B RMS difference after Float32 rounding is 1.17×10⁻¹⁰. Files are stereo Float32 WAV at 48 kHz. No original recording excerpt is exported in this set. These local research files are ignored and are not redistributed with the repository.

## Frozen source, ordering and control contract

The [protocol](../../Tools/prototypes/command-recording-benchmark-20261019/design-frozen.json) keeps all 100 original absolute supports plus both prior Sine diagnostics and the exact old scorer. It uses the same eight conditional [source-ordered fixtures](source-ordered-midi-2026-10-19.md): four fixed maps, each with ascending and descending track order. Both source channels stay in the JSON/input-index ledger and enter one `source=0` MIDI domain in both paths; channel 1 is not CV.

At an equal frame, a due vibrato-grid invocation runs first, then the complete fixture group in its existing program/tick/track/ordinal order, then exactly one key-service invocation. This includes patch-only and off-only groups. All source ticks collapsed onto one frame precede that one service. Audio block boundaries do not create services. The 240-frame grid starts at frame 240. Its 5 ms spacing inherits the shipping VDT interpretation of 10 ms per raw byte and the frontend's two invocations per raw byte; it is not recovered hardware scheduling.

A keeps shipping note stacking/oldest replacement and future-only program snapshots. B applies complete command plans, including live all-slot program reload, adjusted TL, paired key edges, RR and gated PMS. Both clock offset and drift are explicitly zero. A uses Original `pitchModel=1`/`sustainMode=1`; B internally uses `0/0` to avoid a second interpretation of already compiled pitch and RR. `volumeIndex=9`/addend 0 is a neutral fixture assumption, not observed Melody Volume 9. Fixed `masterGain=1` and metric/listening RMS matching are not a hardware level calibration.

Raw factory bytes are not reconstructed from a masked shipping Patch. A separate static original-loader/table review passes 4,824 checks across all 100 public voices and 20 retained loader cases. Raw33 byte 0 is SysEx bank metadata; loader fields 0–30 correspond to raw 1–31, field 23 receives separately addressed factory flags, and all 100 public raw 24 values match. The untouched working byte 31 is explicit zero research padding, not recovered hardware boot state. Original raw payload identity remains in the bound source ledger.

Reverb and Chorus are visibly ON in sampled capture frames. B explicitly selects `StoreReverbBitWithoutAudioEffect`; it stores the raw Reverb high bit without inventing its audio law. Both paths retain the existing recorded chorus. The comparison therefore cannot validate missing Reverb, envelope/DAC, phase-reset or cadence laws. Sender ordering, actual arrival times, program inference and receiver acceptance remain conditional.

## Verification and bounded retention

Audio-free preparation passes 2,116 checks and independent pre-execution review passes 174 checks. After the bound root gate, the synthetic chorus-epoch and sample-chunk contracts pass 2,104 checks. The independent post-run scalar/ledger review passes 7,031 checks across all 1,632 score objects and 350,204 command rows. Exactly twelve independent focused-PCM scorer calls pass 408 checks with maximum numeric difference 0. A separate independent listening-copy review passes 183 checks with zero differing samples against the declared stored-gain formula and no extra scorer calls. The full discarded performances do not receive an independent PCM-recalculation claim.

Only one own full Float32 scratch existed at a time. Every 102-support score set, hash/statistic, event/command ledger and checkpoint succeeded before its scratch was removed. Observed peak own-subtree usage was 97,296,930 bytes, below the 200 MiB cap. The separate listening copies add about 11 MB after scratch completion. No historical or user file was cleaned up. Full scratch SHA256 identities remain; exact focused raw PCM, separate listening PCM and all score objects remain available.

Root caught a source-length assumption before any retained replay or audio. Header-only inspection proves 8,927,609 source frames; the unchanged historical render length 8,931,705 includes 4,096 extra frames. The scorer crops 32 model frames, scores the exact source length and ignores the remaining 4,064 padding frames. Supports and render length were not changed to rescue a run. Earlier unexecuted runner/design versions are retained. An initial strict compile failure from renaming an included `main` was also preserved and fixed with explicit `return 0`. The actual sixteen-cell run completed once without execution or metric errors.

[Runner and gate documentation](../../Tools/prototypes/command-recording-benchmark-20261019/README.md) describes the implementation, guards and preserved evidence. Current numeric results are descriptive reuse of the same capture and authored candidate MIDI, not a fresh hardware holdout or complete circuit identification.
