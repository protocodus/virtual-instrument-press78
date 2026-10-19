# Physical Total Level and Melody Volume mapping — 19 October 2026

Original PSS-780 and PSS-680 firmware execution confirms that the front-panel **Total Level display increases while raw carrier attenuation decreases**. Display 90–99 corresponds exactly to raw TL 9–0. Yamaha's actual warning says **over 90**, so its literal 91–99 range corresponds to raw TL 8–0. Melody Volume 9 selects a carrier attenuation addend of zero. These findings resolve the control interpretation in the [signal-path audit](lofi-signal-path-audit-20261019.md); they do not identify a digital or analog clipping stage.

The [Yamaha owner's manual](https://usa.yamaha.com/files/download/other_assets/1/317511/PSS780E.PDF), printed page 29, identifies parameter 8 as the carrier's output level and warns that some voices distort above the stated display value, especially with Melody Volume 9. The locally retained page was visually checked. No voltage, transfer curve, number of clipping bits or universal distortion threshold follows from that warning.

## Original control behavior

The shared bank-2 display routine `$6DE8` reads the working carrier TL byte, masks its high bit, and displays `max(99 − rawTL, 0)`. Parameter 8 reaches carrier editor `$709C` through dispatcher `$72F9`. The physical Total Level key edge selects parameter 8; the original Value buttons then execute the following behavior:

| Action | Raw carrier TL result |
|---|---|
| Value + | Zero stays zero; otherwise `min(rawTL − 1, 98)` |
| Value − | Increment if the result is below 99; otherwise use 127 |
| Both Value buttons | Restore the selected factory carrier TL |

Normal stepping therefore uses raw values **0–98 and 127**. Display zero uses raw 127; the transition from display 0 to 1 jumps from raw 127 to 98, and the reverse transition jumps back. Injected raw values 99–126 also display zero, but are not reached by ordinary button stepping. Both operators' level fields remain distinct: this parameter changes only the carrier TL byte, leaving the other 31 working-voice bytes unchanged. Sine Wave 99 loads carrier TL 13 and displays **8.86**; resetting after an edit restores that value.

The Melody Volume state is RAM `$3F7C`. With function selector `$2587=12`, the original physical Value handlers increment/decrement the displayed index within **1–9**; pressing both restores **8**. The bank-2 `$4008` lookup supplies these carrier addends:

| Display |1|2|3|4|5|6|7|8|9|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Carrier addend |32|28|24|20|16|12|8|4|0|

Index zero also contains 32, but it is outside the normal panel range tested here. Original Volume updates pass the selected addend to the carrier level builder for all twelve eligible cached voice slots. At Volume 9, it receives zero. Subsequent key-level scaling, saturation and the separate Reverb command bit are described in the [level-command audit](opu-level-command-path-20261019.md). A base TL of 8 need not be the final hardware TL at every pitch.

## Verification and scope

The supplement passes **1,480 original-routine checks**: 256 display cases covering all 128 raw TL values in each ROM; 768 increment/decrement/reset cases; 400 complete-range button-traversal cases; two Sine99 witnesses; and 54 Melody Volume button cases. Display assertions inspect arguments reaching the original digit writer, and editing assertions retain the actual hardware-port writes and level-builder inputs. Both ROMs use an identical bank 2; their fixed-address callers differ. The [machine-readable ledger](front-panel-level-map-20261019.json) records the source identities, routine addresses, artifact hashes and counts.

This is constructed-state 65C02 execution with banked read-only ROM, mirrored stack/RAM and an always-ready peripheral. The Melody Volume function selection is supplied explicitly before exercising its physical Value-button handler; this supplement does not claim a complete boot or front-panel scan-loop emulation. It does not measure audio or fit any DSP parameter. The source identity and ordinary-public acquisition provenance remain in the immutable [pitch-command ledger](opu-pitch-command-path-20261019.md), tied to the [primary MAME driver](https://github.com/mamedev/mame/blob/983e76f8cd84f8da8d14241c9f07a5ee138cc3eb/src/mame/yamaha/ympsr16.cpp).

Local scripts and complete traces are retained only in ignored `build/front-panel-level-map-20261019`. The original firmware bytes are not redistributed. A first script attempt stopped at a Python whitespace syntax error before execution; its diagnostic is retained, and the corrected complete run passes. Production sources, prior frozen research ledgers, presets and audio are unchanged. This evidence grounds a future controlled overload experiment; it does not authorize a new nonlinear default.
