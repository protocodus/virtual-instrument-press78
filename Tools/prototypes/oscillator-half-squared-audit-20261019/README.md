# HALF²: native identities and common-response constraints

This bounded research-only probe follows [design-frozen.json](design-frozen.json).
It does not change the engine, open recordings, render audio or fit a filter.
The actual shipping `wave()` helper is inspected by including its unchanged
implementation in the native probe. This adds no production hooks.

From the repository root:

```sh
mkdir -p build/oscillator-half-squared-audit-20261019
clang++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Werror \
  Tools/prototypes/oscillator-half-squared-audit-20261019/HalfSquaredProbe.cpp \
  -o build/oscillator-half-squared-audit-20261019/probe
build/oscillator-half-squared-audit-20261019/probe \
  > build/oscillator-half-squared-audit-20261019/native-validation.json
python3 Tools/prototypes/oscillator-half-squared-audit-20261019/analyze.py \
  build/oscillator-half-squared-audit-20261019/native-validation.json \
  build/oscillator-half-squared-audit-20261019/result.json
```

The derived analysis requires the exact retained JSON from the separate
signed-square audit at the absolute path bound in the design. That audit's
local PCM remains outside the repository; this analysis does not read it.
The [public result](../../../Docs/research/oscillator-half-squared-audit-2026-10-19.json)
copies all sixteen mid-channel coefficient rows required for independent
arithmetic review. It also embeds the original native receipt, whose exact
bytes are retained in [native-validation.json](native-validation.json).

The initial pre-execution design is retained as
[design-before-null-scope.json](design-before-null-scope.json). Before any
compilation or execution, the final design clarified that a normalized phase
is undefined at known analytic coefficient nulls in synthetic sine and sine³
fixtures. Coefficient identity checks still include those bins. This was a
domain clarification, not an observation-driven window or acceptance change.
[implementation-bound.json](implementation-bound.json) fixes all executed
source bytes before compilation. The first and only execution passed 262,169
native and 42 synthetic assertions, and retained 80 odd-partial, 16 H2 and
16 null-vector diagnostics.

The derivative requirement is conditional on the previously estimated
frequencies being exact and a common stationary LTI chain. No response
smoothness bound is imposed. No observation is promoted to a physical OPU
constant or a production setting. See the
[audit](../../../Docs/research/oscillator-half-squared-audit-2026-10-19.md)
for the algebra, primary sources, all limits and next discriminating evidence.
