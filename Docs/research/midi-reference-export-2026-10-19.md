# Raw MIDI reference-event exporter — 19 October 2026

The new research exporter maps each original MIDI tick once and preserves its note-message order. Four separately named fixtures pass all metadata invariants and 41,553 independent checks. No audio comparison or production change has been made.

[Tools/export_midi_reference_events.py](../../Tools/export_midi_reference_events.py) consumes the hash-bound decoded-event artifact from the [source-order audit](midi-event-order-audit-2026-10-19.md). It reintegrates exact tempo fractions, orders note messages by tick/track/within-track ordinal, and maps each tick to one frame under each of the same four fixed timing scenarios. It uses actual off-event ticks, rather than onset plus a separately rounded gate. Mixed on/off messages at one frame keep their raw canonical order.

The existing Mode00 source filter 36–96 is unchanged. Each output retains 1,761 ons, 1,761 offs and the same 100 inferred patch-command payloads and frames. Program commands explicitly precede notes at the same frame. Raw MIDI channel numbers remain the last event field; they are not independent MIDI/CV owners. A future renderer must separately declare its channel/ownership policy.

All four exports preserve the exact old onset multiset and frames, all 193 contiguous same-channel OFF-before-ON boundaries, and the full canonical note order. None introduces same-channel held duplicate-ons. The genuine simultaneous MIDI 62 event across the two raw channels remains, as does its shared-MIDI key-edge behavior. No current event file or failed benchmark was rewritten.

The source and decoder/input hashes were frozen **before** any new fixture was emitted. Root source review preceded the one frozen export run. An independent reviewer then re-decoded the binary MIDI read-only, rebuilt all outputs and indexes in memory, and compared them byte-for-byte. Six additional independent guard cases and 20 producer synthetic assertions passed. The first producer test harness had a syntax error before assertions; its exact source and error record are retained. The exporter itself was unchanged, and the actual export had no failures.

The [machine-readable ledger](midi-reference-export-2026-10-19.json) binds source, protocol, all four event/index files, test history and independent receipt. Outputs stay ignored under `build/midi-reference-events-20261019/maps/`. The exporter refuses reused output directories, changed bound inputs/source, and research outputs outside this repository's `build/`.

To create a new export when the local audited decoded-event artifact is available:

```sh
python3 Tools/export_midi_reference_events.py freeze --out build/midi-reference-fresh
python3 Tools/export_midi_reference_events.py run --out build/midi-reference-fresh
```

This preserves the retained file's known within-track order. The canonical intertrack merge remains an explicit analysis choice; actual sender serialization, receiver masks and 2017arrival times are unknown. Program-first is likewise a declared convention for the existing inferred commands, not recovered physical ordering. These metadata checks do not measure oscillator phase, envelope behavior, audible program loading, or improved hardware fidelity. The prior allocator comparison remains failed for promotion; a new audio experiment needs a separate prospective design.
