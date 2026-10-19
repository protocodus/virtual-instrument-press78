# Press78 0.1.1 — listener-selected release and output

19 October 2026. Canonical DSP version **0.1.1**; Rack adapter identity **0.1.1b1**.

The user chose **“ok apply B”**, authorizing adoption of both B options from the [release and output auditions](../research/assumed-hardware-auditions-2026-10-19.md). The choice supplies the product direction for longer release tails and shared asymmetric output headroom. It was made by ear after explicitly allowing estimates; it does not establish a measured hardware-fidelity improvement. The [decision log](../decisions.md) records that authorization.

During the selected release behavior, one snapshot of the carrier's absolute internal envelope attenuation is taken before either operator advances. At or above 18 dB in release, both operators use the slower of their ordinary release and their own native RR4 rate, including existing note/RKS scaling. Slower releases stay slower. TL, velocity and output gain do not select the knee. Attack, held decay and the native retirement endpoint remain unchanged, and the previous threefold release-duration experiment is not adopted. The audition explicitly assumed Reverb on; this is a sibling-inspired envelope choice, not a recovered YM3420 Reverb algorithm.

The selected output curve processes the shared mono sum before the existing sibling analog filter:

```text
t = tanh(x / H)
y = H * t / (1 + tanh(b) * t)
H = 1, b = 0.14
```

These normalized constants and the insertion point are chosen assumptions. The curve has unity small-signal slope, maps zero exactly to zero, and introduces level-dependent compression and asymmetry across the shared voices. It adds no hiss, hum, dither or random excitation. It does not establish converter bit depth, measured voltage fluctuations or a detailed target circuit.

The native `Controls::envelopeReverb` setting defaults to `true` in both hosts. It adds no persistent host parameter or UI control; native diagnostic and reference callers can set it to `false`. The existing `outputCircuit` control now switches the selected headroom curve and sibling filter together through its existing smoothed bypass. That branch continues processing while bypassed, retaining the filter history for a warm re-enable. The native `press78_render --transparent` option turns both selected models off for reference rendering.

Existing patches can sound different on upgrade: the release model defaults on, and an enabled output-circuit model now includes the selected headroom curve. This compatibility change is intentional under the user's B choice.

The frozen research A/B WAVs, gain trims, keys, protocol, receipts and failed attempts remain unchanged. The envelope and output Bs were auditioned separately. Their [independent review](../validation/assumed-hardware-independent-review-2026-10-19.json) and [supplemental checks](../validation/assumed-hardware-supplemental-validation-2026-10-19.json) establish the declared research implementation and artifacts; product-integration tests are a separate validation step. No new recording fit, historical benchmark rerun or combined hardware score follows from this choice. The research command consumer and allocator policy are outside this adoption.

The [product-integration receipt](../validation/selected-character-adoption-2026-10-19.json) records all 16 native tests passing, including the complete factory-demo check, plus 15 tests under ASan/UBSan and float-cast-overflow instrumentation. The new character suite covers the cached cap, live model changes, shared output/filter ordering, bypass, silence, reset and allocation safety. The Real-profile native performance probe records zero block-deadline misses in all six selected workloads at 48/96 kHz. These are development-machine checks, not Reason host or target-chip performance evidence; Rack packaging is validated separately.
