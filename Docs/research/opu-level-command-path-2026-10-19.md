# Original OPU level and key-scaling commands

The PSS-780 and PSS-680 programs use the same signed lookup tables to turn operator key-level scaling into integer level commands. They group notes in pairs, clamp both ends of the table, and saturate the scaled TL before adding a separate carrier-only velocity or volume adjustment. This is a recoverable source of the instrument's level and timbre variation across the keyboard. It does not establish the YM3420's command-to-decibel transfer, and no production DSP, preset, UI or default changed in this pass. The existing Original pitch mode remains a frequency-only feature.

The [JSON ledger](opu-level-command-path-2026-10-19.json) binds the frozen design, routines, data identities, test results and ignored reproduction artifacts. Sources are the original PSS-780/PSS-680 program files already identified in the [pitch-command investigation](opu-pitch-command-path-2026-10-19.md), matching the [primary MAME ROM identities](https://github.com/mamedev/mame/blob/983e76f8cd84f8da8d14241c9f07a5ee138cc3eb/src/mame/yamaha/ympsr16.cpp). Field names and the documented TL range follow Yamaha's [PSS-780 owner manual](https://usa.yamaha.com/files/download/other_assets/1/317511/PSS780E.PDF), printed p.41. Original program images, unused ROM table padding, full disassembly and executable research probes remain ignored and are not redistributed. The subsequently published [research prototype](../../Tools/prototypes/key-level-20261019/README.md) separately reconstructs the 640 reachable numerical lookup outputs; it is not included in the product.

## Exact command calculation

For a mapped note `n` and one operator's LKS byte, the original software computes:

```text
p = max(n - 24, 0) // 2
if p < 18:
    offset = signed(lower[LKS & 15][p])
else:
    offset = signed(upper[LKS >> 4][min(p - 18, 21)])
base = clamp(raw_TL + offset, 0, 127)
modulator_command = base + 128 * reverb_enabled
carrier_command = min(127, base + carrier_addend) + 128 * reverb_enabled
```

The last two lines use each operator's own TL and LKS values. The carrier addend does not alter the modulator. Reverb's control bit is separate from the seven-bit level command, as established by the [release/effects investigation](opu-release-command-path-2026-10-19.md).

The lower table is 16 curves ×18 used columns, at bank2 CPU`$69B5`; the upper is 16 ×22 at`$6BB5`. Both use a 32-byte row stride. The same tables occur byte-for-byte in both program ROMs. The used-data SHA256 values are `29b809af9c589338adf828d352b01ffe365439139bf0b43c1236c6f3dfeffe8c` and `c72340fadb97ab1ede605e8d5a2a74b5c3c28e471b490d4fbb2b39ab76f7c8b6`; padding-region identities are recorded separately.

This produces concrete boundaries. Notes 0–25 use the first lower-table entry;24/25,26/27 and subsequent pairs share an index. Notes 60/61 use upper entry 0, which is zero for every curve. Notes 102–127 use the final upper entry 21. Curve 0 disables scaling on its respective side. Lower curves 1–7 provide negative command offsets and 8–15 positive offsets; upper curves 1–3 are negative and 4–15 positive. These are command signs, not independently measured loudness units.

Some rows have simple exact descriptions: lower curve 15 is `35 - 2*j`, and upper curve 8 is `j`. A complete original table-generation formula was not recovered. A bounded mathematical check found 20 of 32 rows cannot be represented by one nearest-integer straight line under the tested strict half-unit rounding margins. This does not exclude other generation or rounding rules. An approximate smooth curve would discard verified entries and pair quantization, so the exact lookup remains the defensible functional reconstruction.

## Carrier adjustment and real note paths

The original Mode00 serial path ignores note-on velocities 1–127. Its caller obtains the carrier addend from bank2 table`$4008`, indexed by RAM`$3F7C`. Explicit indices 0–9 produce 32, 32, 28, 24, 20, 16, 12, 8, 4, 0. The main fixture's zero-initialized index therefore contributes 32; that is an explicit test state, not evidence of the keyboard's boot volume. The supplementary volume sweep covers every index.

Mode99 instead uses a 128-entry velocity table at bank2`$7890`. Representative velocity→addend pairs are 1→31, 16→21, 32→15, 64→8, 96→3 and 120/127→0. Both ROMs have the same table. All 127 nonzero velocities were exercised for the four focus programs in both modes, with the modulator unaffected by this addend. The builder also passes exhaustive arithmetic checks for every carrier TL 0–127 and addend 0–127; those broader arithmetic inputs should not be confused with the smaller addend range observed in these callers.

The serial tests execute original factory translation and actual Mode99 program changes. They preserve the mapped note entering the builder, rather than assuming it always equals the incoming MIDI note. PSS-780 display numbers and internal program numbers differ, as documented in the earlier research. Replacing a cached Mode99 program first sends 127/127 temporary level commands, then the final calculated values. Both phases are retained and verified.

A further model difference appeared at the receive boundary: both instruments' Mode00 path accepts 36–96, but the PSS-680 Mode99 program rejects notes outside 24–108. Its original instructions explicitly compare those bounds. The PSS-780 Mode99 path instead wraps through its program/note mapper. This result does not relabel or change the existing PSS-780 Mode00 audio benchmark.

## Saturation, reserved inputs and the existing engine

The level saturation occurs **after** signed key scaling. Documented TL values 99 and 127 are therefore not unconditional early-mute flags in the firmware calculation. Actual serial Mode00 witnesses, using a constructed legal working patch with LKS`$11` and explicit volume index 9, produce:

| Stored TL | Note 36 command | Note 60 command | Note 84 command |
|---:|---:|---:|---:|
| 99 | 80 | 99 | 93 |
| 127 | 108 | 127 | 121 |

Both operators and both program ROMs agree. These witnesses establish command values, not their audible amplitude or a special silence threshold. They use legal working-patch fields in RAM followed by the original serial note path; the SysEx receiver itself was not executed in this fixture. No existing factory case in the examined 100-voice bank combined the current engine's early-mute condition with a recovered final command below 99, so this is also relevant to editing controls rather than evidence of that specific defect affecting every factory voice.

All 200 factory voice payloads (100 per ROM) have TL bit7 clear. Setting that undocumented raw input bit produces asymmetric arithmetic: for example, raw 128 becomes modulator 128 without Reverb and 0 with it, while the carrier becomes 127/255. These observations are retained outside the documented seven-bit input domain. They do not justify naming a new supported raw-TL flag or conflating it with the independently recovered Reverb bit.

The present engine uses continuous note distance and approximate curve shapes, continues its high-side curve above 102, allows some negative-scaling gains above unity, and returns silence before scaling when stored TL is at least 99. Those choices differ from the recovered command path. At note 74 with zero carrier addend, the carrier comparisons are:

| PSS-780 voice | Firmware command | Legacy curve expressed in its own equivalent TL units |
|---|---:|---:|
| 65 Bowed Bass | 20 | 21.183 |
| 93 Human Voice 1 | 22 | 23.729 |
| 97 Musical Saw | 17 | 18.183 |
| 99 Sine Wave | 14 | 15.183 |

The last column merely divides the current code's attenuation expression by its assumed 0.75 dB/TL. It is not a new measurement of the OPU. Across the 100-voice, 128-note descriptive code comparison, 25,472 finite legacy cases have a mean absolute difference of 1.273 equivalent command units; 128 cases invoke the legacy early mute. These numbers are not audio scores and do not predict an audible improvement on their own. A future exact command path can preserve its verified steps while still labelling the downstream 0.75 dB transfer and oscillator/envelope implementation as hypotheses.

## Verification and remaining scope

The frozen design precedes the formal sweeps and any future audio evaluation. There are 393,216 passing direct original-program checks: all 256 LKS bytes ×128 notes on both ROMs; every valid TL ×signed-byte saturation input; a matrix of complete operator writes with both Reverb states; and exhaustive carrier addends. Another 16,592 actual serial/caller cases and 72 legal-boundary witnesses pass, for 409,880 asserted checks. Sixteen out-of-domain raw-bit observations and the mathematical curve analysis are supplementary. No audio was fitted or rendered for this investigation.

The first serial pass's 7,137 assertion failures remain preserved. Of these, 6,237 arose because the expected trace omitted the real temporary mute prefix, and 900 because the acceptance assertion incorrectly reused the PSS-780's Mode99 behavior for the PSS-680. The corrected fixture verifies both phases and the model-specific bounds; it does not discard those cases. Constructed RAM, a read-only banked ROM, mirrored stack and always-ready peripheral remain fixture limitations. The exact OPU attenuation transfer, rate and pipeline timing, and original full-boot state are still unknown.

Reproduction uses the retained py65 environment and ignored `verify_level.py`, `verify_serial_level.py`, `verify_boundaries.py` and `compare_legacy.py` under `build/opu-level-command-path-20261019`. PSS-780 lookup/saturation/builder entries are`$CACC/$CB57/$CB7F`; PSS-680 entries are`$C9C7/$CA52/$CA7A`. The ledger binds all dependencies and source hashes. Any production mode or default decision requires separate review; none is implied by this report.
