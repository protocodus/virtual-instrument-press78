# Exact circuit source search — 19 October 2026

This bounded public-source search recovered a complete **PSS-560 service drawing**, but no complete PSS-680/780 circuit drawing or new YM3420BF internal-arithmetic document. The PSS-560 circuit is a useful comparison, **not an identified target-board substitute**. No DSP, defaults, noise, presets or product assets changed.

The [machine-readable receipt](exact-circuit-source-search-2026-10-19.json) records acquired files and limits. Downloaded documents and page renders remain in ignored research storage; they are not bundled with Press78 or asserted to have a redistribution licence.

## Newly readable circuit, with an explicit mismatch

The [Circuit Bending Wiki index](https://circuitbending.miraheze.org/wiki/List_of_Yamaha_Keyboards_and_Drum_Machines) links a [13-page Yamaha PSS-560 service scan](https://static.wikitide.net/circuitbendingwiki/4/41/Yamaha_PSS-560_Service_Manual.pdf). Its final PDF page contains the complete drawing; PDF page 9 has the electrical parts list. These pages were rendered and inspected, rather than relying on the index's chip descriptions.

The PSS-560 uses board **VB183800 (M)**, YM3812 with external YM3012 conversion, and **MN3209** with MN3102. Its chorus drawing shows a mono BBD path, bias and input filtering, joined BBD outputs, subsequent low-pass filtering and a FET gate. The stereo mix includes a wet-path inverter with equal 47 kΩ input/feedback resistors and a 220 pF parallel capacitor. This is concrete sibling evidence for filtered, polarity-opposed wet mixing; it does not establish the target's component values, delay range or clock modulation.

The exact PSS-780 parts sheet instead identifies **VF108000 (AM)**, MN3206/MN3102, NJM4558 variants and AN7148. Its digital section contains YM3420BF/C. Thus neither board identity, BBD type nor FM/DAC implementation matches this newly acquired PSS-560 drawing. The PSS-560's 3.579 MHz quartz oscillator also cannot resolve the target's 5.5 MHz ceramic-resonator circuit. No PSS-560 values were transplanted into the model.

## Exact-model acquisition results

The same public index links a [PSS-780 service PDF](https://static.wikitide.net/circuitbendingwiki/6/6b/Yamaha_PSS-780_Service_Manual.pdf). It is the 12-page supplement, ending at the electrical parts list. Its introduction refers to the PSS-680 base manual and mentions an overall circuit diagram; the acquired file does not contain that diagram. It confirms the previously inspected parts sheet, including **VH766700, 5.5 MHz ceramic resonator**; it does not close the foldout gap. The [earlier clock/circuit ledger](opu-sibling-clock-circuit-2026-10-19.md) remains the source for the readable PSS-480 OPU pin/clock/output drawing and its explicit target limitations.

A separate [PSS-780 listing](https://www.owner-manuals.com/PSS780-service-manual-YAMAHA.html) advertised 54 pages and 5.4 MB. Following its normal public download link returned **HTTP 404 and 329 bytes of HTML**, not a PDF. The listing's page-count claim is unverified and supplies no circuit evidence. The linked response is preserved locally; its query string is omitted from this shareable receipt.

Other bounded checks found only an operating-manual link in [TNT23's PSS-680 directory](https://www.sensi.org/~tnt23/pss680/), and three owner-manual items in an Internet Archive exact-model text search. A PSS-680 manual page at PDF-Manuals returned HTTP 403; no access workaround was attempted. Initial Python fetches failed because of this environment's certificate store; ordinary system curl with TLS verification then supplied the recorded HTTP outcomes. The search is not proof that no full schematic exists elsewhere.

## Consequence

There is now another readable Yamaha chorus comparator, and a precise reason not to treat it as the target analog board. The missing target foldout still prevents a component-accurate PSS-680/780 output/chorus reconstruction. This pass adds no measured DAC resolution, update clock, oscillator jitter, BBD distortion, aging behavior or artificial noise. Independent firmware pitch-command research is documented separately in the [pitch-command ledger](opu-pitch-command-path-2026-10-19.md); it supplies software commands, not the missing analog circuit.
