# Original Mode00 allocation research candidate

This is an **unadopted research candidate**, separate from the shipping b15 engine. It implements the recovered [normal-voice allocation commands](../../../Docs/research/opu-allocation-command-path-2026-10-19.md) while preserving the existing synthesis, envelope and output hypotheses. The [separately frozen recording comparison](../../../Docs/research/hardware-allocation-2026-10-19.md) fails its promotion gates; software-command agreement is not hardware-audio agreement.

`candidate.patch` changes eight files against commit `1e7978225ff43b9e423d0fcc0acf8ad79f1ebd34`. A temporary checkout applies the patch, reproduces every target hash in `manifest.json` and passes the exported 25-group allocation test. The first export omitted Git new-file metadata and failed before compilation; that packaging failure is retained locally. The corrected export does not change source contents. No executable original firmware or recording is included.

## Behavior and limits

`Controls.allocationModel` defaults to Legacy `0`; Original `1` selects Mode00's coalescing, retained same-note cache and unsigned event ranks. Duplicate held inputs are complete no-ops. Natural envelope retirement does not erase logical key ownership or the cached slot. Silent TL99/TL127/AR0 inputs still allocate command state. Model changes wait for held inputs, voices and steal fades to clear; reset and all-sound-off clear that state explicitly.

MIDI owner 0 and CV owner 1 remain independent plugin inputs sharing the voice pool. The [original MIDI-channel witness](../../../Docs/research/opu-mode00-midi-ownership-2026-10-19.md) concerns enabled MIDI channels within one original receive domain; it does not merge plugin MIDI and CV. First-N reduced polyphony, unsupported-source rejection in Original, panic behavior, future-only patch snapshots and the existing 48-tick fade are disclosed host adaptations. Mode99, rhythm and the original program loader are outside this candidate. Chip key-service cadence, phase reset and physical retrigger envelopes remain unidentified.

The initial full wrapper was 496 bytes over the existing 192 KiB budget. A separately frozen storage-only amendment reduces the synthesis history from 256 to 128 doubles. The existing 64-tap reader needs at most the latest 64 ticks after fill. Full 64-bit input counters and the original memory ceiling are preserved. The current wrapper shape is 196,080 bytes, leaving 528 bytes; adding a native persisted selector still needs a fresh complete wrapper-size check.

## Reproduce the exported component

Run from a clone named `virtual-instrument-press78`:

```sh
git worktree add --detach ../press78-allocation-test 1e7978225ff43b9e423d0fcc0acf8ad79f1ebd34
cd ../press78-allocation-test
git apply ../virtual-instrument-press78/Tools/prototypes/original-allocation-20261019/candidate.patch
mkdir -p build/allocation
c++ -std=c++17 -O2 -I Source/DSP Tests/test_allocation.cpp Source/DSP/Press78Engine.cpp -o build/allocation/test
build/allocation/test
```

The patch deliberately leaves the project's existing CMake targets unchanged; the command above executes the added allocation test. The retained isolated suite separately passes all five previous C++ targets on the baseline and all six targets including Allocation on the candidate, in Release and ASan/UBSan. Its 25 new groups reproduce 251 original Mode00 fixture events with 1,506 grouped field comparisons. A separate 11-group implementation review passes both build modes.

Legacy default and explicit-zero renders equal the untouched baseline over 330 cases and 9,392,040 bytes per stream. A separate 108-case rate/clock/wrap probe compares another 4,808,592 bytes exactly. Event/render allocation checks and noise-inert checks pass. Four initial builds failed before CTest because the isolated tree omitted three unchanged reference-test headers; their failed receipts remain separate from the corrected dependency-bound runs. These are component results, not fresh Rack/SDK target builds, Reason playback, CPU measurements or persistence evidence.

The [validation summary](validation.json) binds the tested sources and retained local receipts. The fixed recording experiment keeps historical MIDI-owner mapping, independently compiled merged-MIDI Legacy, and Original allocation as three separate lanes. Its inferred one-frame note overlaps must not be confused with measured MIDI arrival order. Short Sine99 comparisons also regress in maps without duplicate onsets, so that ambiguity cannot uniquely explain the failure. All scores and twenty four-part auditions are retained. No production adoption follows from this experiment.
