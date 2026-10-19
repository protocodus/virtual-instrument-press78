# Assumed two-stage release scenario

This is one research-only listening option, authorized as an estimate. It is not a recovered YM3420 envelope algorithm or a production correction. The shipping source remains unchanged. The [retained evidence review](../../../Docs/research/reverb-release-evidence.md) describes the Yamaha TX81Z carrier-triggered envelope-Reverb precedent and the PSS-780 owner's qualitative envelope observation. Neither identifies an 18 dB threshold or RR4 rate in the PSS-780. The [earlier experiment](../../../Docs/research/reverb-envelope-benchmark-2026-10-18.md) combined that analogy with a threefold timing slowdown and had substantial regressions. This option deliberately does not reuse that slowdown, its attack changes, grids or results.

The assumed Reverb-on behavior uses the carrier's absolute internal envelope attenuation before the current internal sample. At or above 18 dB during release, both operators' release slopes are limited to their own native RR4 slopes. A release that is already slower stays slower. Each cap uses that operator's existing note and rate-key scaling through the actual native `Envelope::updateRelease`; no rate equation is reimplemented. At RKS0 the unchanged model predicts 45.254834 dB/s for RR4. The former 15.084945 dB/s figure included the old threefold duration multiplier and does not apply here.

Use this exact substitution inside a temporary copy of `Press78Engine::Voice::next`, replacing only its original two envelope calls. Include `EnvelopeHypothesis.h` by an absolute path in that generated source; leave the original shipping translation unit and baseline build unchanged.

```cpp
const bool knee = research::AssumedEnvelope::engaged(
    carrierEnvelope, released, true); // explicit research Reverb ON
const double em = research::AssumedEnvelope::next(
    modEnvelope, patch.modulator, note, released, knee);
const double ec = research::AssumedEnvelope::next(
    carrierEnvelope, patch.carrier, note, released, knee);
```

The single `knee` snapshot is shared by both calls. This is a carrier-coupled scenario, not independently triggered operator knees. Pass `false` to `engaged` for the Reverb-off parity control. The helper has no mutable global flag, hidden patch-bit inference, scheduler or independent oscillator. The renderer must label Reverb as an explicit assumed performance state. It must not reinterpret factory Sustain as Reverb or describe this option as an implemented command-register Reverb response.

The wrapper temporarily changes the actual native envelope's release coefficient for its actual `next` call and restores that coefficient immediately afterward. A copied envelope is used only to calculate the native RR4 coefficient; that scratch copy never advances. Native attack, D1/D2, output conversion, waveform generation, phase, feedback, voice allocation, resampling, analog output and the 96 dB carrier retirement endpoint remain the shipping implementation. Ordinary RR/SRR selection is performed by the existing engine, then limited only when the assumed knee is engaged. The current MIDI-note-based RKS law and 48 kHz internal cadence remain inherited hypotheses.

The following boundary behavior is intentional:

- The threshold excludes operator TL, velocity, AM and output gain. It is not 18 dB measured from the note-off amplitude.
- A key released with carrier attenuation already at or above 18 dB receives the cap immediately, including during a slow attack or after held decay. A still-held voice receives no release cap.
- The threshold is checked before advancing either envelope. A native step that crosses 18 dB receives the ordinary slope on that step; the cap begins on the next internal sample. No fractional-sample knee is invented.
- The modulator receives its own RR4/RKS ceiling when the carrier triggers it. A muted modulator or carrier TL does not select the trigger. Carrier-only focus patches cannot establish operator coupling.
- A native envelope already in release stage 3 remains in release if a direct caller later passes `released=false`. The helper preserves that behavior rather than inventing a gate-reset rule.
- Disabled or finished envelopes use native `next` directly. The cap does not revive a finished voice, rescue a key-off before an instantaneous first attack, reset envelope attenuation or extend the endpoint.
- A live RR/SRR/RKS update retains its ordinary coefficient. The next sample recomputes the cap from current operator settings. Explicit Reverb-off continuation immediately resumes that ordinary coefficient without resetting envelope or oscillator history.
- Reverb toggling, latched versus live knee state, exact threshold, exact RR mapping, chip keycode and hardware timing are not identified. This scenario chooses a stateless live threshold; no extra latch, delay line, artificial noise or hidden memory fault is added.

Fresh sparse-gate renders should compare unchanged A against this single B with identical notes, controls and output processing. They test the audible consequences of the assumption. They cannot validate a PSS-780 hardware release law without independent controlled captures. Do not rerun historical grids or imply that an estimated choice has passed their former adoption criteria.

Native-envelope-only validation passed in optimized and AddressSanitizer/UndefinedBehaviorSanitizer builds, with 1,644,071 assertions each. The declared matrix covered all 128 MIDI notes, four RKS values and 16 RR values (8,192 configurations), including 786,432 exact native Reverb-off output/state ticks and 8,192 capped-release controls. It also checked the shared pre-step knee, native RR4/RKS ceiling, already slower releases, live RR updates and immediate Reverb-off continuation, disabled/finished behavior, coefficient restoration and the unchanged native endpoint. Compiler and runtime diagnostics were empty. These tests called the actual native envelope implementation; they rendered no audio and establish software behavior only. The pre-execution design/source binding, test source, unchanged pre-validation note and both receipts are retained under `build/assumed-hardware-envelope-20261019/`. The renderer and listening results are separate work.
