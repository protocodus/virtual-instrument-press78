# Mode 00 source-input benchmark - 19 October 2026

This experiment corrects a specific source-input mismatch in the research fixture. The sampled PSS-780 video display reads `c.00`, while the exact [Yamaha owner manual](https://usa.yamaha.com/files/download/other_assets/1/317511/PSS780E.PDF) identifies that state as Keyboard Assign mode (printed page 31), describes restricted five-octave note reception and ignored velocity (page 34), and lists the received-note range as **36-96 inclusive** (page 45). The published source MIDI contains 18 lower notes that the existing benchmark had sent into the engine.

The filter was selected from those manual/source observations **before any new score**. It excludes both note-on and note-off for these 18 note pairs in a separate benchmark branch. It adds no instrument-wide key limit and changes no DSP, factory preset, UI, native adapter, version, package or host state. Artificial noise remains absent. The [complete JSON](mode00-benchmark-2026-10-19.json) retains every outcome, historical comparison, regression and model voice-pressure log.

The interpretation remains conditional: the published MIDI must be the sequence sent to the recorded instrument, its note numbers must reach the hardware without upstream transpose/remapping, and the sampled Mode 00 state must apply during performance. There is no continuous mode trace or captured MIDI wire log. Lower spectral error cannot independently prove these assumptions. This is a source-mode-aware comparison, not a recovered exact sender protocol.

## Frozen scope and exclusions

Protocol SHA256: `8a97f902c9ab96e41da2ff0cd0761209f15b591163cc246d0a9b184cdd15edf9`. It was frozen before filtered rendering or scoring and includes the exact manual PDF/page images, effect-classification result, all 300 sampled source-frame hashes, original recording/MIDI metadata, immutable historical result, factory/source snapshots and all event files.

Exactly four previously frozen timing maps and three existing DSP states are reused from the [timing sensitivity experiment](timing-sensitivity-2026-10-19.md): b11; release-only duration x3 without Reverb; and the same slower release with the carrier-trigger 18 dB/raw RR4 envelope Reverb hypothesis. All three corrected timing maps failed the prior held-out adoption criteria and remain scenarios, not ground truth. No mapping, model parameter or transposition is selected from new scores.

The excluded pitches are MIDI 29 twice, 34 thirteen times and 35 three times, all on zero-based source channel 1. Their original source note indices are 62, 124, 188, 255, 265, 354, 686, 748, 812, 879, 889, 1219, 1224, 1250, 1376, 1721, 1726 and 1752. Every source note already has velocity 127; this fixture cannot identify the hardware's fixed amplitude when velocity is ignored, and it does not introduce a new velocity law.

Each filtered event file contains **1,761 note pairs and 3,622 events**, including all 100 inferred program commands. The original files have 1,779 pairs and 3,658 events. The independent verifier confirms the filtered list is an ordered subsequence and removes exactly those 36 on/off events; no accepted note or program event changes.

All maps still transform note onset plus separately rounded scaled gate, and program commands still map from timeline `midi_start_seconds`. Event order remains program, old note-off, new note-on. Program-bar inference, unchanged active-voice patch state, and note-off delivery remain assumptions. The full 8,931,705-frame/48 kHz sequence, 12 voices, Recorded chorus, audio-time chorus epoch of -32/48000 s, 32-frame latency trim and all 100 fixed **absolute** v4 score windows are unchanged.

The metric is the frozen pair-RMS-normalized stereo comparison: 64 bands over 80-14,000 Hz and STFT 512/2048/8192. There is no timing, phase, pitch, local-window or parameter fitting. One stereo-pair RMS gain is the established normalization; it discards absolute gain evidence. Tone, drive, limiter, DC blocker and additive noise remain disabled. The release/Reverb hypotheses and existing allocation/retirement rules are unchanged.

## All 100-preset results

The source-mode filter modestly reduces joint-band, mid-band and STFT-convergence means in all 12 combinations. **Log-STFT error slightly worsens in every combination**, by 0.00428-0.00588 dB. These mixed spectral outcomes are preserved; the input policy was selected from the manual/source observations rather than whichever metric improved.

| Timing scenario | DSP | Historical joint band, dB | Filtered joint band, dB | Delta | Improve / regress / same |
|---|---|---:|---:|---:|---:|
| Unchanged | b11 | 3.173500 | 3.145007 | -0.028493 | 7 / 8 / 85 |
| Unchanged | RR x3 | 3.216133 | 3.206299 | -0.009834 | 6 / 11 / 83 |
| Unchanged | RR x3 + Reverb | 3.233245 | 3.217090 | -0.016155 | 10 / 8 / 82 |
| Old scale + offset | b11 | 2.925535 | 2.893976 | -0.031558 | 9 / 8 / 83 |
| Old scale + offset | RR x3 | 3.022330 | 3.002392 | -0.019939 | 10 / 8 / 82 |
| Old scale + offset | RR x3 + Reverb | 3.095914 | 3.072636 | -0.023279 | 11 / 7 / 82 |
| Nominal scale | b11 | 2.913863 | 2.882409 | -0.031454 | 9 / 7 / 84 |
| Nominal scale | RR x3 | 3.022311 | 3.004885 | -0.017426 | 10 / 8 / 82 |
| Nominal scale | RR x3 + Reverb | 3.094309 | 3.073113 | -0.021195 | 12 / 6 / 82 |
| Robust affine | b11 | 2.915858 | 2.884220 | -0.031638 | 9 / 8 / 83 |
| Robust affine | RR x3 | 3.019881 | 3.001791 | -0.018090 | 11 / 7 / 82 |
| Robust affine | RR x3 + Reverb | 3.091868 | 3.070001 | -0.021867 | 12 / 6 / 82 |

Counts use the established 1e-6 dB tolerance. Many presets are unchanged because only 18 source notes were excluded. The complete JSON retains the full historical and filtered metric dictionaries, every score-window delta and each regression.

| Timing scenario | DSP | Filtered mid band, dB | STFT convergence | Log-STFT, dB | Log-STFT delta |
|---|---|---:|---:|---:|---:|
| Unchanged | b11 | 2.734443 | 0.550611 | 3.157069 | +0.004853 |
| Unchanged | RR x3 | 2.777823 | 0.548942 | 3.074592 | +0.005880 |
| Unchanged | RR x3 + Reverb | 2.801209 | 0.548712 | 3.006127 | +0.005154 |
| Old scale + offset | b11 | 2.483913 | 0.469230 | 2.895595 | +0.005149 |
| Old scale + offset | RR x3 | 2.577175 | 0.486974 | 2.844774 | +0.005488 |
| Old scale + offset | RR x3 + Reverb | 2.668417 | 0.487639 | 2.784480 | +0.004988 |
| Nominal scale | b11 | 2.470302 | 0.470357 | 2.898727 | +0.004841 |
| Nominal scale | RR x3 | 2.581022 | 0.487503 | 2.839478 | +0.005077 |
| Nominal scale | RR x3 + Reverb | 2.668890 | 0.488229 | 2.778083 | +0.004468 |
| Robust affine | b11 | 2.472417 | 0.469767 | 2.894692 | +0.004767 |
| Robust affine | RR x3 | 2.578069 | 0.486792 | 2.835496 | +0.004879 |
| Robust affine | RR x3 + Reverb | 2.665769 | 0.487457 | 2.773766 | +0.004276 |

Music Box 98 supplies the largest b11 joint-band improvement under every timing map: -2.071 to -2.213 dB. Banjo 66 also improves by approximately 0.49-0.55 dB. Regressions remain: Accordion 20 worsens by +0.236 to +0.371 dB for b11, and by +0.461 to +0.616 dB for RR x3. Under the unchanged timing map, Strings 77 adds +0.249 dB for RR x3 and Ocarina 42 adds +0.263 dB for the Reverb candidate. These are whole-window errors, not identified note-level causes.

**Model orderings do not change.** All-100 joint- and mid-band error still favor b11 over RR x3 over Reverb for every map. The historical STFT-convergence timing dependence persists: the old map favors Reverb, while each corrected scenario favors b11. Log-STFT favors Reverb across the maps. This source-policy correction does not rescue a unique release law or choose a timing map.

## Bowed Bass, Human Voice 1 and Musical Saw

The three focus-window joint-band changes are all below 1e-9 dB; the maximum absolute change across the four primary metric families is approximately 1.02e-9. The focused results are effectively unchanged. No excluded note-on lies inside these fixed windows. Their old/new audio exports are retained to make that absence of a material improvement reviewable.

| Timing scenario | DSP | Bowed Bass 65, dB | Human Voice 1 93, dB | Musical Saw 97, dB |
|---|---|---:|---:|---:|
| Unchanged | b11 | 5.074640 | 5.259832 | 3.194993 |
| Unchanged | RR x3 | 3.174110 | 5.167125 | 2.138073 |
| Unchanged | RR x3 + Reverb | 2.952059 | 5.103087 | 2.138163 |
| Old scale + offset | b11 | 4.430285 | 3.047601 | 3.014010 |
| Old scale + offset | RR x3 | 3.173022 | 3.153277 | 2.257568 |
| Old scale + offset | RR x3 + Reverb | 3.002984 | 3.108246 | 2.257532 |
| Nominal scale | b11 | 4.399180 | 2.872304 | 2.858313 |
| Nominal scale | RR x3 | 3.171003 | 3.043378 | 2.105312 |
| Nominal scale | RR x3 + Reverb | 2.997158 | 2.969520 | 2.105325 |
| Robust affine | b11 | 4.410611 | 2.838638 | 2.963845 |
| Robust affine | RR x3 | 3.167603 | 3.000579 | 2.230526 |
| Robust affine | RR x3 + Reverb | 2.989792 | 2.939324 | 2.230497 |

Human Voice 1 therefore retains the prior timing ambiguity: the old map slightly favors slower release, but each corrected scenario favors b11 in joint-band error. Bowed Bass and Musical Saw retain their slower-release band improvements. The source filter does not explain or fix their audible envelope differences. It also does not alter the model replacement counts within these focus presets: under the old map they remain 0 / 0 / 5 for b11, 17 / 3 / 13 for RR x3 and 17 / 18 / 17 for Reverb (ordered 65 / 93 / 97).

## Model voice pressure

The existing read-only fixture records `activeVoices()` before and after each note-on and the model's exact oldest-replacement eligibility condition. All 12 historical scenarios are rerendered with this diagnostic and must reproduce their original complete WAV hashes. Their temporary WAVs are deleted immediately after verification. The same audited fixtures render the 12 filtered scenarios and retain every pressure CSV.

These counts describe **the current model**, not observed hardware allocation. The unchanged 12-voice oldest replacement, 96 dB carrier retirement and 48-tick stolen fade remain uncertain. Removing a note can affect later allocation and carried-over preset tails; a target window can therefore change without containing an excluded onset itself.

| Timing scenario | DSP | Historical replacements / 1,779 ons | Filtered replacements / 1,761 ons | Change |
|---|---|---:|---:|---:|
| Unchanged | b11 | 251 | 238 | -13 |
| Unchanged | RR x3 | 814 | 799 | -15 |
| Unchanged | RR x3 + Reverb | 1759 | 1741 | -18 |
| Old scale + offset | b11 | 251 | 238 | -13 |
| Old scale + offset | RR x3 | 814 | 799 | -15 |
| Old scale + offset | RR x3 + Reverb | 1759 | 1741 | -18 |
| Nominal scale | b11 | 251 | 238 | -13 |
| Nominal scale | RR x3 | 813 | 798 | -15 |
| Nominal scale | RR x3 + Reverb | 1759 | 1741 | -18 |
| Robust affine | b11 | 251 | 238 | -13 |
| Robust affine | RR x3 | 814 | 799 | -15 |
| Robust affine | RR x3 + Reverb | 1759 | 1741 | -18 |

The filter removes 13 replacements from b11 and 15 from RR x3, while the Reverb candidate loses exactly 18 replacements with the 18 removed notes. Reverb still replaces 1,741 of 1,761 onsets, so the long-tail capacity problem remains. Removing unsupported source notes is useful fixture work; it does not validate the modeled hardware allocator or the 96 dB retirement threshold.

## Verification and reproduction

The independent verifier checks input hashes; exact on/off exclusions and retained event order; all 100 program commands under each map; all 12 filtered audio hashes and all 12 historical diagnostic hashes; every pressure CSV/count; every per-preset filter delta and model contrast; and all 100-preset aggregate means. All 24 renders are finite and report 32-frame latency. Every new gain-matched listening file is read back and checked for finite samples, matching hash and peak at most 0.85. No live-browser or listening-study validation is claimed.

Local artifacts are under ignored `build/mode00-benchmark-20261019/`. The `audition.html` page compares **hardware -> historical unfiltered fixture -> filtered Mode 00 fixture**, separately for each timing map and DSP state on Bowed Bass 65, Human Voice 1 93 and Musical Saw 97. Each model uses one stereo-pair RMS gain; a common safety gain across the hardware and all 24 candidates is used per voice. Source-derived audio remains local and is not shipped.

The source-aware branch is reproducible without editing historical reports or production:

```sh
python3 Tools/benchmark_mode00_recording.py freeze \
  --output build/mode00-benchmark-new-run \
  --manual-page45 /path/to/exact-owner-manual-printed45.png
python3 Tools/benchmark_mode00_recording.py run \
  --output build/mode00-benchmark-new-run
```

Use the tool's `--prior-timing`, `--prior-law`, `--prior-reverb`, `--effect-audit` and `--manual-pdf` options when immutable local evidence is stored elsewhere. It downloads nothing and refuses to overwrite a started run. The maximum WAV storage during rendering was 857,444,208 bytes; all retained full WAVs plus 111 listening exports total 955,242,646 bytes, below one billion. The 12 historical diagnostic WAVs were deleted after exact-hash verification. Production remains b11; the benchmark branch does not impose the source hardware's keyboard mode on the plugin's playing range.
