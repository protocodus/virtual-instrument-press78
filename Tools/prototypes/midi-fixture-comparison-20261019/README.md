# Frozen MIDI-fixture experiment source

`runner-frozen.py` and `common-frozen.py` are the exact sources used for the completed 19 October 2026 experiment. They retain the original workspace/path assumptions and are audit snapshots, not standalone entry points. Their hashes are unchanged.

The current entry point is `Tools/benchmark_midi_fixture.py`. Its only migration changes are evidence-document lookup paths; the rendering, scoring, comparisons, limits and no-rerun rules are unchanged. It still requires the locally retained, hash-bound research corpus. No media or firmware is included, and this migration does not rerender an experiment.

See the [results](../../../Docs/research/midi-fixture-comparison-2026-10-19.md) and [migration record](../../../Docs/validation/research-layout-migration-2026-10-19.json). Original JSON receipts intentionally keep the paths and hashes recorded at execution time.
