# Verified OPU firmware pitch-command path — 19 October 2026

Original PSS-480, PSS-680 and PSS-780 program dumps contain the same fractional pitch table and the same converter that packs it into three hardware writes. This replaces an important part of the earlier pitch hypothesis with **direct software evidence**. It does not recover the chip's phase accumulator, native sample rate or block-shift arithmetic. Production b11 remains unchanged, using equal temperament with no additive noise; no preset, UI, native adapter or production DSP was modified.

The [machine-readable ledger](opu-pitch-command-path-20261019.json) separates recovered commands, constructed-state execution, functional reconstruction and remaining hardware assumptions. Firmware, full disassembly and source-derived artifacts stay in ignored `build/opu-pitch-command-path-20261019`; none is distributed with the product.

## Source identity and method

The three program files were obtained through ordinary public links on the [PSS-480](https://mdk.cab/game/pss480), [PSS-680](https://mdk.cab/game/pss680) and [PSS-780](https://mdk.cab/game/pss780) archive pages. Each file's size, CRC and SHA-1 match the identities in the [primary MAME driver at commit 983e76f8](https://github.com/mamedev/mame/blob/983e76f8cd84f8da8d14241c9f07a5ee138cc3eb/src/mame/yamaha/ympsr16.cpp). The mirror supplies bytes; MAME supplies independently published identities. Neither a mirror download nor a matching hash establishes a redistribution licence.

| Instrument | Program file | SHA-1 |
|---|---|---|
| PSS-480/580 | `xe418c0-077.ic4` | `c0015cbb34f50ac5687db9def679117e4b2bad32` |
| PSS-680 | `xe416d0-093.ic4` | `d578324cfae73cd5f6c628eb3044be07684bc5d0` |
| PSS-780 | `xg503b0-132.ic4` | `33cc3f4ab27cf6e5068627625f6ab236209ad776` |

Each program is 262,144 bytes. MAME remains a no-sound skeleton: its guessed CPU divider is not an FM timing measurement. The [original jbevren investigation](https://forum.mamedev.org/viewtopic.php?start=10&t=1017) provided the initial routine/banking leads, not a published pitch formula. Its public updates end with a separate drum-program investigation; the author's five public repositories contain no OPU implementation identified in this pass.

The research fixtures execute the original routines with the independent standard 65C02 implementation in py65. They model the banked ROM mapping, RAM and writes, with the busy flag always ready. They supply explicit neutral controller/allocation state. This is **not a booted machine or peripheral emulator**: interrupt timing, keyboard scanning cadence, hardware register meaning beyond the observed software packing and actual audio are not simulated.

## Recovered frequency commands

Bank 2 maps file offset`0x8000` to CPU`$4000`. A pointer at CPU`$607B` selects the 768-byte table at`$5D7B`, file offset`0x9D7B`. The table contains 12 pitch classes  × 32 fractional positions, each a little-endian16-bit stored value. The converter at`$4256–$435A` and the entire table are identical in all three verified programs.

The converter takes a whole note and a five-bit fraction. The preceding pitch-state routine constructs a signed coordinate in1/32-semitone units from the voice note and controller state before splitting these inputs. Whole-semitone values are:

| Class | C | C♯ | D | E♭ | E | F | F♯ | G | A♭ | A | B♭ | B |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Software FNUM |2394|2537|2688|2847|3017|3196|3386|3588|3801|4027|4266|4520|

“FNUM” here names a decoded software numeric field. **Its13-bit packing is not evidence of a 13-bit phase accumulator.** For voice`v`, the routine writes three ports, with pair`v>>1` and selector`(v&1)<<7`:

- `$0228+pair`: selector plus FNUM bits 6–10.
- `$0230+pair`: selector plus FNUM bits 0–5.
- `$0238+pair`: selector, FNUM bits 11–12 and a three-bit block field.

For example, C60 produces FNUM 2394/block 4; E♭39 produces 2847/block 2; E♭51 produces 2847/block 3; F77 produces 3196/block 5. High input blocks are adjusted or capped by software, and the lowest input octave is halved before packing. These boundary commands are retained in the local128-note results; they are not a claim that every MIDI mode admits every input note.

The earlier [twelve-seed hypothesis](opu-frequency-hypothesis-20261019.md) reproduces C/E♭/G/B♭ commands, but several other classes differ. F is 3196 rather than 3195 on the equivalent scale: a conditional +0.541773-cent difference under identical downstream scaling. This is a firmware observation, not a refit to the disputed F77 recording tail. D and A♭ remain unchanged relative to that earlier hypothesis.

## A reachable fractional-command irregularity

At table indices 256, 257, 258—A♭ plus 0, 1, 2 fractional steps—the stored words are **3801,3838,3815**. The six bytes at file`0x9F7B` are`D9 0E FE 0E E7 0E`; the sequence and full-table hash are identical across all three programs. The middle value makes the software command sequence nonmonotonic.

Executing the PSS-780 serial note parser for note 68 with fine-pitch RAM`$3F75` set to 0, 1, 2 reaches those precise indices and emits those words. This confirms address interpretation and reachability; it does not yet map a front-panel tuning display increment to that RAM unit or measure the resulting audio. No random noise, bit faults or aging model is implicated.

A compact mathematical reconstruction is possible: for index`k=0..383`, every normal entry equals`floor(2394.41 × 2^(k/384) + 0.5)`, with the single explicit exception`k=257 →3838`. The common scale could be any value in approximately`[2394.40888684,2394.41432799)` and still reproduce all 383 normal integer outputs. Thus 2394.41 is a **nonunique reconstruction constant**, not a recovered Yamaha design formula, master-clock calibration or new audio fit. The functional verifier checks this construction against original table data and original converter execution.

## The MIDI mode distinction matters

PSS-780 software tests RAM`$3F80`: the zero branch behaves as Yamaha's Keyboard Assign mode, while the nonzero branch behaves as Sound Source mode. The panel transition that sets this flag was not executed; the names follow the corresponding behavior in the [exact owner manual](https://usa.yamaha.com/files/download/other_assets/1/317511/PSS780E.PDF), printed pp 31, 34, 45.

In the zero branch, the serial parser routes through`$B460`, rejects notes outside 36–96, and queues accepted notes as virtual keyboard bits. Executing the subsequent key scan reaches the pitch converter with the original note. Every one of 100 factory programs  × 128 MIDI notes passes this rule: 6,100 accepted note cases and 6,700 rejected cases. None enters the Sound Source input-transpose routine. Five nonzero velocities also give identical hardware writes for each of programs 65, 93, 97, 99 in this neutral fixture.

In the nonzero branch, the parser calls`$8F6A`. This reads a separate factory-program octave-offset table at bank3`$783D`, applies that offset, then folds ordinary shifted notes into 24–108. Extreme signed overflow cases clamp to 0 or 127; those cases are preserved in the executable model rather than silently simplified. All 100 × 128 cases and a further 105 × 128 direct mapper cases pass. User programs 100–104 have zero offset.

There are 28 factory programs with nonzero offsets. Bowed Bass 65 has −12; Human Voice1 93, Musical Saw 97 and Sine 99 have zero. **Do not apply the Bowed Bass offset to the published `c.00` video.** The verified zero-mode path does not call this translation. The inverse-looking routine`$8FB7` is called by MIDI-output helpers, not by the audible pitch converter. This supports the existing [Mode00 input fixture](mode00-benchmark-20261019.md); it does not justify an additional transpose correction to that recording.

## Pitch bend is a separate firmware path

Both tested MIDI paths use the pitch-bend message's high seven bits for pitch. All 128 low-byte values produce identical commands at each of four tested high bytes. Normal keyboard mode queues the update before its pending-bend service; Sound Source mode updates matching voices directly.

The bend tables contain signed 1/32-semitone offsets. All 12 ranges  × 128 entries match this functional rule:

1. Start with high byte`h`; replace 62 with 61 and 127 with 128.
2. Compute`truncate_toward_zero(range × (h−64) / 2)`.

The repeated61/62 step and endpoint are present in every verified program. For a negative configured range, a preliminary reversal maps 0→127,127→0 and other values to`128−h`, then applies the positive-range rule. The Sound Source branch chooses range 12; the zero-mode branch reads the configured range. The exact pending-update cadence is not established by these stateless calls.

These findings concern external firmware pitch commands. They **do not establish that the chip's internal vibrato, detune or operator multiplication use this table**, and provide no basis for quantizing an internal LFO to these MIDI steps.

## Validation and integration boundary

The initial converter/neutral-state suite passes 24,878 checks. The serial parser, complete two-mode note matrix, direct program mapper, bend-LSB invariance and selected velocity/fine-offset fixtures pass 40,087 more. The separate functional reconstruction suite covers all 384 words, 1,536 bend values, 128 reversed-controller values, every 128-note  × 32-fraction  × 12-voice converter combination per program ROM, and every positive/negative bend range in the PSS-780 pitch-state caller. That suite passes 156,672 checks, bringing the combined total to 221,637. Its separate result and source hashes are recorded in the ledger; this is numerical software verification, not hardware fidelity certification.

To repeat locally, use the retained py65 environment with `verify_pitch_path.py`, `verify_midi_path.py` and `verify_functional_pitch.py` in the ignored research directory. Inputs must match the stated ROM hashes. No firmware bytes or full disassembly are emitted by the reports.

A proposed engine improvement can independently implement these **functional command outputs**, preserving the existing equal-temperament behavior as an explicit compatibility choice. It must keep downstream hardware assumptions visible. In particular, the firmware emits the same FNUM 2847 with two different blocks for E♭39/51; it does not perform the low-octave truncation invoked by the earlier recording hypothesis. The proposed `floor(FNUM × 2^(block−3))` internal grid and its frequency scale remain behavioral hypotheses. This pass neither adopts them nor rescores recordings.

The next useful checks are an independent review of the address mapping/packing and a controlled bus-plus-audio observation of the fractional anomaly and low E♭ octave pair. Native FM cadence, phase precision, block arithmetic, internal modulation and the physical-panel Decay 22-to-envelope-command mapping remain unresolved here. Those gaps must not be filled with unrelated Yamaha-chip assumptions.
