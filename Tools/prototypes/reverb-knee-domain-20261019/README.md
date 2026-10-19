# Reverb knee domain: structural evidence capsule

This directory contains no DSP model, estimator or executable test harness. The existing source cannot identify an EG-state versus total-attenuation knee after allowing still-unidentified key/rate behavior. Adding a fitter would not remove that structural ambiguity.

See [the note](../../../Docs/research/reverb-knee-domain-2026-10-19.md) and [complete ledger](../../../Docs/research/reverb-knee-domain-2026-10-19.json). Existing exact lookup/helper composition gives Sine99 carrier commands39→17+u and79→15+u, with unknown common Mode00 volume addend. Command units are not calibrated decibels.

Only existing source/ledger/table/command records were read. The ignored `build/reverb-knee-domain-20261019/command-evidence-verification.json` binds the retained lookup and serial observations. No saved curves, captured PCM, new audio, CPU execution, production DSP, UI or host action occurred.

A same-pitch/TL contrast crossed with equal-command/different-pitch controls and independently separated Reverb/capture state is missing. No new capture protocol or hardware-access question is created here.
