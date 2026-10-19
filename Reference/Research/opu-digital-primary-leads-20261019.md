# OPU digital interface: new primary leads - 19 October 2026

A firsthand PSS-480 disassembly report supplies a reproducible software fact: the posted routine polls bit 7 at address $0200, then writes through `$0200 + X`. Mapping that interface to the FM block remains the investigator's provisional interpretation. This is useful software-interface evidence, but it does not recover the YM3420's waveform arithmetic, frequency encoding, sample clock or envelope tables. No production code, factory data, artificial noise, package or host changes were made.

## Original source and visible facts

The source is jbevren's [27 October 2024 investigation post](https://forum.mamedev.org/viewtopic.php?start=10&t=1017#p2852), including the attached [write routine](https://forum.mamedev.org/download/file.php?id=322) and [initialization](https://forum.mamedev.org/download/file.php?id=321) screenshots. The investigator's hardware identification remains provisional. Both full images and lossless opcode crops are retained locally with hashes.

The visible routine contains six initial NOPs, reads status at$0200 with mask$80, waits while that bit is set, loads the byte from zero-page$04 and stores it at$0200+X; X comes from zero-page$03. The initialization loops over256 address/data pairs. Subsequent visible writes are register1=$00, register$17=$0B then$9F, and register$16=$2E. The third literal is visibly `A9 9F`; its neighboring analyst comment instead says8f.

No meaning is established for these register values. The [1 November 2024 update](https://forum.mamedev.org/viewtopic.php?start=10&t=1017#p2862) still describes SysEx-to-hardware translation as unresolved. Its missing table bytes cannot be reconstructed from the screenshot. Software's eight-bit address arithmetic also does not prove256 independently decoded hardware registers.

## Reproducible software-semantics check

The research verifier transcribes only the visible21-byte routine and executes it with py65's independent standard65C02 emulator. It supplies every address0..255, eight representative data values, zero through three initial busy reads, and four ready-state mask controls: **8,196 checks pass**. Each execution polls the designated status address, produces exactly one expected target write and returns correctly. No firmware blob, MIDI port, instrument or audio renderer is used.

A static detail matters for any future bus emulator: the BNE at$4300 branches from next-PC$4302 to$42FD, crossing a256-byte page. Under the conditional standard65C02 timings documented in [WDC's manufacturer table, p20](https://www.westerndesigncenter.com/documentation/w65c02s.pdf), each additional busy iteration costs8 cycles. With no interrupts, stalls or further waits, the observed routine takes37+8n cycles through RTS, or31+8n through its completed write. These are software predictions checked against the independent emulator, not measured Yamaha timings.

The forum's conversion of12 NOP cycles to4.8 microseconds implies a2.5MHz CPU if literal. The previously audited MAME skeleton uses an expressly guessed1.375MHz CPU. Neither value identifies the FM sample rate, EG tick or LFO divider, and the screenshot supplies no CPU-clock trace to settle the discrepancy. The generic CPU timing reference does not establish that every OPU timing detail matches a discrete W65C02S.

## Separating consequence and remaining source gap

The evidence identifies a software polling pattern at the provisionally identified interface. A low-level emulator of that software would need to reproduce its reads and writes. It does not justify importing an OPL register layout, assuming control writes become audible immediately, or adding a fixed audible parameter latency. Chip acceptance, internal scheduling and analog arrival are separate events. A future controlled bus/audio capture can measure their relation; a guessed CPU frequency cannot replace it.

The public-code search returned48 matches, including26 paths named `ympsr16.cpp`. Those paths were triaged rather than treated as26 independent implementations. The additional original chip-comparison table inspected, [nanase/opxdata](https://github.com/nanase/opxdata/blob/4d689797febff1c921907b4567002d4dffc2e6f9/comparison.html), leaves OPU's numerical fields unknown. The source search recovered no identifiable OPU patent linkage or usable note-frequency, DT1, RKS, phase-reset or arithmetic-width specification. This is a bounded result, not a claim that no such evidence exists.

The [machine-readable ledger](opu-digital-primary-leads-20261019.json) records source author/date, exact image URLs and hashes, the opcode transcription, branch calculation, emulator version/file hashes, all validation summaries, search scope and explicit unknowns. Original sources, crops, the isolated research environment and the verifier remain ignored under `build/opu-digital-primary-leads-20261019`. Run its `verify_write_routine.py` with that directory's `venv/bin/python` to repeat the software check. No source firmware or source image is included in the product.
