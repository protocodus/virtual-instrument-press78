# Native Press78 comparison with the PSS-780 recording

This is a descriptive regression comparison with an already inspected recording. It is not a fresh hardware holdout, and it cannot establish bit-exact OPU behavior or the accuracy of a recovered circuit.

## Available evidence

The useful target source is the user-supplied [PSS-780 preset-tour video](https://www.youtube.com/watch?v=ONfIvtDOog0). Its externally cached 48 kHz stereo PCM audio remains in the original research workspace. No redistribution license was found; neither that recording nor extracted reference clips are shipping resources. Generated local audition files belong only in a git-ignored build directory or an external directory.

The source plays a polyphonic MIDI arrangement of Scott Joplin's *Eugenia*. The original [Mutopia MIDI](https://www.mutopiaproject.org/ftp/JoplinS/eugenia/eugenia.mid) supplies 1,779 notes, on two MIDI channels, all with velocity127. One globally frozen affine mapping converts MIDI time to video audio time:

`audio_seconds = 0.8906462238832541 + 0.9998070138348876 × midi_seconds`

The 99 visible program changes each correspond to a different two-quarter-note MIDI bar. A new program applies at that bar to future note-ons; existing voices retain their earlier patch. This is an explicitly inferred performance policy, not a captured MIDI program stream or verified keyboard firmware behavior.

| Voice | Original v4 score window | First group retained by continuous replay |
|---|---|---|
| 65 Bowed Bass | 116.066667–117.233333 s | MIDI72 held1.764363s;80/41/53 held0.441091s, beginning115.574270s |
| 93 Human Voice1 | 165.500000–166.666667 s | MIDI82 held1.102727s;46/58 held0.441091s, beginning164.976446s |
| 97 Musical Saw | 172.566667–173.700000 s | MIDI72 held1.764363s;80/41/53 held0.441091s, beginning172.033900s |

These are not isolated single-note recordings. Vibrato, reverb and stereo chorus are visibly enabled for all three; sustain is additionally enabled for97. Portamento and duet are off. The file's MIDI velocity does not independently verify sender transformations or the keyboard's velocity response. Prior releases, polyphony and unknown capture processing remain confounds.

## Protocol

`Tools/hardware_benchmark.py` freezes its source snapshot, native fixture, exact sample-event schedule and protocol before estimating scores. `Tools/HardwareSequence.cpp` runs the whole performance from video time zero, including all prior program changes, held notes and tails. Program changes use `setPatch(..., false)`. Both source channels use the same patch; their identities distinguish note-offs. At a shared sample, program changes precede old note-offs, which precede new note-ons. Native voice allocation remains a documented model policy.

The fixture uses48kHz,12voices, unity master gain and the researched PSS-480 output-filter surrogate. Tone, drive, noise, DC blocking and limiting are bypassed. Raw-core parity is separately rendered with the output circuit bypassed. The existing factory vibrato/sustain flags are preserved identically to the frozen Python model. These settings isolate the measured model stages; they are not a promise to recreate every enabled keyboard effect.

The initial native modes are dry output and the old creative chorus at full mix,0.65Hz rate and2ms depth. The frozen offline v4 effective stereo transfer is an additional comparator. That offline transfer was fitted to this capture and includes acausal FIR context; it is a recording predictor, not an identified BBD circuit.

Full-synth scoring retains the original v4 windows,64 logarithmic bands over80–14,000Hz and three STFT resolutions512/2048/8192. A single RMS gain applies to each stereo pair; left and right are never fitted separately. Only the reported nominal native engine latency is removed. There is no local onset, phase, pitch or per-preset parameter search. Pair RMS matching intentionally removes absolute output-level evidence and must not be described as gain calibration.

A separate input-driven diagnostic supplies the observed arithmetic mid channel to an effect model and scores its predicted side channel over100–4,000Hz. It uses the prior frozen program-bar+.25s to+1.5s windows with0.2s context. A third-order zero-phase Butterworth bandpass is an analysis filter. No per-window gain or phase matching is allowed. The old creative effect is reproduced analytically with its fixed delay-tap law; native implementations of a new output component must be labeled separately. This diagnostic avoids synthesized-FM error but still includes reverb, codec, channel imbalance and unknown capture-chain effects. It cannot identify DAC or BBD distortion.

The targets were selected after observing earlier errors. Immediate neighbors64/66/92/94/96/98 and prior groups0/2/22/34/59/77 and1/3/23/35/60/75 are reused regression material. `--all-presets` evaluates all100 as descriptive reuse. There is no untouched hardware holdout in the current dataset. A stronger future test needs independently recorded dry sustained notes and matched note-off events with documented patch, tuning, velocity, effects and output connection.

## Reproduction and local artifacts

Run from the repository with NumPy, SciPy and a C++17 compiler installed:

```sh
python3 Tools/hardware_benchmark.py \
  --reference-root /path/to/original/pss780-experiment \
  --artifact-dir build/hardware-benchmarks/unique-run-name \
  --report Tests/results/hardware-baseline.json \
  --all-presets
```

Use `--source-dir` to select a previously frozen native source snapshot and `--baseline-report` to include its preserved outputs in a later comparison. Completed artifact directories cannot be overwritten. The external reference directory is required; the tool does not download recordings or silently substitute a synthesized reference.

Every target audition uses the same recorded window followed by the named model variants, separated by0.4s silence. Each candidate receives one stereo RMS match, then all variants share one safety gain. The exact gains, order, timing and SHA-256 hashes are recorded. No captured-noise bed is added. The JSON results are metadata suitable for review; reference audio stays in the ignored local artifact directory.

The baseline engine was snapshotted before the researched-chorus integration at `build/hardware-benchmarks/baseline-20261018T081942Z/source`. Subsequent mode changes must receive a new artifact directory and report, preserving the baseline and recording their source revisions. Improvements in a reused side-prediction score must be distinguished from changes in full-synth timbre, and neither score is a percentage of hardware fidelity.

## Initial preserved baseline

The completed baseline evaluates all100 previously observed presets. Its primary three-voice mean joint stereo band error is5.3051dB for native dry output,5.5728dB for the old native creative chorus, and5.1469dB for the frozen offline v4 transfer. In the independent input-driven side diagnostic, the old creative delay reproduction has target mean NRMSE1.5830; the archived v4 API reproduces0.31525. These comparisons demonstrate a mismatch in the old creative stereo behavior, not a newly measured hardware component law.

The raw native FM signal matches the offline target windows to approximately2.6×10⁻⁸ relative RMS, consistent with float32 output rounding. A1.18% whole-performance discrepancy is concentrated in preset91; its allocation/tail cause has not been established. The detailed local `parity-diagnosis.json` keeps that discrepancy visible instead of silently excluding it.

The analog comparisons use different numerical treatments of the same PSS-480 surrogate: the original offline `process_audio` uses4×192kHz processing plus FIR up/downsampling, while native `AnalogOutput` applies the derived SOS at the48kHz host rate. The native impulse test establishes agreement with the48kHz MNA discretization; it does not establish identity with the oversampled offline pipeline. This explains why unchanged target FM can coexist with small differences in midpoint spectra. A new chorus must be judged on the identical native midpoint as well as against the separately labeled offline pipeline.

## Recorded chorus comparison

The next immutable run is `build/hardware-benchmarks/recorded-20261018T084000Z`, summarized in `Tests/results/hardware-recorded-chorus.json`. It uses the new native Recorded mode at the frozen v3 capture rate0.9546467518Hz and fundamental depth0.4968365658ms, with full mix and width1. There is no new fit. The full engine receives `setChorusTime(-32/48000)` before playback so trimming its declared32-sample FM latency preserves the original absolute capture LFO epoch. This is fixed latency bookkeeping, not a measured phase adjustment.

| Target | Old Studio joint-band error | Recorded joint-band error | Offline v4 joint-band error |
|---|---:|---:|---:|
| 65 Bowed Bass | 5.465706dB | 5.140637dB | 5.337480dB |
| 93 Human Voice1 | 5.541306dB | 5.256891dB | 5.134617dB |
| 97 Musical Saw | 5.711329dB | 4.932254dB | 4.968507dB |
| Three-target mean | 5.572780dB | 5.109927dB | 5.146868dB |

The recorded transfer improves this band metric on all100 reused presets, with overall mean3.927488→3.202236dB. Target STFT convergence improves0.724090→0.598653, while target log-STFT error slightly worsens3.614403→3.642891dB. The six immediate neighbors likewise improve mean joint-band error4.124936→3.622473dB but worsen mean log-STFT error4.339867→4.455471dB. Improvement therefore depends on the metric; the remaining FM/envelope/capture mismatch is substantial.

The entire native raw and dry WAV files are byte-identical to the preserved baseline. Target midpoint error remains4.993459dB. This isolates the stereo change from the native FM and analog stages. The offline v4 score is a different numerical analog pipeline and a more elaborate fitted stereo transfer; its small ranking differences do not prove the causal native mode is more physically accurate.

The separate observed-mid-to-side target mean NRMSE changes from1.582988 for the old creative delay reproduction to0.403529 for native Recorded mode. The standalone native processor reproduces frozen v3 to4.32×10⁻¹¹ maximum absolute error across100 windows. Offline v4 remains better on this diagnostic at0.315248. These results validate the native implementation of an existing empirical stereo predictor, not a newly identified YM3420 DAC or MN3206 transfer law.

The run's `validation.json` verifies all100 offline v4 score rows to1×10⁻¹⁰ tolerance,27 local audition files across the main and focused manifests, finite unclipped samples, source/audio hashes and raw/dry byte identity. `focused-comparisons.json` supplies shorter four-part sequences in this order: reference → old Studio → native Recorded → offline v4. Its adjacent generator concatenates the already level-matched files without new gain changes. No source recording audio is tracked in the repository.

To repeat the new-path run after a later code revision, choose another unique directory:

```sh
python3 Tools/hardware_benchmark.py \
  --reference-root /path/to/original/pss780-experiment \
  --artifact-dir build/hardware-benchmarks/unique-recorded-run \
  --baseline-report Tests/results/hardware-baseline.json \
  --report Tests/results/hardware-recorded-chorus.json \
  --modes raw,dry,recorded --all-presets
```
