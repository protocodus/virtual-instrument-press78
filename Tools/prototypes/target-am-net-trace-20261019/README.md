# Target AM-board trace check

Research-only geometric and source-binding checker for the existing PSS-780
AM-board photo pair. It does not recover or simulate an electrical netlist.
See [the report](../../../Docs/research/target-am-net-trace-2026-10-19.md).

`input.json` binds the already acquired local images, Panasonic pinout scans and
three unchanged prior ledgers. The photographs and manufacturer material are
not bundled. The absolute acquisition paths are intentional provenance paths;
reproduction requires that existing local store. Python, NumPy, OpenCV and
Pillow are used; no packages are installed by this checker.

From the repository root:

```sh
python3 Tools/prototypes/target-am-net-trace-20261019/check.py \
  --out build/target-am-net-trace-20261019
```

The script checks hashes and the prior unaccepted status, recomputes two
grouped-exclusion fits from the **previously inspected** coordinate hypotheses,
reports a manual-location sensitivity scenario, verifies two conditional
pinout/copper-edge consistencies, and regenerates ordinary crop enlargements.
The exclusions are not independent held-out landmarks, and the manual estimates
are not confidence intervals. Neither operation accepts a numbered target net.
No electrical constants, noise or production behavior are changed.
