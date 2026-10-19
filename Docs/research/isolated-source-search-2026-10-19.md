# Isolated public-source sample search — 2026-10-19

This pass recovered a useful independent-source stationary-pitch fixture: three author-published PSS-680 WAV recordings, containing 63 separated note interiors. Two different frequency estimators agree within 0.011875 cents on 62 notes. The remaining note has an octave-detection failure and is excluded, with its original measurements retained. These are conditional pitch references, not calibrated clock measurements or recovered raw patches. No synthesis law, production constant or preset was fitted or changed.

The earlier Andrews PSS-780, Keen On Keys PSS-480, Kevin PSS-680, KeyboardKrazy PSS-580 and Soden/ako PSS-680 recordings were already audited and are not counted as new sources. This search prioritized original-author isolated samples with accessible public files; it did not attempt an exhaustive catalogue. The complete source ledger, measurements, recipe association and artifact hashes are in [the JSON report](isolated-source-search-2026-10-19.json).

## Acquired source and scope

Jon Jungle's [PSS680 sample page](https://www.pss680.com/samplepacks.php) offers continuous musical recordings for subsequent manual cutting or sampler zoning. The author specifies ascending C, E-flat, G and B-flat notes. Three original ZIPs were downloaded through ordinary public HTTPS, without accounts, cookies, payment or access workarounds:

| Author download | Original WAV member | WAV bytes | Format |
| --- | --- | ---: | --- |
| [Saw Synth](https://www.pss680.com/samplepacks/tuned_instruments/pss680/saw_synth.zip) | `saw_synth.wav` | 2,859,618 | Mono PCM16, 44,100 Hz |
| [Chiptune Esq](https://www.pss680.com/samplepacks/tuned_instruments/pss680/chiptune_esq.zip) | `Chiptune esq.wav` | 2,473,058 | Mono PCM16, 44,100 Hz |
| [Synth Bass 1](https://www.pss680.com/samplepacks/tuned_instruments/pss680/synth_bass_1.zip) | `synth_bass_1.wav` | 3,918,178 | Mono PCM16, 44,100 Hz |

Each archive contains one continuous WAV. RIFF inspection finds only `fmt ` and `data` chunks: no embedded root key, sampler mapping or loop points. Analysis reads these files at their stored sample rate directly, without a sampler, transposition or resampling. Absence of loop metadata does **not** establish that the author never edited, retuned, looped or resampled the recordings upstream.

The author's [same-named recipes](https://www.pss680.com/patches.php) all start from voice 99 and list effects according to preference. Front-panel parameter values 0–8 are respectively:

| Recipe | 0–8 values |
| --- | --- |
| Saw synth | 63, 63, 0, 0, 1, 1, 7, 77, 86 |
| Chiptune esq | 63, 63, 0, 0, 2, 1, 7, 77, 86 |
| Synth Bass 1 | 63, 63, 24, 22, 1, 1, 0, 77, 86 |

This is an association between corresponding names on the author's site, not an observed SysEx dump or proof that every recorded setting matches the recipe. Capture route, physical effects, global tuning, audio interface clock and any normalization or individual-note processing are undocumented. All three packs come from the same author/site and may share one instrument and capture chain; they are not three independent hardware replicates.

No explicit general redistribution or commercial sample license was found. The public author links were analyzed privately under the research task's authorization. Original media and excerpts remain in ignored research storage and are not product assets. Free access does not establish permission to bundle the recordings commercially.

## Frozen measurement procedure

`fixture-protocol-frozen.json` was written after archive/header inspection and before decoding the audio. It selects all three files and all separable notes, rather than notes chosen for a desired synthesis result. Twenty-millisecond RMS frames define active segments at 30 dB below each file's 90th-percentile RMS; at least 60 ms below threshold separates segments. Segments shorter than 150 ms are rejected. Measurement uses the central 35–65% of each segment, capped at a centered 500 ms and requiring at least 120 ms. No segmentation overrides were applied.

The first estimator uses an autocorrelation period candidate between 30 and 4,000 Hz, then a 262,144-point Hann periodogram with log-parabolic peak interpolation. Autocorrelation selects the harmonic number used to divide the dominant partial. Each retained interior is also split into three equal windows; a frequency range above 1.5 cents would flag nonstationarity. All 63 interiors pass that stability rule, which alone does not establish correct octave identification.

A second, post-inventory estimator checks the same windows independently: fourth-order zero-phase Butterworth bandpass at 0.8–1.2 times the nominal note frequency, Hilbert analytic phase, and a straight phase-versus-time regression. It uses up to 500 ms source context on either side. Its band center comes from the first-pass nearest musical note; it is therefore an independent frequency estimator, not an independent note-label oracle. Filter-edge and capture-processing errors remain possible. No filter, time shift or engine parameter was optimized against a candidate DSP model.

All files contain 21 active segments. Frequencies and the author's scale together support inferred musical note numbers 36–96: C2, E-flat2, G2, B-flat2, C3 and so on. These labels are inferred musical pitches, **not recorded MIDI messages**, and there is no documented hardware transposition setting. Both estimates are retained for every row in `fixture-notes.json` and `.csv`; scripts and full harmonic inventories are retained alongside them.

## Separating pitch evidence

For the 62 unambiguous rows, the two estimators differ by at most **0.0118744436 cents**. Example Saw Synth windows and first-estimator frequencies are:

| Inferred musical MIDI | Frozen WAV window, seconds | Frequency, Hz |
| ---: | ---: | ---: |
| 39 | 2.396–2.684 | 77.7376107352 |
| 51 | 8.443–8.737 | 155.530031421 |
| 60 | 12.928–13.192 | 261.565110716 |
| 75 | 20.249–20.531 | 622.119777186 |
| 79 | 21.756–22.044 | 784.041066542 |
| 87 | 26.235–26.505 | 1,244.23894252 |

The table's decimal places preserve reproducibility, not a claim of corresponding physical accuracy. The lowest E-flat octave, inferred 39→51, exceeds an exact 2:1 ratio by **0.6102 cents** in Saw Synth, **0.6097 cents** in Chiptune and **0.5947 cents** in Synth Bass 1. Most other octave ratios are much closer to exact doubling. Saw Synth's first twelve harmonic peaks independently imply nearly the same roots, so the low-E-flat discrepancy is not merely interpolation of one irregular dominant line. Independent phase estimates corroborate it.

An unknown common tuning offset cancels in those within-file ratios. Consequently, these samples can distinguish ideal equal-tempered oscillator tuning from some note-dependent pitch laws. They do **not** identify a specific accumulator width, lookup table, master-clock frequency or OPU arithmetic mechanism. The four sampled pitch classes also do not determine the complete twelve-note tuning law. Upstream individual-note processing remains a competing explanation. This is a source-characterization result; testing any frozen synthesis candidate against it requires a separately declared prediction and scope.

The final Chiptune segment is a useful explicit failure. Its central window is 26.840–27.080 s. Autocorrelation chooses a spurious half-frequency near 1,046 Hz; the dominant 2,092.564 Hz line and its odd harmonics instead support the next C7. The putative half-frequency fundamental is about 53.7 dB below the dominant line, and the phase cross-check at that wrong nominal center disagrees by 497.57 cents. The original row is retained and excluded from interval summaries. It was not silently relabeled, and it is not evidence of hardware period doubling or a wrong played key.

## Other leads and access results

| Primary source | Result and reason |
| --- | --- |
| [Tabula's original Zynthian post](https://discourse.zynthian.org/t/soundfonts-from-minilogue-and-vintage-yamaha-synths/4908) | The owner describes per-key, finite samples of their own PSS-580 among other units. The directly linked public Drive file returned HTTP 404 in this attempt. No SF2 was acquired; this does not establish permanent deletion. |
| [Joel Bisson's PSS-480/680 pack](https://www.audiobombs.com/items/671/yamaha-pss-480-680-sample-pack-(sfz)), [waveform collection](https://www.audiobombs.com/items/1083/joel's-synth-waveforms), [house bass](https://www.audiobombs.com/items/642/yamaha-pss-480-house-bass) | Original-author material is promising, but public pages require sign-in for download. No account or bypass was used. The author discloses a defective/distorting PSS-480, and the waveform collection mixes TX81Z and PSS-480 sources; uninspected files cannot supply clean chip-specific fixtures. |
| [Cubilas PSS-680 product](https://www.cubilas.com/p/sf2-pss680/) | Vendor describes factory-voice multisamples with edited loop points. Purchase is required and a downloadable demo was unavailable on the inspected page. No purchase or sample acquisition. |
| [Freesound PSS-370 result](https://freesound.org/people/cms4f/sounds/159238/) and [ZANDERHUD's PSS-560 material](https://freesound.org/people/ZANDERHUD/) | Neither establishes the requested 480/580/680/780 OPU source and isolated-voice setting. No media was acquired or treated as interchangeable chip evidence. |
| PSS680 author's drum pack | Accessible, but PCM percussion does not constrain the FM oscillator question. Not downloaded. |

## Reproduction and freeze

Research files are under `build/isolated-source-search-20261019/`, which is ignored. `analyze_jungle_pitch.py` reproduces segmentation, harmonic/FFT inventory and segmentation plots. `crosscheck_phase_pitch.py` reproduces the second estimator. The JSON report includes the original ZIP/WAV, cached source pages, protocol, scripts, exact output and chart hashes. `fixture-notes.json` provides the combined accepted/excluded rows without selecting one estimator after comparison to another recording.

Frozen protocol SHA-256: `afb771879de9ce7e2d0114277450e47cff2b412657bf7e4f2896a5c73ac5bd77`. Frozen combined-note JSON SHA-256: `b9e56d5fdcf140ac7a8d838423403eade79d19cecfc1a35477b8ebadbf156961`. Measurements were frozen before the separate exact-PSS-780 cross-source prediction test. No runtime, factory bank, host session, package or artificial-noise path was changed, and no Git operations were performed in this pass.
