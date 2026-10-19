# Key-level command research candidate

This candidate is **not adopted or packaged**. Its recovered command path passes independent software checks, but Bowed Bass exceeds the predeclared recording-regression limit on all four timing maps. Production remains b12. See the [complete comparison](../../../Docs/research/hardware-key-level-b13-2026-10-19.md).

`candidate.patch` preserves the eight tested source/tool/test changes against commit `c8e9982d1619438d5713a6b373f4edb64c1e77e4`. A temporary repository applied the patch and reproduced every target hash in `manifest.json`. No original firmware executable, media or unused ROM padding is included. The independently authored lookup represents reachable numerical command behavior; its downstream decibel transfer remains a hypothesis.

The patch adds `Controls.keyLevelModel`: 0 preserves b12; 1 applies integer key-level lookup and saturation before the existing amplitude conversion. The mode waits for voices and steal tails to finish. It includes a generator, twelve new contract groups and renderer/probe options. It makes no Rack, preset, controller, Reverb, analog, DAC, supply or noise changes.

To inspect it in a separate checkout, run from a clone named `virtual-instrument-press78`:

```sh
git worktree add --detach ../press78-key-level-test c8e9982d1619438d5713a6b373f4edb64c1e77e4
cd ../press78-key-level-test
git apply ../virtual-instrument-press78/Tools/prototypes/key-level-20261019/candidate.patch
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release --parallel
ctest --test-dir build -C Release --output-on-failure
```

The retained macOS Release and ASan/UBSan runs each pass eight CTest targets. Independent checks compare all 640 table entries and 4,194,304 composed valid commands with original-program primitive results. Those are software checks, not measurements of hardware gain or envelopes. The fixed recording experiment keeps all 800 scores and twelve auditions, including the failed adoption gate; no timing or parameter was retuned afterward.
