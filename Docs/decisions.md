# Press78 — decision log

Directions chosen by ear, recorded per the A–Z listening-test convention in
the repository's `CLAUDE.md`. A choice made by ear is recorded as made by ear.

## 2026-10-19 — release knee and shared output headroom

The user chose **“ok apply B”** after the [assumed-hardware auditions](research/assumed-hardware-auditions-2026-10-19.md). This authorizes adopting both separately auditioned B assumptions:

- A carrier-triggered release knee at 18 dB of internal envelope attenuation. Both operators then use the slower of their ordinary release and their own native RR4 rate, including existing note/RKS scaling.
- Deterministic shared output headroom with normalized `H = 1` and shape bias `b = 0.14`, before the sibling analog filter.

This is a listening preference under the user's explicit permission to estimate unknown behavior. The constants and placement remain assumptions rather than measured PSS-780 properties. Both changes preserve the absence of additive noise. The separate A/B sets, their level matching, keys and results remain frozen; this decision does not rewrite those historical experiments or promote the research command frontend into production.

Adopted for canonical DSP version **0.1.1**, with Rack adapter identity **0.1.1b1**. Existing patches intentionally take on the selected behavior when its models are enabled. See the [adoption note](release/assumed-hardware-adoption-2026-10-19.md) for defaults, reference bypass and validation boundaries.

## 2026-10-29 — release knee off

The owner heard a reverb or release tail on every Press78 sound and asked for it to go. It was the 2026-10-19 release knee above: once the carrier had fallen 18 dB after key-up, both operators released no faster than their native RR4 rate, so Init's C3 fell 60 dB in 0.94 s instead of 0.05 s. This reverses that half of the B choice by the owner's word, not by a listening test against a new candidate; the shared output headroom stays. Adopted for canonical DSP version **1.0.1**: `Controls::envelopeReverb` defaults to off and the Rack adapter sets it off.
