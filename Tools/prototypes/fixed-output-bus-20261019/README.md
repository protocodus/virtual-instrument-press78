# Fixed output bus prototype — 19 October 2026

This causal wrapper makes other host rates follow the existing 48 kHz instrument. It does **not** identify a Yamaha clock, DAC format, analog circuit or envelope law. The entire underlying engine remains unchanged and runs at 48 kHz. Its common FM clock control still varies digital time internally; the output circuit and chorus remain in physical time.

At exactly 48 kHz, audio and all events delegate directly to the old engine. At other rates, a final stereo converter follows the complete output chain. Events are applied to the next 48 kHz physical frame after flushing earlier frames under the old state. Integer rates use exact quotient/remainder arithmetic. Other binary64 rates use a portable two-limb integer division; no `__int128`, long-double assumptions or epsilon snapping are required. This preserves the old engine's internal fractional-clock event behavior rather than silently repairing it.

The converter is a Kaiser-windowed sinc with cutoff `0.95 * min(1, hostRate / 48000)`, half-support `ceil(96 / ratio)` and a shared immutable table. The 1024-point-per-sample table occupies 393,220 bytes; it has no runtime initializer. A 2048-frame stereo history keeps the raw wrapper at 193,792 bytes and the protected wrapper at 193,816 bytes, before any host-wrapper overhead.

| Host | Added physical delay | Total nominal delay | Reported host frames |
|---|---:|---:|---:|
|8 kHz|12.000 ms|12.667 ms|102|
|44.1 kHz|2.188 ms|2.854 ms|126|
|48 kHz|0|0.667 ms|32|
|96 kHz|2.000 ms|2.667 ms|256|
|192 kHz|2.000 ms|2.667 ms|512|

The 32 inner ticks retain the existing clock-dependent variation. These are nominal delays, and the exact-48 bypass deliberately creates a latency discontinuity when changing host rate. Reprepare/reset must be handled by the host.

## Evidence

[The complete receipt](results.json) binds sources, prospective designs, archived failures and individual results. All original limits were retained:

- All eight previously frozen complete 48 kHz performance WAV hashes match. No recording score, event time or factory parameter was changed.
- 2,019 native checks cover control/event boundaries, 48 kHz identity, split blocks, panic/reset, null and aliased outputs, long counters and allocation-free processing. The byte-identity fixtures cover 11,520,000 bytes. The matching memory/undefined-behavior sanitizer suite passes.
- An independent 790-case Python rational oracle checks exact floor, ceiling and fractional positions across 79 rates, including rates immediately beside 48 kHz and timestamps after seven days.
- All 13 supported test rates pass the declared converter gates: 0.01 dB gain error, 0.05° phase error, at least 80 dB image/stopband rejection. Normal rates from 44.1 kHz cover 20 Hz–20 kHz; lower rates cover 0.8 of their Nyquist frequency. Measured rejection exceeds 100 dB. This is conversion quality, not removal of aliasing already produced inside the old engine.
- Native sharp-wave output differs from independently evaluated double-precision sinc/Kaiser output by at most `3.663e-7`; the complete engine comparison peaks at `2.078e-7`. An independent SciPy polyphase calculation is also retained, with its own transition stated.
- The raw converter can overshoot: bounded synthetic inputs reach 1.644. The measured coefficient L1 bounds and an independent analytic calculation explain those peaks; no gain normalization or hidden clamp conceals them.

`GuardedOutputBus` adds an explicit software safety rule. With `outputLimit=true`, only reconstructed values outside ±1 are hard-clipped. Nonfinite faults become zero. With the limiter off, all finite output is unchanged. The 48 kHz branch delegates directly. This is **software output protection**, not Yamaha distortion or a second soft limiter.

The 65 guard scenarios and separate edge checks pass, including live limit toggles, nextafter boundaries, signed zero, NaN/infinities, allocation checks, block splitting and null/aliased output. Extreme 12-voice, gain-2, circuit-bypass, wide-chorus, drive-0 signals can reconstruct to 2.169 even after the inner limiter; the guard clips 245,292 channel-samples across the tested rates, with maximum change 1.169. Those deliberately severe conditions show a real clipping tradeoff. Limiter-off output reaches 28.602 and remains byte-identical to the unprotected reference. Drive-1 and low-gain fixtures do not activate the guard. Both native and sanitizer guard runs pass.

Local 64-frame performance tests cover 15 rates and one/twelve voices. Worst mean wall/audio time is 0.1263 at 192 kHz with twelve voices; 44.1 kHz/twelve voices is 0.0721 and direct 48 kHz is 0.0433. Scheduler outliers exceed individual block deadlines. This is a research sanity check on the machine recorded in the receipt, **not** a Reason/AOT or hard real-time guarantee.

## Preserved failed attempts

The initial two-ULP timestamp snap returned the wrong floor at 48,000.25 Hz after seven days plus one host frame. The error was only about 0.11 ns but failed the exact causality contract. Its full source and witness remain archived. Exact rational arithmetic replaces it.

The initial 256-point table passed frequency-response gates but failed the sharp-fixture absolute error limit (`7.372e-6` versus `2e-6`). Increasing table density fourfold fixes interpolation accuracy without changing the filter shape, support, cutoff or latency. The original source and results are preserved. An early NumPy-scalar JSON serialization error is retained separately; its correction did not change numerical results.

## Production equivalence and latency correction

The separately authorized production wrapper is now [Press78OutputBus.h](../../../Source/DSP/Press78OutputBus.h), with its own deterministic kernel generator. The legacy `Press78Engine` files remain byte-identical. [Production validation](../../../Tests/results/output-bus-production-20261019.json) passes all ten CTest targets in Release and ASan/UBSan, including 277 output-bus checks and 12,515,880 compared production/prototype bytes. The native renderer now uses this public wrapper.

A new independent production test found a **metadata-only** issue at 24 kHz: floating-point evaluation reported 113 frames for an exact 112-frame nominal delay. Both prototype and production getters now compute the ceiling using exact binary64 integer arithmetic. No audio, event, kernel, guard or 48 kHz branch changed. The old headers and failed logs remain mapped in [the correction record](latency-correction.json), including the historical root-audition source bindings. This record supersedes the 24 kHz integer-latency field in the earlier frozen performance receipt. Thirty-two independent rational boundary cases include neighboring floating-point rates around 24/48 kHz.

The original [prototype receipt](results.json) remains immutable. Native Reason/AOT, Windows and delivery validation belong to the parent integration workflow and are not asserted by these standalone checks.

## Reproduction

The files here are isolated research tools, with heavy outputs under ignored `build/fixed-output-bus-20261019`. The checked-in `KernelTable.h` is generated deterministically by `generate_kernel.py`. Compile `Probe.cpp`, `GuardProbe.cpp`, `Performance.cpp` or `ProtectionEdges.cpp` as C++17, include this directory and `Source/DSP`, and link `Source/DSP/Press78Engine.cpp` where needed. `Probe` exposes `selftest`, `coeff`, `src`, `full` and `perf`; `analyze.py` provides independent response, component, full-engine, overshoot and polyphase checks. `verify_bounds.py` independently computes the analytic L1 bounds. The retained bindings contain exact command/source identities. `full_performance.py` additionally requires the local frozen research event files; it never downloads or redistributes media.

Production promotion was explicitly authorized after prototype validation; native SDK and delivery validation remain separate parent-controlled steps. No artificial noise, FM-law change, Reverb algorithm, fitted EQ or third-party recording parameter is introduced here.
