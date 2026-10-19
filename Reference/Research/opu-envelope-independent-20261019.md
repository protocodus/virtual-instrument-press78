# Independent OPU envelope sources — 2026-10-19

The new useful constraint is a repeatable, slow amplitude decay in Jon Jungle's original PSS-680 PCM samples. All **16 feasible fixed late Synth Bass 1 windows** have nearly straight log-amplitude slopes, −24.469 to −28.556 dB/s. A separately frozen **posthoc** harmonic diagnostic changes these slopes by at most 0.202 dB/s. Their slow decline therefore cannot mainly be explained by changing harmonic balance in the measured windows.

This does **not** identify a new envelope law. The published recipe is associated by name, not by a recorded raw voice dump. Actual key gates, performance effects and capture processing are unknown. It is particularly unsafe to equate front-panel Decay 22 with an isolated raw D1R or D2R field without checking the front-panel macro. No production envelope, multiplier, preset or noise path is changed.

## Source and evidence limits

The [author's PSS680 sample page](https://www.pss680.com/samplepacks.php) supplies continuous Saw Synth, Chiptune Esq and Synth Bass 1 WAVs. The author describes ascending C/E-flat/G/B-flat samples intended for subsequent cutting or sampler zoning. Their acquisition, original archive/WAV equality, headers and pitch inventory were already documented in [the isolated-source audit](isolated-source-search-20261019.md). Each is mono PCM16 at 44,100 Hz; none has embedded gate, loop or root-key metadata. They are read at their original sample rate without sampler playback or resampling.

The [same-name recipes](https://www.pss680.com/patches.php) start from voice 99. Saw and Chiptune list zero decay for both operators; Synth Bass 1 lists modulator/carrier decay 24/22, attack 63/63, ratios 1/1, feedback 0 and modulation/total level 77/86. Effects are left to preference. The exact captured patch, hidden fields, interface settings, normalization, edits and upstream processing are not established. All three may share one unit and capture chain. Public access permits this authorized private research; no broad commercial sample or redistribution license is claimed, and the media remains ignored.

Checking the author's own [linked channel](https://www.youtube.com/channel/UCLDvEldk7cG3nRLkwVEX-Mg) also recovered [PSS 680 Editing Fun!](https://www.youtube.com/watch?v=a0SFoa7lUNQ), published 13 February 2024 by Jungle Jon. Metadata reports 218 seconds. Ordinary public acquisition obtained H2641080p60 video plus Opus audio, 112,904,678 bytes total. Only source 60–78 s was decoded to a new analysis WAV; no full-length WAV was needed. No accounts, cookies, access workarounds or purchases were used.

Its captions and readable panel frames show selection of voice 99, storage in bank 1, modulation editing, then carrier Decay changes before modulator Decay changes. Parameter 3 reads 31 around 64–67 s and 21 around 70–73 s. Modulator Decay still reads 0 beforehand. Reverb, Sustain, Chorus, Vibrato, Duet and Portamento indicators appear unlit in the inspected front-panel coverage. Physical key fingers are cropped; **gates are not recovered**. The recording transfer is undocumented, and audio-active groups can contain several notes. This source supplies exact visible front-panel settings, not a sample-accurate dry MIDI fixture or captured SysEx.

The site's tutorial page currently contains headings without embedded tutorials, and its SysEx page links an editor rather than downloadable same-name patch dumps. Neither fills the raw-patch/gate gap. Previously inspected Soden, Kevin and Keen sources were reviewed rather than presented as new independent recordings; their documented timing and state limitations remain.

## Procedure frozen before new amplitude measurements

The prior pitch pass had already inspected these WAVs, so this is new fixed-window amplitude analysis of reused sources, not an unseen-audio holdout. Before measuring slopes, protocol SHA-256 `c009354ad30af119ec368087c728910e4d6b19ca28504f55b4bdfd3978c23cc3` fixed:

- Every one of the 63 prior RMS-active segments: body interval at active entry +0.15 to +0.55 s.
- Every one of the 21 Bass segments: additional late interval at entry +0.65 to +1.05 s.
- A fixed end-plus-100-ms feasibility margin within the prior active interval. Five high Bass late windows fail this rule and are retained without shortening.
- Centered 50-ms Hann energy RMS at 5-ms hops, followed by ordinary regression of level in dB against source time. No pitch, gate, gain, smoothing or rate optimization.
- A straight captured-decay gate: negative slope, R²≥0.99, maximum residual≤0.5 dB, fitted drop≥0.5 dB, no near-full-scale samples and minimum amplitude at least ten times the fixed preceding reference RMS.

Audio-active entries/exits are explicitly **not MIDI note-ons/offs**. Even a passing interior is not proof of a held-key D2 stage. The channel policy was separately frozen before measurement: mono WAVs use their one channel; the video uses arithmetic mid primarily and both sides as retained diagnostics.

The video ranges are fixed at 64.5–67.5 s (display 31) and 70–73 s (display 21). A predefined 10-ms RMS detector selects all active groups; fits use entry +50–150 ms and +100–400 ms. Cropped groups or incomplete support fail rather than move. The fixed reference at 60.0–60.2 s contains speech and is deliberately only a conservative background reference, not a certified electronic noise floor.

Extraction controls use known decaying sine and fixed-timbre FM waves at three frequencies, two phases, four rate-derived slopes and four fixed windows. **All 192 controls pass** the one-percent slope-error gate; the worst relative error is 0.000129896 (0.01299%). These establish extraction behavior for fixed timbre, not the hardware rate formula or an unknown capture chain.

## WAV results

There are 84 declared windows, 79 metadata-feasible fits and 16 straight-decay passes:

| Source / fixed window | Fits | Captured slope range, dB/s | Outcome |
| --- | ---: | ---: | --- |
| Saw / body | 21 | −0.069114 to +0.093291 | Essentially held level; negative-decay gate does not pass |
| Chiptune / body | 21 | −0.019677 to +0.090222 | Essentially held level; negative-decay gate does not pass |
| Bass / body | 21 | −25.891925 to −17.963469 | Curved; all R² below 0.99, maximum 0.989910 |
| Bass / late | 16 | −28.556085 to −24.469032 | All pass; R² 0.999875–0.999930 |

No analysis support is clipped. The first implementation stopped on the first Chiptune note because its frozen preceding reference lies before file start. The original script and failure record are retained. The corrected implementation keeps that unavailable-reference failure; it does not truncate the reference, choose another floor or change the frozen protocol/window. That note's descriptive fit remains in the ledger.

For comparison only, the current heuristic at effective rate 22 gives 90.509668 dB/s. Equating that rate with the published carrier Decay 22 would require the still-unrecovered macro/patch mapping, known envelope stage and capture transfer. These samples must not supply an arbitrary replacement global divisor merely because the observed decline is much slower.

## Same-window harmonic check and pitch grouping

After the RMS result was known, a second protocol froze a diagnostic on exactly the 16 accepted late Bass windows. It uses the prior frozen note frequencies, 100-ms Hann-weighted joint sine/cosine fits for eight integer harmonics plus DC/trend, and the **same 81 timestamps in each window**. There is no new frequency, window or selection fit and no new adoption threshold.

The fundamental's log-amplitude slope differs from total RMS by only +0.055870 to +0.201933 dB/s. Higher-harmonic energy starts around −16.5/−22 dB relative to the fundamental and falls to about −30/−36 dB. Thus the sound becomes closer to a sine while its fundamental itself continues the slow, nearly linear decline. This bounds one timbre-related explanation; it does not establish an operator's exact internal attenuation.

A **posthoc descriptive grouping** is conspicuous:

| Inferred musical pitches in the sampled four-class sequence | Fundamental slope range, dB/s | Median |
| --- | ---: | ---: |
| MIDI 36–58, eight notes | −24.433235 to −24.269411 | −24.329866 |
| MIDI 60–82, eight notes | −28.494750 to −28.395038 | −28.463828 |

These are inferred pitches, not recorded MIDI events. The sampled step is a useful constraint to test against raw patches and firmware; it is not a fitted RKS threshold. Hidden key scaling, capture dynamics interacting with pitch-dependent levels, performance effects, author editing or a parameter change remain alternatives. The five excluded higher late windows do not establish another rate group. The [existing exact-780 RKS0 audit](rks0-release-slopes-20261019.md) independently found audible pitch dependence with different confounds; matching directions do not identify one common implementation.

## Video remains unqualified

The detector finds two display-31 active groups per channel, both cropped by the frozen range boundaries. All their fixed fits are rejected. Display 21 yields one group per channel; its mid extended fit at 70.15–70.45 s gives −23.110415 dB/s, R²0.995745, but the minimum amplitude is only 0.700 dB above the fixed reference rather than the required 20 dB. Its short fit also fails linearity. **Zero video fits qualify.** No windows or reference were replaced to rescue this result, and those active groups are not labeled single gated notes.

The new evidence therefore constrains captured Bass envelope shape and its sampled pitch dependence; it does not resolve dry RR/SRR, actual note-off delivery, Human Voice 1's Reverb-enabled tail, or the complete OPU rate table. The useful next separator remains a raw-patch, effects-off, fixed-gate capture, or a verified firmware trace of the front-panel macro and rate commands. Production stays unchanged.

The [JSON ledger](opu-envelope-independent-20261019.json) retains all passes, failed feasibility/reference cases, 192 controls, video failures, the posthoc diagnostic, sanitized source metadata and hashes. Ignored artifacts are under `build/opu-envelope-independent-20261019/`; no third-party audio enters instrument resources.
