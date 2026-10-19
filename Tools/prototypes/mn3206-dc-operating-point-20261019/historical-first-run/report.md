# MN3206 settled-DC operating-point model, 2026-10-19

This adds a **nonlinear, voltage-explicit DC component to the research circuit
model**. It interpolates Panasonic's measured typical DC output versus DC input
curve, including its lower and upper plateaus. It does not process audio or
change the instrument's sound. No generic saturation curve or THD polynomial
was substituted for that source.

The primary source is the previously acquired Panasonic
[MN3206 datasheet, printed page 77](https://github.com/fmillion/yamaha-pss270/blob/8943bf963f196f20b4e2fc714f15400db578891b/datasheets/MN3206.pdf),
upper-left `VO–VI` graph. Its retained page raster is
`v4-MN3206-curves-p77.png`, SHA-256
`34916e399deedf1f7247c5c1e481197854786d1604bb6e292a26b66d1c1dd90f`.
It had already been inspected qualitatively; this is a new digitization and
component implementation, not a newly acquired source or hardware holdout.
The manufacturer scan and inspection overlays remain in ignored local storage.

## Explicit ports and conditions

The [component](../../Tools/prototypes/mn3206-dc-operating-point-20261019/mn3206_dc.py)
requires an input voltage and **all** the graph conditions on every query:
VDD **5 V**, VGG **14/15 VDD**, CP **10 kHz**, temperature **25 °C**, and VSS
**0 V**, in `settled_dc_only` mode. All voltages are relative to VSS. The output
is the graph's VO; the source does not establish a specific target jack, output
load or tied-pin interpretation. Other supplies, clock rates, temperatures,
modes, missing ports and nonfinite inputs are rejected.

The lookup is piecewise linear through **18 retained raw pixel coordinates**.
That interpolation is an explicit reading approximation. The nominal digitized
input span is 0 to 1146/269 V, about 4.2602 V. Requiring support for every declared
coordinate-reading scenario narrows the query range to **24/269 through
1122/269 V**, about **0.0892–4.1710 V**. Values outside it are rejected rather
than extrapolated. These are this model's evidence limits, not the chip's
absolute input ratings.

| Explicit DC input | Nominal graph output | Declared graph-scenario range |
| --- | ---: | ---: |
| 0.50 V | 1.99 V | 1.92–2.05 V |
| 2.00 V | 2.75 V | 2.61–2.89 V |
| 2.50 V | 3.14 V | 3.00–3.27 V |
| 3.00 V | 3.51 V | 3.38–3.65 V |
| 4.15 V | 4.22 V | 4.15–4.28 V |

The last column spans **64 declared coordinate-reading corner scenarios**:
each axis endpoint moves by ±1 source pixel, with ±3-pixel horizontal and
vertical trace readings. It is not a confidence interval, device tolerance,
or bound over every possible continuous trace. Small nominal plateau variations
from manual pixel readings remain visible in the data; they are not claimed
electrical ripple or physical nonmonotonicity.

## Preserved support failures and checks

The initial protocol froze 19 abscissae before numerical ordinate extraction.
The final rounded column, x=373, lay beyond the visible curve, so its ordinate
remains **null** in the preserved failed-support extraction. An unexecuted
proposal to use x=371 was rejected after independent review because vertical
grid ink could confound that endpoint. The final v3 design uses only the
original 18 supported points through x=362; every retained ordinate is
unchanged. It was frozen after those readings and before model construction
and execution. No curve continuation, knee fit or criterion relaxation rescued
the unsupported endpoint.

The first execution passes **6,976 assertions** using `python3 -S`, without site
packages. These cover primary-source and pre-execution source bindings, all
16 knots inside common support, 101 interpolation queries, 6,464 independently
expressed coordinate-corner checks, query-order independence, numeric boundary
handling, explicit conditions and rejected extrapolation. Exact rational
coordinate arithmetic separates graph limits from binary floating-point
rounding. The [receipt](mn3206-dc-operating-point-2026-10-19.json) retains the
first-run source/result hashes, examples, both earlier designs and their support
outcomes. An independent reviewer checked the final design and pixel support
before model execution.

From the repository root:

```sh
python3 -S Tools/prototypes/mn3206-dc-operating-point-20261019/check.py \
  build/mn3206-dc-operating-point-review/validation.json
```

Results refuse overwrite; the retained acquisition store is required to repeat
the primary-source hash checks. The lookup itself uses only the small tracked
digitization and design, with Python's standard library.

## What this makes possible

The component can now answer a prescribed **settled DC operating-point** query
and expose the source's limited input/output headroom at its specified test
conditions. It does not supply settling dynamics, signal-dependent audio
distortion or a transistor model. In particular, the same page's AC gain/THD
plots use different conditions and do not justify applying this DC curve to
every audio sample. Target BBD bias, signal volts, surrounding connections,
power sensitivity and output route remain unresolved in the
[target-board trace](target-am-net-trace-2026-10-19.md).

No production DSP, host, presets, defaults, version, Drive or noise behavior
changed. No random excitation, new recording or third-party media download was
introduced.
