# Sine99 cross-note distortion: estimator qualification failed

**No source-audio distortion result is claimed.** The fixed estimator produced false mixed-note sideband coefficients on known linear chorus and detuned independent-tone controls. It failed its prospective qualification, so the retained recording PCM was never opened. No production DSP, UI, host state, preset or artificial-noise behavior changed.

The [complete ledger](sine-crossnote-imd-2026-10-19.json) retains all11 qualification cases,33 fixed-support fits,66 witness rows, source/code bindings, native controls and the failure. The [prototype](../../Tools/prototypes/sine-crossnote-imd-20261019/README.md) preserves the fixed design and reproducer.

## Why this chord needs a guarded estimator

The already reused exact-device Sine99 chord contains MIDI39/75/79/87. The previous [release](exact-sine-release-2026-10-18.md), [codec](codec-tail-audit-2026-10-18.md), [capture](envelope-capture-forensics-2026-10-18.md) and [endpoint](dac-endpoint-evidence-2026-10-19.md) ledgers establish known Chorus/Reverb-on state, uncertain actual gates, prior tails and an unknown recording/master chain. AAC and Opus are two encodes of the same upload, not independent hardware recordings.

The proposed quadratic cross-note witnesses were the sum and difference of non-octave-related MIDI79 and39:861.772618 and706.209126Hz. However, bass39’s eleventh and ninth harmonics sit only6.173413Hz below those respective frequencies. MIDI75 and87 are exactly bass39’s eighth and sixteenth harmonics. Separate fitted lines therefore cannot be called isolated voices. Unknown native sampling/aliasing adds another unresolved source of translated oscillator content.

## Prospective design and controls

Before any controls or source PCM read, the design froze three held supports: final-chord onset+[0.10,0.40],+[0.12,0.38] and+[0.14,0.36]seconds. Frequencies remained equal-temperedA440; no pitch, onset, phase or rate search was allowed. The joint squared-Hann fit retained43 independent current/prior-note harmonic nuisance lines and the two witnesses. Every sinusoid had constant/linear/quadratic complex-envelope terms, plus a slow quadratic trend:273 columns.

Qualification required condition number≤1e7, every negative witness≤−65dB relative to the largest fitted primary, and recovery of declared global-quadratic positive controls within20% complex-amplitude error and0.20radian phase error. All cases/supports had to pass before source analysis. The design SHA256 is`31dad8c2db647e1567a1ca9af7c0d79ffee77592c8bafa4fe8f12718366cf113`.

The synthetic negatives include independent per-note harmonics, independent nonlinear waveform shaping, small unequal detuning/common drift, and a purely linear variable delay. Positives inject known quadratic mixing, including after linear chorus. Four native controls use the current held pure-sine DSP with dry output, circuit, Recorded chorus, and circuit plus Recorded chorus; drive/limiter/noise/LFO are disabled. They do not assert that the current chorus is the exact hardware implementation.

## Qualification result

| Fixed support after onset | Weighted design condition | Required maximum |
|---|---:|---:|
| 0.10–0.40s | 3.25372e+08 | 1e7 |
| 0.12–0.38s | 1.01267e+09 | 1e7 |
| 0.14–0.36s | 3.92937e+09 | 1e7 |

All matrices retain numerical full rank, but fail the condition limit. Near-coincident harmonic/witness terms and polynomial envelopes are too poorly separated on this short chord for stable coefficient interpretation.

| Qualification case | Pass | Largest fitted witness, relative amplitude dB |
|---|---|---:|
| clean linear | Yes | -216.476 |
| independent harmonic | Yes | -122.304 |
| detuned harmonic | No | -35.750 |
| linear chorus | No | 14.391 |
| independent nonlinearity | Yes | -148.847 |
| quadratic positive | Yes | -47.982 |
| quadratic after chorus positive | No | 14.622 |
| native dry | Yes | -90.289 |
| native circuit | Yes | -77.416 |
| native chorus | No | 2.522 |
| native both | No | 2.620 |

The clean quadratic positive is recovered accurately: worst complex error0.73%, worst phase error0.0072radian. That success does not validate the estimator on the actual problem. The independent detune/drift negative produces a false sum coefficient as large as−35.750dB; linear synthetic chorus reaches+14.391dB. Native Recorded chorus also fails, while native dry/circuit controls pass. These numbers are unstable fitted coefficients, **not proof of real discrete intermodulation lines or gain exceeding the signal**.

## Separate native superposition diagnostic

After the estimator failed, a posthoc diagnostic compared the native four-note output with the sum of four separately rendered single-note outputs under identical controls/epochs. Dry, circuit, Recorded chorus and combined paths agree to relative RMS3.45–3.75e−8, with maximum absolute difference2.61e−8. This is consistent with float rounding and confirms implementation superposition for those controls. It supports interpreting their false witnesses as estimator failure rather than actual native cross-note nonlinearity. It says nothing about the physical keyboard’s linearity.

The first diagnostic was posthoc. An unnecessary unchanged repeat occurred afterward; its source/binary/settings and numerical result were already known. Both receipts and their hashes remain in the ignored supplemental artifact manifest. The repeat is neither independent nor prospective evidence and does not change the original chronology or estimator failure.

## Consequence

Captured source PCM was not analyzed under the failed method. There is no physical positive finding, upper bound or linearity claim. The result prevents mistaking a finite-window, time-varying chorus/leakage artifact for a hardware distortion mechanism. No basis/window/threshold was changed to rescue source analysis.

A useful discriminator needs longer unprocessed dry two-note recordings with known patch/gates and independently recorded single-note controls, avoiding octave/harmonic overlap. Alternatively, an independently constrained time-varying output transfer would be needed before interpreting this short chorused chord. Even a qualified positive could not locate keyboard versus interface/master nonlinearity or identify DAC bits. No new capture protocol is created here.

Ignored artifacts: `build/sine-crossnote-imd-20261019/`. The prototype tool refuses to overwrite its completed result. No source media or synthesized control audio is added to product resources.
