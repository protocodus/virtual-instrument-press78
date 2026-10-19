# Reverb knee domain: the current source cannot choose it

**No EG-state or total-attenuation knee is adopted.** Exact per-note level commands improve the known inputs, but pitch and level command still vary together in the single Sine99 patch. A key-dependent EG knee can reproduce a total-attenuation knee exactly. This is a structural limitation, not another failed audio fit.

The [complete ledger](reverb-knee-domain-2026-10-19.json) binds the prior release/codec/RKS/capture studies, complete frontend, lookup helper and retained command observations. No saved curves or captured PCM were opened; no estimator, audio, original-CPU rerun or algebra test harness was created. Production, UI, host and noise behavior are unchanged.

## What the commands now establish

Sine99 has carrier rawTL13 and LKS`0xB9`. The [verified integer lookup](opu-level-command-path-2026-10-19.md) gives:

| Mapped note | Lookup | Offset | Seven-bit carrier command | Reverb-on full word |
|---|---|---:|---|---|
|39|lower row9, column7|+4|17+u|145+u|
|75|upper row11, column7|+1|14+u|142+u|
|79|upper row11, column9|+2|15+u|143+u|
|87|upper row11, column13|+3|16+u|144+u|

`u` is one unknown common Mode00 volume addend under the existing stable-volume assumption. Documented indices1–9 yield32,28,24,20,16,12,8,4,0; constructed index0 also yields32 and is not an inferred boot setting. No command saturates in this range. Thus39-minus79 is exactly **two command units** despite unknown common volume. The command-to-attenuation map remains unknown, so this cannot be relabeled1.5dB. The separate Reverb bit128 does not identify where an internal threshold is tested.

All640 helper entries were compared with the already retained original lookup outputs. Existing original serial traces at Sine99 note74 confirm base14 plus every volume addend. That retained main serial sweep did **not** directly include39/79/75/87: their values above are compositions of the verified lookup/helper, not newly executed serial witnesses. No original firmware was run. Source Mode00, unchanged note mapping and common volume remain recording assumptions, not wire logs.

## Why relative knee levels do not settle the domain

Let`C_n` be the recovered command,`A(C_n)` its unknown static attenuation,`E_n(t)` the internal EG attenuation, and`T` a symbolic total-domain knee. A conditional log-level observation is:

```text
L_n(t) = g_n - A(C_n) - E_n(t) + q_n(t)
```

Here`g_n` is static frequency/capture gain, while`q_n(t)` represents possible moving effects, capture processing or overlap. If the held EG starts at0 and`q_n` stays constant, plateau-relative drop equals`E_n(t)`: static gain and staticTL cancel within each note. A strictly pitch-independent EG knee would therefore predict the same relative drop across notes. Different rates change crossing time, not that drop.

But a total-domain trigger is:

```text
E_n(t) + A(C_n) >= T
```

Define a competing EG-state knee`K_n = T - A(C_n)`. Its condition`E_n(t) >= K_n` is identical at every time. With the same initial states, rate functions and output path, **the complete curves coincide**. No numerical threshold, cap rate or hardware law is assumed in this counterexample. It does not assert that the hardware has a key-dependent threshold; the current single-patch source cannot exclude that alternative.

Every pitch has only one key-scaled command in this comparison. Consequently an apparent command dependence can also be pitch/key dependence. Published rawRKS0 audible slopes already differ across pitches, without establishing the internal mechanism. Unknown`A`, moving Chorus/Reverb, previous-note tails and component mixtures add further limits. Static gain alone is not the obstacle to a plateau-relative comparison.

MIDI39/79 are the useful non-octave pair, but39 has prior same-pitch history and few cycles in short windows;79 has nearby/preceding harmonic contaminants.75 and87 coincide with bass39’s eighth/sixteenth harmonics, and75 is retriggered. They are frequency components rather than independent isolated-voice controls.

## Relation to the previous cap experiment

The [earlier three cap candidates](reverb-envelope-benchmark-2026-10-18.md) all imposed internalEG18dB, excludingTL/velocity/AM, with rawRR4 through the assumed rate law. They compared carrier versus independent triggers and base timing variants. They did **not** compare total-attenuation and EG-state domains. Their reused-tour calibration and mixed scores cannot promote either physical domain. The later component endpoints likewise do not identify the early knee’s domain.

## Missing discriminator

The required contrast is **different verified level commands at the same pitch**, crossed with **equal final commands at different pitches**. Keep raw rates/RKS, initial/gate state and capture fixed; measure plateau-relative changes as well as timing. Separate Reverb and Chorus states, use stable unprocessed direct output and sufficient gaps/single-note controls to remove older tails. This breaks the command/pitch confounding and tests effect state independently.

The existing [capture fixture](hardware-capture-protocol-2026-10-18.md) is a starting point, not proof that these conditions have been recorded. No hardware-access request or new capture protocol accompanies this note. The defensible current result is the exact command contrast and the explicit remaining non-identifiability.
