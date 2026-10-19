# OPU sibling oscillator and output circuit evidence, 19 October 2026

The useful new constraint is a **documented oscillator-component difference**, not a recovered internal clock divider. The PSS-480 foldout specifies a 5.5 MHz quartz crystal connected to the YM3420BF. The exact PSS-780 parts page instead lists a 5.5 MHz ceramic resonator. The PSS-780 overall foldout and a readable PSR-16/36 circuit were not recovered in this bounded public-source pass.

No DSP, preset, package, host or noise behavior was changed. The user's requirement excludes artificial noise.

## Visually verified manufacturer drawings

The original PSS-480 foldout is the [scanner's attachment](https://forum.mamedev.org/download/file.php?id=323), posted by jbevren on [1 November 2024](https://forum.mamedev.org/viewtopic.php?start=10&t=1017#p2862). It is drawing **KEC-11861**, board **M(VF344300), XE42020, FCC F mark**. Its component list identifies IC1 as **YM3420BF (XF032A00), OPU**. Full-image and lossless crop hashes are preserved in the accompanying JSON; the actual drawing, not OCR or the forum description, was inspected.

| Drawing location | Direct observation | Limit |
| --- | --- | --- |
| Component list, CR1 | Under “Quartz Crystal Unit”: **5.5M AD6496CA (VE760300)** | Specifies this PSS-480 board, not every OPU instrument |
| IC1 oscillator pins | CR1 spans **XI pin 93 / XO pin 94**; each node has **22 pF to ground** | No CPU, FM, envelope, LFO or DAC divider is identified |
| IC1 straps | **CT1 pin 56** and **CT2 pin 92** connect to ground | Pin names and logic levels do not decode their internal function |
| IC1 output | **TB pin 42** feeds **47 kΩ**, then IC13 pin 5; pins 6/7 form a follower | An external analog output connection, not the internal converter transfer law |
| IC13 filter | First follower output → **2.2 kΩ** → node with **0.01 µF** to ground → second follower | Confirms the previously modeled sibling low-pass path |
| Other OPU outputs | **CHA / CHB / CHC / CHD / FB** terminate as unconnected stubs on this drawing | Does not establish that these outputs are interchangeable with TB |
| Analog supply | AVDD pin 41 fed from +5A through **47 Ω**, with **470 µF / 6.3 V** to AGND pin 43 | Supply filtering does not specify converter resolution or distortion |

The exact [PSS-780 service supplement, electrical parts p12](https://www.manualslib.com/manual/4045165/Yamaha-Portasound-Pss-780.html?page=12#manual), was inspected from its retained original raster. It lists **YM3420BF / XF032A00** and **YM3420C / XF193A00** as OPU alternatives. Its main-board section calls **VH766700, 5.5MHz** a **Ceramic Resonator**. The part number is **VH766700**, correcting an earlier working-note transcription of “VI766700.” A separate 768 kHz ceramic-resonator row must not be confused with this part.

The PSS-780 parts page alone does **not** show which pins its 5.5 MHz component connects to, its load network, its manufacturer's tolerance, or a measured oscillation frequency. Therefore the defensible comparison is “PSS-480 documented quartz hookup versus PSS-780 listed ceramic component”; copying the complete PSS-480 oscillator circuit into the PSS-780 model would exceed the evidence.

## What the board difference constrains

Equal nominal 5.5 MHz labels are insufficient evidence of equal oscillator construction, tolerance, temperature behavior, aging or short-term stability. This prevents treating a sibling crystal specification as a measurement of the target instrument. It does **not** supply numerical drift, phase noise, jitter, or a reason to introduce random pitch modulation. Those quantities remain unmeasured.

The oscillator connection also does not resolve the CPU-clock disagreement in the [earlier interface audit](opu-digital-primary-leads-2026-10-19.md). The forum's software-delay annotation implies 2.5 MHz if taken literally; MAME's skeleton uses an expressly guessed 5.5 MHz / 4. Neither is a measured OPU synthesis timebase. Grounded CT1/CT2 cannot select between them without an authoritative mode definition or a clock trace.

The externally buffered TB node is consistent with an integrated analog output. Its external resistor, capacitor and supply connections do not identify the number of converters, channel multiplex schedule, bit depth, companding, arithmetic precision, or digital silence threshold. Those require different evidence. This pass supplies no justified new DAC artifact.

## PSR-16 / PSR-36 and exact-model search outcome

The first-hand investigator states that PSR-36 routes CHA/CHB to its stereo output whereas PSS-480 uses TB. At the same time, the post says the PSR-16/36 paper diagrams had not been scanned and stitched. No corresponding PSR schematic attachment was acquired. The stereo route therefore remains **a named investigator's report**, not a visually verified circuit in this ledger; it cannot establish stereo DAC encoding or the PSS-780 output route.

Searches covered the exact PSR-16, PSR-36, PSS-680 and PSS-780 model names, service/overall-circuit/schematic variants, DSR-500 as an additional lead, and major public manual indexes. Public results yielded paper-manual sales, owner manuals, the existing twelve-page PSS-780 supplement, or unrelated models. The [Transanalog catalogue](https://www.transanalog.com/manuals/Yamaha/) lists relevant service manuals but explicitly offers mailed copies rather than scans. No purchase, account, external contact or access-control workaround was attempted. A certificate failure from a PSR-36 sales index was left unresolved rather than bypassed.

The search ledger retains specific acquisition leads and exclusions. A PSS-560 drawing or a forum guess about another chip family was not substituted for a YM3420 circuit. This is a bounded failure to acquire a new drawing, not proof that none exists publicly.

The existing [output schematic audit](output-schematic-audit-2026-10-18.md) remains the boundary for the analog model: it is a PSS-480-derived circuit, with the exact PSS-780 AUX, chorus connections and oscillator network still unverified. The new evidence strengthens that boundary and adds the quartz-versus-ceramic distinction without inventing missing hardware behavior.

Ignored evidence is under `build/opu-sibling-clock-circuit-20261019/`. The JSON records original source paths, source URLs, image dimensions, crop coordinates, hashes, verified pin/value observations, and explicit unknowns.
