# MN3206 DC operating point

Research-only lookup of the Panasonic MN3206 printed-p77 **DC** transfer graph.
See [the report](../../../Docs/research/mn3206-dc-operating-point-2026-10-19.md).
There is no audio, clock-stepping or Drive processor.

```python
from mn3206_dc import MN3206DC

point = MN3206DC().operating_point(
    2.5, mode='settled_dc_only',
    vdd_v=5.0, vgg_v=14 / 15 * 5,
    cp_hz=10000.0, temperature_c=25.0, vss_v=0.0,
)
```

All voltage ports are relative to VSS. The output is the graph's VO, not a
recovered target pin/load or AUX transfer. No operating condition has an
implicit default. Unsupported corners and inputs beyond the common graph
support are errors. The returned graph-scenario limits describe 64 declared
coordinate-reading corner cases; they are not statistical intervals or part
tolerances, nor a bound on every possible curve between measured points.

For VGG, exactly `Fraction(14, 3)` and its single nearest binary64 alias are
accepted. This representation alias adds no physical tolerance: adjacent
floats and nearby rationals are rejected without coercing them to float.

`design-frozen.json` and `extraction-failed-support-v1.json` preserve the original
19-column design and the unsupported final column. `design-frozen-v2.json` is an
unexecuted endpoint proposal rejected because of possible grid ink. Final
`design-frozen-v3.json` uses the original 18 supported points, with no changed
ordinate; `digitized-pixels.json` retains their raw source coordinates.
`implementation-bound.json` was written before the original model execution.
That source passed 6,976 checks but rejected exact rational VGG 14/3 V. Root
review found this port-contract defect. `historical-first-run/` preserves the
complete original source/checker/binding, successful receipt, publication and
root reproduction. The separately frozen
`port-semantics-correction-frozen.json` and `implementation-bound-v2.json` bind
the corrected exact-rational/binary64-alias contract before its execution.
The graph coordinates, support and all numerical examples are unchanged.

The model uses only Python's standard library and the tracked small JSONs.
Validation additionally verifies existing primary files in the retained local
acquisition store; those manufacturer scans are not redistributed here.

From the repository root, with a new result path:

```sh
python3 -S Tools/prototypes/mn3206-dc-operating-point-20261019/check.py \
  build/mn3206-dc-operating-point-review/validation.json
```

The checker refuses to replace a result. The corrected first run passed 7,002
assertions, including the focused representation tests, a separate voltage-space
interpolation oracle and all 6,464 independently expressed coordinate corners.
None of these software
checks validates an instantaneous audio transfer, physical PSS-780 operating
point or full BBD circuit.
