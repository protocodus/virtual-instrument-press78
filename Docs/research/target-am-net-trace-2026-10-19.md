# Target AM-board net trace: bounded reassessment, 2026-10-19

**No numbered target net or component-value-to-pin association is accepted.**
This pass checked whether the existing component/copper photo pair could close
the geometric gap around MN3206 and the neighboring clock-package candidate.
The local pattern is consistent with that hypothesis, but independent pad-level
registration is still missing. No DAC, BBD, supply or Drive constant follows.

The [original acquisition](target-am-board-2026-10-19.md),
[thirteen rejected registration attempts](target-am-registration-v2-2026-10-19.md)
and [anonymous copper ledger](target-am-clock-trace-2026-10-19.md) were read before
this inspection and remain unchanged. The source images are deepsonic's
[component side](https://www.flickr.com/photos/deepsonic/10090241086/) and
[copper side](https://www.flickr.com/photos/deepsonic/10090216715/), acquired earlier
through Commons. No image, schematic or datasheet was newly downloaded. Ordinary
crops and enlargements stay in ignored build storage; none was generated or
painted to fill missing detail.

## What the images can constrain

The original, unmirrored component crop again shows the MN3206/IC2 marking and
the package-end notch. Some metal lead ends are visible, but the package,
neighboring parts and bent leads conceal several actual board-plane entries.
The two adjacent bare links are useful landmarks, but they were already used
in the earlier fit. No new, independently identifiable distant hole or pad
constellation was recovered. The two mounting features at the far-right corner
remain distinct and cannot be interchanged to make a fit look better.

Two grouped exclusions quantify the local sensitivity of **the old exploratory
correspondences**. A region is excluded from fitting before its coordinates are
predicted. All its identities had already been inspected in the older study:
these are geometric cross-checks, **not independent held-out validation**.

| Excluded from the old 26-point fit | Maximum training error | Maximum excluded error | Maximum manual sensitivity sum |
| --- | ---: | ---: | ---: |
| Both paired DIP near rows, eight points | 5.97 px | 7.12 px | 18.44 px |
| Both rows and the four adjacent bare-link ends | 6.27 px | 9.01 px | 20.28 px |

The minimum spacing among the proposed near-row copper pads is 18 px. The last
column adds each excluded error, the transform's local maximum displacement
from a 6 px component-contact location estimate, and a 3 px copper-pad estimate.
Those location estimates come from the prior manual ledger. **This is a
sensitivity scenario, not a measured confidence interval or an established
whole-board error bound.** It illustrates the missing pad-assignment margin;
it cannot establish correspondence truth. The earlier omitted right-op-amp-row
error of 28.62 px also remains unrepaired. No additional free fit was selected
from these checks.

## Manufacturer pinouts narrow a conditional hypothesis

The previously acquired, Panasonic-authored
[MN3206 sheet, printed page 76](https://github.com/fmillion/yamaha-pss270/blob/8943bf963f196f20b4e2fc714f15400db578891b/datasheets/MN3206.pdf)
and [MN3102 sheet, printed page 107](https://github.com/fmillion/yamaha-pss270/blob/8943bf963f196f20b4e2fc714f15400db578891b/datasheets/MN3102.pdf)
give explicit top-view terminal drawings. Their bound local page scans were
visually checked. They are primary manufacturer documents preserved by a
third-party mirror; they are not target-board schematics.

If the proposed MN3206 footprint has near row at copper `y=340`, far row at
`y=391`, and the same notch orientation as the unmirrored component photograph:

- The visible bridge from `(1625,391)` to `(1645,392)` would connect MN3206
  pin 8 OUT2 to pin 7 OUT1.
- If the neighboring footprint is MN3102 with near row at `y=428`, the existing
  diagonal from `(1665,391)` to `(1685,428)` would connect MN3206 pin 6 CP2 to
  MN3102 pin 4 CP2.

These are **two conditional consistency constraints, not accepted named nets**.
The copper edges were recorded before this pass; the manufacturer pin labels
do not independently validate which package occupies each footprint. A familiar
output bridge or like-named clock connection must not be used to choose the
correspondences and then presented as confirmation of those same choices.

The land at `(1665,483)` still has no visible outgoing copper in this photograph.
Even if it became candidate MN3102 pin 6 OX2, that observation alone would not
prove it electrically open or prove external excitation. The marked 68P, 390K
and 2.7K components remain unassigned to copper pad pairs. No named rail,
oscillator RC pairing, modulation law, gain, converter transfer or nonlinear
supply response has been recovered.

## Reproduction and consequence

The [result ledger](target-am-net-trace-2026-10-19.json) binds seven existing
inputs, source/photo hashes, the two exclusion transforms, all numerical errors,
conditional pin labels and inspection crops. The
[checker](../../Tools/prototypes/target-am-net-trace-20261019/check.py) verifies
the hashes, recomputes the geometry, verifies conditional copper-edge endpoints
against the unchanged old ledger, and regenerates ordinary inspection crops:

```sh
python3 Tools/prototypes/target-am-net-trace-20261019/check.py \
  --out build/target-am-net-trace-20261019
```

Its input paths refer to the existing local acquisition store; no photographs
or manufacturer scans are redistributed in the source tree. The initial
numeric result is also retained locally as `result-first-pass.json`; the final
checker additionally validates the conditional endpoints against the old
anonymous edge list, without changing coordinates or numerical outcomes.

The next useful evidence is a genuinely independent board-plane correspondence
or another primary view that exposes the obscured through-hole entries. Refit
iterations on these same uncertain identities cannot supply it. This bounded
failure leaves the accepted named-net count at zero and justifies **no
production DSP, noise, preset, version, DAC or Drive change**.
