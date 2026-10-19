# Target AM-board photo registration: geometric check, 2026-10-19

The two existing PSS-780 photographs support a better **coarse component-region alignment**, but this pass does **not** establish a validated whole-board homography or a numbered copper-pad map. No DSP, circuit constants, presets or production files changed. The earlier [source acquisition note](target-am-board-2026-10-19.md) remains unchanged; these are the same photographs, not a newly acquired schematic.

The original component photograph is by deepsonic, [Flickr 10090241086](https://www.flickr.com/photos/deepsonic/10090241086/), and the copper photograph is [Flickr 10090216715](https://www.flickr.com/photos/deepsonic/10090216715/). The accompanying [machine-readable record](target-am-registration-v2-2026-10-19.json) binds both original JPEG hashes, every retained trial and the numerical reproducer. Coordinates always refer to the original 2000-pixel-wide JPEGs, before viewer resizing or rotation.

## What improved

The initial fits confused elevated package/lead positions with board-plane contact positions. Several visible near-row lead ends were approximately 7–12 pixels below earlier estimates. Another proposed DIP rectangle was actually a longer row of passive-component pads. Correcting these observations produced a plausible mirrored alignment for five candidate chip regions. Two adjacent bare-wire links also give more distinctive local landmarks than guessed board corners. The two holes at the component-side front-right corner must not be treated as one feature or interchanged with the copper-side screw and adjacent circular feature.

A separate, rotation-only inspection resolves an orientation mistake. The dark marking at the left short end of both IC2/MN3206 and its neighboring package is a **centered end notch**, not the previously supposed far-corner pin-1 dot. With the package viewed from the component side, notch left, the visible near row is pins 1–4 and the far row is pins 8–5. This observation is independent of the homography. It corrects the earlier tentative orientation but does not, by itself, identify the corresponding copper footprint. The neighboring package's part marking is still less legible than MN3206.

## Why the transform is not accepted

Thirteen exploratory attempts are retained, including incorrect footprint hypotheses and projective fits that developed a pole through the board. None is accepted for pin or net assignment. The most coherent trial, attempt 13, fits 26 manually proposed correspondences: five four-pin near rows, two mounting-feature candidates and four bare-link ends. Its maximum training error is 6.35 pixels. That attractive training result is insufficient.

When each four-pin row is omitted from fitting, its maximum prediction error is:

| Proposed region | Maximum omitted-row error |
| --- | ---: |
| Left/front op-amp | 6.75 px |
| Left/back op-amp | 18.17 px |
| IC2/MN3206 | 4.43 px |
| Neighboring clock package | 7.74 px |
| Right op-amp | 28.62 px |

These are exploratory cross-checks, **not fresh held-out evidence**: the proposed identities had already been inspected during the earlier attempts. Two errors equal or exceed the approximately 19–20 pixel pad pitch. The actual board-plane entry point is partly hidden by some bent leads; manually locating a visible metal end does not eliminate that uncertainty. Fitting more points cannot make an uncertain correspondence true.

The 68P, 390K and 2.7K lead predictions remain near competing passive-pad columns. Reliable independent power-slider and connector through-hole correspondences were not recovered. Thus the requested combination of four or more secure landmarks **and independent distant validation has not been achieved**. Possible image distortion or nonplanarity was not calibrated and is not used to excuse the discrepancies.

## Consequence for electrical tracing

The corrected package orientation and coarse chip-region candidates can guide further inspection. They cannot yet certify component-valued nets, oscillator pin connections, a clock frequency, or physical BBD delay. In particular, no manufacturer example circuit is substituted for the photographed target wiring. Any independently visible copper connection can remain recorded anonymously or conditionally, without promoting this transform to evidence.

Reproduce the numerical checks locally with `python3 build/target-am-registration-v2-20261019/reproduce_registration.py`. It verifies the two source hashes, refits the frozen coordinates and regenerates the errors. Originals, enlarged inspection crops and failed overlays remain in ignored build storage. The next useful evidence is an independently identifiable distant board-plane landmark or a less oblique component view; no new production model is justified by this registration pass.
