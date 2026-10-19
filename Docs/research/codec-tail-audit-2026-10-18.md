# AAC versus Opus tail audit - 18 October 2026

The final Sine Wave partials disappear at essentially the same times in YouTube's AAC140 stream and the previously acquired Opus251 stream. Their abrupt losses are therefore unlikely to be specific to Opus251 decoding or the old PCM16 export. This does **not** establish a YM3420 envelope cutoff: both streams may share instrument processing, a source-master gate/edit or earlier lossy encoding.

The [full ledger](codec-tail-audit-2026-10-18.json) preserves acquisition/decode provenance, the frozen lag, validation failures, every endpoint, channel-specific measurements and source hashes. No alignment, old benchmark score, DSP, preset, package or host state was changed.

## Acquisition and fixed comparison

The source remains AndrewsVintageKeyboards' [Yamaha PSS-780 Sounds](https://www.youtube.com/watch?v=ONfIvtDOog0). Ordinary public `yt-dlp` format 140 acquisition succeeded. A second acquisition with `--ignore-config` verifies that no user configuration, cookies or account is needed; both acquired M4A files are byte-identical, SHA256 `6be10a54e8d6112400f7c1c32af212d40836f3cf436a9a3574cb045cbebf1854`. The AAC stream is stereo 44.1 kHz, approximately 129.5 kb/s; the retained format 251 stream is stereo 48 kHz Opus. The newly acquired AAC is another encode of the same public video, not an independently recorded keyboard or an unprocessed source master.

Both streams were decoded with FFmpeg to floating-point 48 kHz stereo PCM, with no gain normalization or audio effect. AAC requires resampling from 44.1 kHz. The old benchmark PCM16 file was also read unchanged. Float Opus has exactly the old PCM16 frame count; their peak difference is 3.052e-5 and RMS difference 1.762e-5, consistent with the existing PCM16 quantization. The comparison never substitutes float audio into an old score.

Before inspecting the tail, one integer waveform-correlation lag was selected from arithmetic-mid audio over 2-30 s, restricted to ±100 ms. AAC content is 627 frames, or 13.0625 ms, later than Opus. This single lag is retained for every subsequent interval and tail measurement. There is no new gain, affine-scale, pitch or tail-specific phase fit. The initial code selected this lag with unnormalized finite-window correlation despite the protocol saying normalized correlation. A disclosed posthoc full-overlap normalized check independently selects the same 627-frame peak; the lag and every tail measurement remain unchanged.

The early-context correlation at this lag is 0.85767. A disclosed limitation is concentrated in its first part: 2-5 s correlation is 0.09577 and 5-10 s is 0.81513. The same frozen lag gives 0.99906 over 10-15 s and 0.99839-0.99933 over subsequent 5 s subwindows through 30 s. The cause of that early discrepancy has not been established; the record must not imply whole-file identity or a universally correct encoding delay.

Independent later validation uses the same lag:

| Opus-time interval | Arithmetic-mid correlation |
|---|---:|
|60-80 s|0.998894|
|140-160 s|0.998977|
|170-180 s|0.999232|

The nearby 170-180 s check supports using the frozen lag at the final tail, without rescuing the earlier failure through local adjustment.

## Frequency-specific survival

The frozen benchmark's final note-off is 182.178979166667 s, sample 8744591. Actual MIDI delivery remains uncertain, as documented in the [audible-event audit](midi-alignment-audit-2026-10-18.md). This uncertainty is common to both codec observations and does not change their relative comparison.

The original protocol retains nominal-tone 24/48/96 ms Hann demodulation. A second method, declared before codec-tail measurements after reading the forensic investigator's procedure, jointly estimates fixed-frequency sine/cosine components at MIDI 39,46,58,59,67,75,79,87 plus DC and a linear trend. It uses 40 ms windows, 2 ms hops, with Hann applied to both signal and basis, separately for left/right/mid. No synthesis or envelope law enters the estimator. The methods are stored separately, with their different temporal support explicit.

For each partial, the held reference is its median amplitude dBFS over frozen-off [-200,-100] ms. Audio is not normalized; relative levels only label measurements. The original endpoint code accepts at least 96% of the 50 subsequent 2 ms samples below threshold (nominal 100 ms), allowing up to two samples at or above threshold. This is more tolerant than the frozen protocol's continuous-persistence wording. The table gives the final qualifying downward crossing at 50 dB below the held reference, which lands in the abrupt loss rather than the preceding slow decay.

A disclosed **posthoc** strict check requires all 50 of those same samples below threshold. It exactly reproduces all 108 stored endpoints across three formats, three channels, four partials and three levels, with zero differences. This independently repeats the audit agent's earlier inline check. The new `strict-persistence-validation.json` receipt binds the original result, curve and analysis-script hashes; the frozen protocol and measured endpoint values remain untouched. Thus the displayed crossings also satisfy the stricter sampled criterion, without claiming more temporal precision than the window supports.

| Mid-channel partial | AAC after mapped off | Opus float after mapped off | AAC minus Opus |
|---:|---:|---:|---:|
|39|1.801715 s|1.802172 s|-0.457 ms|
|75|1.733185 s|1.733081 s|+0.104 ms|
|79|1.679560 s|1.679618 s|-0.058 ms|
|87|1.312207 s|1.312238 s|-0.031 ms|

All differences are below 0.46 ms. Interpolation provides numerical crossing estimates; it does **not** create submillisecond physical timing accuracy from a 40 ms window. The result is that both encodes preserve the same abrupt feature within analysis support.

Held amplitudes agree to approximately 0.03 dB. Over off+0.3 to +1.0 s, median absolute AAC-minus-Opus partial-level differences are 0.133,0.078,0.078 and0.055 dB for 39,75,79,87 respectively. The slow tails and separate extinction times visibly overlap. Crossing times at 40 dB below held level differ by as much 32 ms because small level differences intersect a shallow, rippling tail; the full JSON retains those values rather than reporting only the best-agreeing threshold.

The original PCM16 Opus and float Opus 50 dB crossings differ by less than 0.005 ms. Reading below one sample's quantization step through a windowed coherent estimate does not establish greater DAC resolution; it only shows that PCM16 export is not causing this large abrupt disappearance.

After the loss, fixed-frequency estimates mostly sit near -93 to -99 dBFS over off+2.2 to +2.8 s. Broadband recorded background remains substantially higher: stereo RMS is about -71 dBFS, with mid RMS about -77 dBFS. A frequency-specific tone can disappear while recording background remains. These observations do not authorize adding any noise to the instrument.

## Interpretation boundary

The same distinct partial losses in AAC and Opus make a format 251-specific Opus decision an inadequate sole explanation. PCM16 quantization also does not explain them. The evidence strengthens the case that this feature exists earlier in the common signal chain.

It does not locate the feature inside YM3420. The original upload could already include a lossy encode, level-dependent gate, multiband processing, recording effects or an instrument-side threshold. YouTube's two formats share a public video and likely substantial upstream material; their agreement is not a fresh hardware holdout. Frequency 87 can include a harmonic of 75, and 75 can include an eighth harmonic of 39. These estimates describe frequency-specific survival, not independently identified voice allocation.

No 96 dB-to-shorter-cutoff correction follows directly from this test. The appropriate next evidence is an unprocessed direct-output recording with known gates, several carrier TL values and effects independently toggled. That separates an absolute signal threshold from an envelope-state threshold and from capture processing. Existing production constants and all noise-removal requirements remain unchanged.

Acquired media, decoded audio, scripts and plots remain ignored under `build/codec-tail-audit-20261018`. No recording or derived audio was added to shipping resources.
