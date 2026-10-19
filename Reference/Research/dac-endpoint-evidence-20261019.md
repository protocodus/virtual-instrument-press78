# DAC and low-level endpoint evidence — 19 October 2026

The exact PSS-780 recording rules out a single common scalar output gate as the complete explanation of the separate tail endings. It still does **not** identify a DAC bit depth, an envelope word length, or the location of the threshold. A per-voice attenuation endpoint and frequency-selective processing in the unknown upload master remain plausible. No DSP, factory patch, circuit coefficient, version, host state or added-noise behavior changes in this pass.

## Selective loss while other components survive

This is a posthoc discriminator on the reused [PSS-780 tour](https://www.youtube.com/watch?v=ONfIvtDOog0), rather than a new hardware holdout. The [earlier codec audit](codec-tail-audit-20261018.md) supplies the fixed 627-frame AAC-to-Opus alignment and the 40 ms joint fixed-frequency estimator. The present comparison uses declared windows before and after the first recorded partial ending: 1.15–1.25 and 1.35–1.45 seconds after the frozen inferred note-off at frame 8,744,591/48,000. No gain, pitch, gate, synthesis or timing fit is introduced.

Each number below is the median recorded arithmetic-mid component amplitude in dBFS. The final column is the difference of the two medians, not a fitted release slope.

| Encode / component | Before | After | Change |
| --- | ---: | ---: | ---: |
| Opus251 / MIDI 39 | −55.64 | −57.77 | −2.14 dB |
| Opus251 / MIDI 75 | −54.44 | −57.29 | −2.85 dB |
| Opus251 / MIDI 79 | −55.73 | −58.21 | −2.47 dB |
| Opus251 / MIDI 87 | −60.29 | −95.67 | **−35.38 dB** |
| AAC140 / MIDI 39 | −55.75 | −57.77 | −2.02 dB |
| AAC140 / MIDI 75 | −54.31 | −57.33 | −3.02 dB |
| AAC140 / MIDI 79 | −55.55 | −58.22 | −2.68 dB |
| AAC140 / MIDI 87 | −60.25 | −98.34 | **−38.09 dB** |

Thus the lost component falls an additional 32.53–33.25 dB relative to each survivor in Opus, and 35.07–36.06 dB in AAC. A common scalar gain would multiply all of these simultaneous components alike. It cannot by itself create this selective collapse, provided the separated components represent their own sources. Chorus changes individual left/right amplitudes, so the full ledger retains both channels and does not treat them as independent hardware trials. MIDI 87 can also include the second harmonic of MIDI 75; these are frequency components, not proven isolated voice stems.

As an implementation check, the fit was recomputed directly from the retained float audio at 200 centers per format/channel. All 1,200 windows agree with the archived amplitudes to a maximum absolute amplitude error of 4.34×10⁻¹⁹. This confirms the numerical comparison, not the physical origin of the ending.

## Recorded background does not undergo the same loss

Unnormalized 100 ms Hann Welch periodograms use a 50 ms hop. Integrated power is retained for 2.5–3.5, 4–6 and 7–9 kHz. These bands contain no fundamental of the declared sine chord; harmonics, analog and recording interference, codec content and other background remain possible. They are not measured device-noise specifications.

In arithmetic mid, the 7–9 kHz band is −81.33 dBFS before the first ending (off+1.05–1.25 s), −81.14 dBFS afterward (off+1.40–1.60 s), and −81.08 dBFS after all four endings (off+2.20–2.80 s). AAC gives −81.05, −81.10 and −81.10 dBFS. The high-band recorded background therefore survives while the tone components vanish. The lower two bands fall modestly and are retained in the JSON rather than described as perfectly constant.

This strengthens the rejection of a single final mute of the whole recording. It does not rule out a gate before subsequently added background, frequency-selective denoising, an instrument-side voice mute, or a nonlinear converter. It does not authorize restoring hiss or any artificial noise.

## Mechanisms that must remain distinct

| Candidate mechanism | What the present recording establishes | Missing discriminator |
| --- | --- | --- |
| Fixed EG-state endpoint | Compatible; the observed dBFS cluster does not establish its domain | Same patch/rate/pitch with LKS0 and different carrier TL/velocity; an EG-only endpoint should occur at the same elapsed time when TL is independent of EG state |
| Per-voice total-attenuation truncation | Compatible; raw factory carrier TL13 and LKS0xB9 make total attenuation different from EG attenuation | Increasing known static attenuation should advance cutoff by approximately the attenuation difference divided by the late release slope, if other laws remain fixed |
| Postmix DAC quantizer or dead zone | Unidentified; this is nonlinear and is **not** excluded by the scalar-gain test | Weak releasing tone alone versus with a stronger, nonharmonic held tone, at unchanged gain and only two voices; recover distortion/transfer at a known pre/postmix point |
| Source-master spectral gate or earlier lossy coding | Still compatible; AAC and Opus are encodes of the same unknown upload master | Unprocessed lossless direct-output capture; repeat at two analog output-volume settings with constant capture gain |
| One final common scalar gate/mute | Inadequate as the sole cause of the selective component ending | The simultaneous surviving components already provide the relevant control, subject to component identity |

A lossy, filtered, stereo-chorused recording cannot expose the original converter's code histogram or staircase directly. The −61 dBFS arithmetic-mid cluster is affected by recording gain and phase cancellation. Neither `−61 / 6.02` nor a comparison to a nominal PCM floor recovers meaningful YM3420 bits here. A short-window coherent estimate below one PCM16 step also does not demonstrate additional DAC resolution. No integer quantizer, hidden gate, arbitrary cutoff or word-length default is adopted.

## Refreshed primary-source boundary

The exact PSS-780 service parts evidence still identifies the YM3420BF/C and its analog connections only to the extent recorded in the [output schematic audit](output-schematic-audit-20261018.md). It does not supply a numerical converter transfer table or EG word length.

The refreshed [firsthand d-tech chip investigation](https://dtech.lv/techarticles_yamaha_chips.html) identifies an integrated DAC and a separate CPU in YM3420. Its CPU width must not be relabeled as DAC width. No converter resolution, sample-update cadence or endpoint equation was recovered there. The current [MAME PSR/PSS driver](https://raw.githubusercontent.com/mamedev/mame/master/src/mame/yamaha/ympsr16.cpp) still registers the instruments without sound and marks its CPU clock divider as guessed. The [ymfm supported-chip list](https://raw.githubusercontent.com/aaronsgiles/ymfm/main/README.md) does not list YM3420. Those are explicit implementation gaps, not independent specifications of OPU arithmetic.

Exact-part-number searches in English and Japanese, including DAC resolution, D/A, envelope counter, patents and die/decap terms, recovered no new usable YM3420 word-length source. An indexed Silicon Prawn Yamaha table includes a YM3420 row, but the public page fetch returned 403 and no actual die image or tracing was acquired. Other Yamaha DAC datasheets and later patents do not establish this chip's architecture. The earlier [US4928569A envelope-mute example](opu-envelope-evidence-20261018.md) remains an unlinked Yamaha-era mechanism analogy; its −60 dB example is not a model-number identification. This is a bounded source gap, not proof that the material does not exist.

## Reproduction and next evidence

The [machine-readable ledger](dac-endpoint-evidence-20261019.json) contains all fixed-window levels, left/right checks, background bands, source hashes, raw-recompute receipts and source-search limits. Original media and analysis artifacts remain ignored under `build/dac-endpoint-evidence-20261019`; they are not shipping resources. The local plot is `selective-loss-and-background.png` there. `measure_endpoint.py` repeats the calculation from the already retained float decodes and joint-curve archive.

The most useful controlled extension to the [capture protocol](hardware-capture-protocol-20261018.md) is a paired endpoint sequence: independently authored pure carrier, LKS0, fixed RR/pitch/velocity, several carrier TL values, then the same weak release with a stronger nonharmonic held note. Repeat dry and with physical Reverb on, without changing capture gain or normalizing individual notes. A second analog-volume setting tests recording-domain thresholds. Explicit note-offs, comfortably fewer than twelve voices, full tails and unchanged clock/gain are necessary. Until that evidence exists, the waveform ending is real in the shared source chain but its hardware location and numerical rule remain unknown.
