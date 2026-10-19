# Conditional command-path recording benchmark

Research only. This compares the unchanged shipping Engine with the reviewed one-owner command consumer, using the same eight conditional fixtures: four fixed maps × two source-track orders. It changes bundled command policy, rather than isolating an envelope calibration. The original capture has Reverb ON; store-only Reverb cannot validate that missing audio law, envelope/DAC laws, phase reset or native cadence.

`design-frozen.json` fixes all 100 original supports, both prior Sine supports, controls, event/grid order and storage. Root's header-only correction preserves render 8,931,705 frames and binds source 8,927,609 frames independently: crop 32, score source length, ignore 4,064 remaining padding. Prior unexecuted protocol/runner versions and the initial compile failure remain under the ignored build directory.

Before approval, only synthetic parser/scheduler/metadata/storage tests may execute. `ContractTests.cpp` defaults to audio-free checks. `test_runner_guards.py` checks constructed approval/hash/budget/JSON failures; it never runs the benchmark or reads retained PCM. Strict prechecks pass 2,116 checks. The audio-contract mode processes synthetic audio only after the same root gate as source replay.

## Root execution gate

`run.py` requires a root-authored JSON receipt with this schema. Values must bind the current files, including the exact pure-precheck receipt; an example is deliberately not an approval:

```json
{
  "schema": "press78.command-recording-root-execution-review.v1",
  "approved": true,
  "design_sha256": "<exact design-frozen.json SHA256>",
  "implementation_sha256": {
    "BenchmarkSequence.h": "<SHA256>",
    "BenchmarkRenderer.cpp": "<SHA256>",
    "ContractTests.cpp": "<SHA256>",
    "run.py": "<SHA256>"
  },
  "prechecks": {
    "path": "<absolute passing pure prechecks.json>",
    "bytes": 0,
    "sha256": "<exact SHA256>"
  }
}
```

After root approval, use a fresh descendant of the ignored experiment directory:

```sh
python3 Tools/prototypes/command-recording-benchmark-20261019/run.py \
  --output build/command-recording-benchmark-20261019/run-01 \
  --review /absolute/path/to/root-execution-review.json
```

The runner verifies all frozen inputs and validates every source JSON/text event, raw factory payload, program count and source-channel identity before constructing a renderer. Both MIDI channels remain in provenance and enter source0; channel1 is never CV. One key-service runs after each complete equal-frame source group. A due240-frame vibrato tick runs first; that5ms grid is an inherited modeling assumption, not recovered firmware time.

## Storage and retained evidence

The complete own experiment subtree has a 200 MiB cap. Before each cell the runner reserves scratch + 16 MiB and requires64MiB free headroom. C++ caps command words, line lengths and logs before writes; Python caps/checks JSON bytes before exclusive writes. The conservative fixed-artifact bound is168,358,388 bytes before prior artifacts, which also count against the cap. No historical/user files are cleaned up.

Only one new full Float32 scratch WAV exists at a time. All102 scores, support hashes/scalars, event/command ledgers and a checkpoint must succeed before that own scratch is removed. Failures preserve scratch and stop. Full WAV hashes remain, but full ephemeral PCM cannot receive an independent post-discard recalculation claim.

Exact focused PCM is retained only for unchanged/ascending_track, both paths, supports 65/93/97/99/199/200: twelve short files. They preserve scoring samples without file-level trims. Separate key metadata reports pair-RMS listening gains and common safety factors; no listening verdict is selected. Independent raw metric recalculation is limited to these retained files. No original recording, factory payload bank or expanded full fixture is redistributed here.

## Completed frozen run

The single root-authorized run completed all sixteen cells and 1,632 score objects with exit 0. It is frozen under `build/command-recording-benchmark-20261019/run-01`; do not rerun it. Independent review recalculated exactly the twelve retained focus scores with zero numeric difference and made no full discarded-PCM claim.

`export_listening.py` is a separate, one-time constant-gain copy of those twelve focus files. `listening-design-frozen.json` binds original result/key/source hashes and the exact pre-existing gain × common safety formula before any copy. It does not process the synth, fit gains or call the scorer. Outputs under `listening-01` are level matched; the raw scoring files and result remain unchanged.
