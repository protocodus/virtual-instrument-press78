# Hardware model pass — 18 October 2026

The next native change should be a **causal, recording-calibrated chorus mode**, while retaining the existing Studio mode and the documented PSS-480 output surrogate. A complete physical PSS-780 chorus or DAC has not been recovered. This pass reuses the closed source/evidence set; it does not present a new hardware recording, new holdout or newly acquired exact schematic.

## Native model decisions

| Layer | Evidence | Recommendation |
|---|---|---|
| FM analog output | Original PSS-480 schematic, OPU TB pin42 through documented buffer/preamp network; exact PSS-780 parts identify related devices but its foldout remains absent | Retain existing six-SOS `AnalogOutput` as a **related PSS-480 circuit**. Its output is the volume-pot top, not a measured PSS-780 AUX response. Keep source loading/coupling and polarity. |
| Recorded chorus | One lossy PSS-780 video; six named training presets, nine fixed evaluation presets | Port frozen v3 to streaming fractional delay with a continuous global LFO. Name it **Recorded**, not identified circuit/BBD. Preserve Studio mode and prior defaults. |
| Refined recorded chorus | Same video and frozen linear branch correction; two-sided FIR | Keep offline benchmark/reference until a latency-aware implementation is justified. Do not silently drop future taps or call it zero latency. |
| Physical wet filtering | Original PSS-270 MN3206 filter/inverter/mixer | Useful separately testable sibling circuit. Do not append it to the empirical chorus: that would double-count unknown filter/capture response. |
| BBD clock/hold | MN3206 128-stage chip, MN3102 separate clock driver | Keep manufacturer-condition test scenarios separate. A fractional delay alone is not the validated sampled/held BBD plus reconstruction chain. |
| Noise | PSS-480 MNA resistor/opamp budget and MN3206 manufacturer limits are different sources | An optional circuit-noise generator can use actual transfer/covariance; preserve zero default and explicit electrical volts. No capture bed stacked on physical noise. |
| DAC/aging | YM3420 integrated conversion supported; resolution/update law unknown | No invented bit depth, companding, random memory errors, jitter PSD or age-dependent distortion. |

## Recorded v3: exact reference condition

For global phase `phi=2*pi*0.9546467517767424*t`, the effective delay in milliseconds is:

```
D = 1.0125596159214152
  + 0.0495126833338911*sin(phi) + 0.4943632948117077*cos(phi)
  + 0.05909196059342724*sin(2*phi) - 0.026924964944642096*cos(2*phi)
side = 0.5323384856515782 * mid(t-D) + 0.0935776226127722 * mid(t)
left = mid + side; right = mid - side
```

A dense full-cycle evaluation gives **0.4874479940–1.5114074457 ms**. The reference condition has depth multiplier 1 and side multiplier 1. New modulation controls should not quietly change those values when comparing against the capture. Input means a proposed recorded mid signal: arithmetic-mid preservation is a construction, not proof that an actual instrument has a perfect dry mid path. The phase origin is the beginning of the decoded recording, not a recovered power-on phase. Do not reset the LFO at every note or processing block. For new performances, a continuous arbitrary phase is acceptable and must not be called a calibrated reset state.

At 48 kHz, a fractional-delay ring needs only 73 history samples at the exact reference maximum, plus interpolation margin; other sample rates must scale delay in seconds. The frozen Python version uses linear interpolation. Matching it first gives a clear regression reference; changing interpolation is a separate, measured implementation choice. The live algorithm needs no artificial whole-output latency beyond the real wet delay. Streaming state should persist across arbitrary host block boundaries, including silent periods. Smooth mode/mix changes so automation does not expose discontinuities. The native event/transport clock and the reference's audio origin must be aligned explicitly for diagnostics.

This fit used presets 00,02,22,34,59,77 and 100–4000 Hz. It does not identify the oscillator resistor/capacitor network, instantaneous CP frequency, DAC, input voltage or high-frequency transfer. Do **not** calculate a claimed hardware CP by substituting its effective delay into64/D: the fitted delay also contains analog and capture phase. Source: [user-provided PSS-780 recording](https://www.youtube.com/watch?v=ONfIvtDOog0); frozen `Tools/reference/circuit/video_chorus_profile.json`.

## Why v4 has a latency requirement

`refined_chorus.py` forms a fitted branch response from seven taps spanning −0.5…+0.5 ms, then blends its correction through a zero-phase autocorrelation kernel. At 48 kHz the kernel has 2049 taps and center 1024 samples. Its positive lookahead plus the earliest branch tap is **1048 samples =21.8333 ms**. Delay both dry/mid and side by the same amount in a causal equivalent; delaying only side changes the model. A 32 ms context pad was the conservative offline crop protocol, not the minimum algorithm latency. Coefficients/tap times must be rebuilt or consistently resampled for other host rates. The bounded blend is calibrated100–4000 Hz and reverts toward v3 outside that band.

Diagnostic nine-preset mean side NRMSE improved 0.39324→0.28616 with the linear branch fit. Quadratic/cubic additions did not meet the predeclared cross-validation rule; the combined nonlinear candidate scored 0.28624 and was rejected. Those are observed-mid→side diagnostics from already-used material, **not** absolute native FM accuracy or independent new-device validation. Production's bounded-band correction and a direct unblended fitted branch are distinct outputs; do not mix their reported scores.

## Physical circuit facts and assumptions

The [original Yamaha PSS-270 schematic](https://github.com/fmillion/yamaha-pss270/blob/8943bf963f196f20b4e2fc714f15400db578891b/PSS270-Schematic.tif) shows the wet path: 0.1 µF coupling;100 kΩ bias loads; 22 kΩ+22 kΩ Sallen–Key with 12 nF feedback and 680 pF ground capacitor;47 kΩ/47 kΩ inverter with 220 pF feedback;0.1 µF output couplers;6.8 kΩ wet branches; shared 4.7 µF dry coupling into 8.2 kΩ branches;2.2 kΩ shunts and 100 kΩ pot loads. The exact postnetwork is implemented in `pss270_chorus.py`, and dry superposition in `sibling_output.py`.

The two wet channels are not exact negatives at all frequencies: the inverter's extra feedback pole gives residual wet mid/side around −29.68dB at 1 kHz and−17.71dB at 4 kHz. This is a useful concrete hardware improvement over a universal cancellation assumption. The unloaded Sallen–Key values imply f0 ≈2532.5 Hz/Q≈2.10, but that is not the complete keyboard cutoff. Its MNA uses ideal-on FET, AC-ground bias rails, an ideal voltage-driven BBD output and finite one-pole opamp macros. Unknown BBD output impedance, FET resistance, pre-BBD network and amplifier loading are excluded. Independent ngspice47 agrees with this declared network; that validates the solver, not PSS-780 component identity.

The visible related PSS-270 LFO has 330 kΩ/1 µF timing, three 100 kΩ Schmitt bias/feedback resistors and a follower; its clock-control area includes 390 kΩ,68 pF,27 kΩ, transistor and diodes. These values do not establish the exact PSS-780 clock trajectory. The PSS-480 AM board is not a proven identical PSS-780 chorus board; the recovered PSS-480 schematic has no MN3102/MN3206 chorus. [Original PSS-480 scanning post and schematic](https://forum.mamedev.org/viewtopic.php?start=10&t=1017).

The [Panasonic MN3206 datasheet](https://github.com/fmillion/yamaha-pss270/blob/8943bf963f196f20b4e2fc714f15400db578891b/datasheets/MN3206.pdf) gives 128 physical stages,10–200 kHz CP and 0.32–6.4 ms delay: **64 complete CP periods**, so40 kHz→1.6 ms and 100 kHz→0.64 ms. The [MN3102 datasheet](https://github.com/fmillion/yamaha-pss270/blob/8943bf963f196f20b4e2fc714f15400db578891b/datasheets/MN3102.pdf) distinguishes its oscillator from the opposite CP outputs: CP is half oscillator frequency. The OPU's5.5 MHz resonator is a separate clock domain.

Frozen BBD validation uses 320 kHz/800 kHz integration for 40 kHz/100 kHz CP, eight integration samples per complete CP. These rates and Kaiser8.6 rational resampling are numerical choices, not recovered DAC rates. Noncommensurate coarse grids previously generated spurious linear harmonics. Any native physical port needs persistent clock-edge state, sufficient interpolation/reconstruction, an actual sampled-hold path, and a measured latency contract for resampling. Do not paste the offline FFT/noise/resample API into a realtime callback. Exact clock-range or modulation values for this keyboard remain unknown, so no new physical chorus mode is recommended in this bounded pass.

## Noise and distortion scope

At 5 V,40 kHz CP, 1 kHz and 0.25Vrms input, MN3206 specifies typical 0.3%THD (maximum 2.5%). At100 kHz CP it specifies maximum 100 µVrms A-weighted noise. These are **different test conditions**, not interchangeable operating points or typical PSS-780 dBFS levels. The existing cubic is a single-point scenario whose compressive sign and third-harmonic distribution are assumptions; it does not reproduce the U-shaped THD/input graph or bias asymmetry. The existing Gaussian 20 Hz–20 kHz noise shape is likewise an assumption normalized to a maximum, not the chip's measured spectrum. Neither should become a hidden default. The recorded residual supplied no robust reason to add nonlinear wet terms.

A PSS-480 resistor/opamp noise budget is more directly grounded for the existing output surrogate: each real resistor contributes4kTR with its documented network transfer, and NJM4558 input-voltage noise is a declared manufacturer-typical scenario. It remains conditional on temperature, bandwidth, macro approximation and mapping of model units to physical input volts. A native implementation should reproduce the **stereo covariance**, not add one common white signal and call it circuit hiss. Its spectrum can be represented by a compact causal realization if validated against the frozen MNA PSD/covariance; the optional amplitude must remain zero by default. Captured side-dominant noise additionally contains unidentified power/ground, BBD and recording effects and cannot calibrate this source.

Exact PSS-780 parts confirm YM3420BF/C, NJM4558, MN3102/MN3206, a5.5 MHz ceramic resonator and a768K CSB768J.D resonator. The [exact service parts page](https://www.manualslib.com/manual/4045165/Yamaha-Portasound-Pss-780.html?page=12#manual) does not recover DAC resolution/update timing, resonator aging/jitter constants or normal memory-corruption behavior. Those remain unknown; no random bit-flip or bit-depth default follows from the age of the instrument.

## Acceptance for the next native pass

1. Recorded mode: sample parity with frozen v3 at 48 kHz, exact phase origin, arbitrary block-size invariance, silence/state continuity, no accidental per-note reset, and scaled delays at44.1/96 kHz.
2. Keep Studio behavior/defaults compatible; the recorded mode does not silently cascade the PSS270 wet filter or manufacturer noise fixture.
3. Repeat the fixed whole-performance observed-mid→side diagnostic and original65/93/97 demonstrations, explicitly describing reused polyphonic, effects-enabled lossy reference material.
4. Any circuit-noise port must report source units, sample-rate-consistent RMS/PSD and interchannel covariance, deterministic seeded continuity, zero-default behavior, finite output and state/memory cost. Preserve causal filters across blocks.
5. Continue to label the PSS480 output and PSS270 wet networks by their actual source instruments; do not promote surrogate or fitted behavior to exact PSS-780 hardware.

## Completed causal circuit-noise port

`Tools/generate_circuit_noise.py` now generates `Source/DSP/CircuitNoise.h` directly from the preserved PSS-480 MNA and `Tools/reference/circuit/output_stage.py`. This is an exact reduction/change of state coordinates followed by bilinear discretization, **not a fitted two-channel noise curve**. It retains 12 dynamic states and 14 separate resistor/opamp sources, including shared-front-end and independent-channel contributions. One-sided physical PSD uses unit-variance innovations scaled by `sqrt(sampleRate/2)`. Uniform PRNG innovations reproduce the model's second-order statistics; they do not claim a uniform physical thermal-noise distribution. The runtime performs no allocation, block normalization or sample-file playback.

The native object occupies **3,024 bytes**. `prepare(rate, seed)` configures the fixed-size causal matrices, `reset(seed)` clears state, and `process()` returns two electrical-voltage samples. All channels share the correct source injections and retain state continuously. A fixed public normalization constant, **11.968 µVrms**, is the original continuous-circuit 20–20,000 Hz integral. Scaling by `noiseRms / kReferenceRmsVolts` makes the existing UI amount a reference-band level, not a calibrated keyboard-voltage claim. Neither the reference constant nor source excitation is refitted per voice, clip or sample rate. The optional noise model remains disabled by default.

Finite-rate bilinear integration intentionally shares the analog-output model's warping limitation. Its predicted 20–20,000 Hz RMS is approximately **10.85 / 11.04 / 11.77 µV** at **44.1 / 48 / 96 kHz**, respectively, against the continuous circuit's 11.97 µV. Corresponding stereo correlations are approximately **0.0586 / 0.0578 / 0.0563**. The generator checks the full complex covariance against the direct MNA at bilinear-mapped frequencies; it does not claim a sample-rate-invariant physical spectrum or hide the difference with a gain boost. Frequencies above a host's Nyquist cannot be represented; at 8 kHz the reported integration band stops at 3.92 kHz.

Validation is in `Tests/results/circuit-noise-generated.json` and `Tests/results/circuit-noise-runtime.json`. Native sample parity passes at 8, 44.1, 48, 96 and 192 kHz. Independently sampled 20-second native fixtures at 44.1, 48 and 96 kHz match predicted RMS within 2%, correlation within 0.015, and five broad spectral-band powers within 0.9 dB; these are acceptance tolerances, not measurement error bars for the real keyboard. Repeated seeds are bit-exact. No recorded audio is embedded. Tests concern the declared surrogate/noise assumptions; omitted current noise, 1/f noise, BBD noise, supply coupling and the real PSS-780 board remain outside this model.

The input-voltage-noise assumption is the NJM4558 manufacturer's typical white-noise value, not a measurement of an installed vintage component: [Nisshinbo NJM4558 product specification](https://www.nisshinbo-microdevices.co.jp/en/products/operational-amplifier/spec/?product=njm4558).

A separate reviewer compiled the header and compared it against the **full MNA descriptor trapezoidal recurrence**, bypassing the generated reduced state-space implementation. All six rates passed, including the nonstandard 44,117 Hz case. Maximum absolute difference was 7.97×10⁻¹⁷ V, and maximum relative RMS difference was 1.58×10⁻¹². This independently verifies state reduction, the bilinear direct-feedthrough term, source scaling and output-before-state-update order. Preserved review: `Tests/results/circuit-noise-independent-review.json` (original review run under `build/hardware-benchmarks/noise-review-20261018/`). These checks establish numerical agreement with the declared **sibling model**, not the real PSS-780 noise gain.

No remaining physics blocker prevents the bounded Recorded-mode/circuit-noise implementation described here. The exact-board/DAC/BBD uncertainties above remain fidelity limitations, and do not justify silently changing the supported model or claiming a complete transistor-level replica.
