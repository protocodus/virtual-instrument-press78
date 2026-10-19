# Repeated-note allocation and phase audit — 2026-10-19

The final Sine Wave 99 repeated note has a measurable amplitude interruption and a carrier-phase discontinuity. It does not simply continue the old tone unchanged. This is evidence to investigate same-pitch retrigger handling, but it does not identify whether the keyboard reuses a voice, kills a previous voice, steals one, or receives the note-off and note-on at different actual times. No allocator or phase-reset rule is adopted in this pass.

This is source analysis only. DSP, factory data, host state, alignment, builds and packages are unchanged. The [JSON record](retrigger-allocation-audit-20261019.json) includes the frozen protocol, all accepted/rejected estimator configurations, explicitly exploratory sensitivity checks and file hashes. This source was already used for calibration; it is not an unseen recording holdout.

## Protocol frozen before inspecting these windows

The source is the original [AndrewsVintageKeyboards PSS-780 recording](https://www.youtube.com/watch?v=ONfIvtDOog0), with the existing Eugenia MIDI metadata and frozen mapping:

```
source seconds = 0.8906462238832541 + 0.9998070138348876 × MIDI seconds
```

Protocol freezing occurred at 2026-10-18 22:41:35 UTC, already 2026-10-19 locally. Selection used metadata, not audio: all Sine99 same-channel/same-pitch notes with a predecessor ending within 0.1 ms of the new note, plus the gapped MIDI67/75 pair at 180.855717 seconds. The resulting eight note-cases were:

| New nominal source time | Pitch | Prior-off/new-on gap | Role |
| --- | ---: | ---: | --- |
| 176.224263 s | 70 | 0 | Corroboration |
| 176.885899 s | 63 | 0 | Corroboration |
| 176.885899 s | 67 | 0 | Corroboration |
| 177.988626 s | 68 | 0 | Corroboration |
| 178.650262 s | 68 | 0 | Corroboration |
| 180.855717 s | 67 | 0.441091 s | Late-tail retrigger control |
| 180.855717 s | 75 | 0.441091 s | Late-tail retrigger control |
| 181.737898 s | 75 | 0 | Primary test |

The primary old MIDI75 begins at 180.855717 seconds and ends at the same inferred MIDI time as the new MIDI75 begins. Both are channel0, velocity127, with unchanged patch. The new gate lasts approximately 441.1 ms. New MIDI79/87 and bass39 also begin at this boundary. These are inferred sender gates, not recorded hardware arrivals; the earlier audit established tens of milliseconds of local delivery uncertainty.

The predeclared observables were fixed-frequency complex amplitude, phase, and the trajectory before/after a common measured change. No synthesis model, per-model shift, phase, gain or frequency was fitted. Local observed activity was allowed to be measured in the same fixed +20–100 ms interval, explicitly separate from the nominal MIDI boundary.

The first estimator used simultaneous sine/cosine least squares plus DC, Hann-tapered on both signal and basis, at all metadata fundamental pitches active or released within the preceding two seconds and starting in the following 250 ms. The eight, twelve and twenty millisecond windows advance by 1 ms. Coefficients are rotated back to absolute source-time carrier phase, preserving phase comparisons between frames. Left, right and arithmetic mid are evaluated separately. Configurations with design-matrix condition number above 100,000 are rejected as frozen in the protocol.

## Conditioning limits the multi-note comparison

Only two of 24 case/window configurations pass that condition limit: MIDI70 at 176.224263 seconds with the 20 ms window, condition approximately 36,802; and the primary MIDI75 at 181.737898 seconds, condition approximately 1,448. The other 22 configurations are retained as rejected, not silently simplified or reclassified. Close bass frequencies make short-window joint separation ill-conditioned even when the target pitch itself is well separated.

The rejected cases provide no clean joint-estimator allocation evidence. Later single-target demodulation is reported as exploratory sensitivity analysis, not a substitute confirmation for those cases. In particular, MIDI68 is close to other previously sounding pitches, so its single-target trace can contain beating from another note. A quiet old gapped tail also provides a poor reference phase.

An initial frozen-protocol expectation that the primary pitch would lack a lower-note octave-harmonic confound was too broad: MIDI39's eighth harmonic and MIDI51's fourth harmonic coincide with MIDI75. These are a sine-carrier patch's higher output harmonics rather than additional fundamentals, but their level was not independently bounded here. The original frozen file is retained unchanged, and this qualification is explicit in the JSON.

## Primary MIDI75 observation

The 20 ms joint estimator's largest four-millisecond complex change is at nominal time +62.0 ms. Its amplitude minimum is at +59.0 ms, source approximately 181.796896 seconds. Arithmetic-mid magnitude falls from a fixed pre-window median of −20.37 dBFS to −31.38 dBFS, a drop of 11.01 dB. It then returns to approximately −20.3 dBFS. Individual channels also have a dip, although Chorus changes their baseline level and phase substantially.

The old and new stable arithmetic-mid phases have almost the same slope relative to nominal MIDI75 frequency: −0.7141 and −0.7243 Hz in the separate fixed nominal windows −120 to +20 ms and +80 to +200 ms. Extrapolating these descriptive straight phase trends to the measured change gives a phase difference of 1.220 radians, approximately 70 degrees. This is a phase discontinuity relative to continued old-tone motion; it does not prove a reset to any particular hardware phase. Actual new-note arrival is not known to a carrier cycle.

Those phase regressions were declared after the first plots and are exploratory observations. They do not alter the nominal frequency in the estimator, change MIDI alignment, or optimize a model. Their phase regressions have R² 0.9986 and 0.9888. The mean old/new stable magnitudes are −20.37/−20.33 dBFS.

A simple geometric check helps interpret the dip. An instantaneous transition between equal-magnitude phasors separated by 70 degrees, averaged with positive scalar weights, has a minimum magnitude `|cos(70°/2)|`, approximately −1.73 dB. The observed 20 ms dip is substantially deeper. Therefore an equal-level phase step with no amplitude interruption is insufficient by itself under that restricted model. Different envelopes, effects memory, actual off/on separation and interference remain outside that geometric test.

## Exploratory estimator sensitivity

After observing the primary dip, a separate protocol declared fixed-target demodulation to check that it was not solely an ill-conditioned joint-basis artifact. Each channel is multiplied by the nominal carrier's complex exponential and passed through a fixed fourth-order Butterworth lowpass forward and backward, using 60, 90 and 120 Hz cutoffs. A full second of source context guards filtering edges; the central 400 ms is inspected. There is no fitted frequency, phase, gain or time shift. Wider bands admit more nearby-note leakage and filter ringing, so the deepest value is not treated as the true physical amplitude minimum.

| Primary MIDI75 estimator | Mid dip relative to fixed pre-window | Minimum after nominal on |
| --- | ---: | ---: |
| Frozen 20 ms joint estimator | −11.01 dB | 59.00 ms |
| Exploratory 60 Hz demod lowpass | −10.81 dB | 58.73 ms |
| Exploratory 90 Hz demod lowpass | −17.00 dB | 59.31 ms |
| Exploratory 120 Hz demod lowpass | −32.95 dB | 59.35 ms |

All four show an interruption at nearly the same time. This supports a recorded transient amplitude loss rather than a pathology unique to the bass nuisance dictionary. The filter-dependent depth explicitly prevents claiming a calibrated zero or exact gap length. The nominal-time minimum is not a measured hardware key-off time.

The other accepted joint case, MIDI70, also changes phase and has an approximately 10.37 dB dip. Its extrapolated phase step is approximately 3.019 radians, close to 173 degrees. Unlike the primary75 case, its dip can readily be produced by averaging nearly opposite phasors. Its poorer conditioning, nearby fundamentals and proximity to the preceding program change further limit it as allocation corroboration.

## What this does and does not distinguish

| Hypothesis | Status from these observations |
| --- | --- |
| Same oscillator continues unchanged through the repeated note | Disfavored: primary75 has a clear carrier-phase discontinuity and transient amplitude loss. |
| Instant equal-amplitude phase-only replacement with positive smoothing | Insufficient for primary75's dip under the measured approximately 70-degree phase step. |
| A previous same-pitch voice is choked or reused | Compatible; not uniquely established. |
| Old and new voices always stack, with an ordinary released old voice | Not validated. A discriminating render or isolated capture is still needed; actual off/on delivery, phase, effects memory and allocation pressure prevent identifying a surviving old component from one same-frequency coefficient. |
| Voice stealing during the simultaneous chord change | Compatible; the hardware allocator and actual available voices are unknown. |
| A real note-off/note-on delivery gap despite same-tick source events | Compatible; actual hardware event arrivals were not captured. |
| Old sound remaining after a voice reset proves that its oscillator survived | Invalid inference: Chorus/circuit memory and the effect-enabled late tail can retain sound after voice replacement. |

Physical Reverb and Chorus are on in this recording. Their histories make early post-event behavior especially ambiguous; the exact Chorus delay and phase are not recovered by this analysis. Recording processing and coincident harmonics also remain possible confounds. The new phase cannot be called zero, free-running, or tied to a particular hardware slot from these data.

The current engine's stacking assumption should therefore remain an explicitly unverified part of the model. The strongest new fact is the primary recorded note's brief interruption, not a recovered allocator rule. A useful future control is one independently authored pure-carrier patch with Reverb/Chorus off: repeated same-pitch notes at known zero, 10, 30 and 100 ms off/on gaps, no coincident chord changes, plus a held nonharmonic note to expose common output gain changes. Actual transmitted MIDI timestamps and a dry line recording would separate voice reuse from delivery gaps and effects memory. This pass does not generate or transmit that sequence.
