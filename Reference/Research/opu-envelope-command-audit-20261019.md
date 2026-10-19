# Sine99 and Synth Bass 1 envelope commands — 19 October 2026

The PSS-680 and PSS-780 firmware send **modulator D2R 24, carrier D2R 22 and RKS 0 unchanged** when constructing the published Synth Bass 1 recipe from Sine99. That remains true across all 12 cached slots and notes 36–96. The CPU does not turn those values into pitch-dependent rate commands in the tested paths. The chip's internal envelope cadence, rate arithmetic and response to keycode remain unknown.

Selecting Sine99 also **preserves an already enabled Reverb state**. The author's recipe leaves effects to preference, so the absence of subsequent effect messages cannot establish an effects-off recording. This audit changes no DSP, preset, output noise or GUI and fits no audio parameters.

## Exact inherited fields

Both original firmware images produce the same Sine99 working payload. Identity and acquisition follow the [pitch-command ledger](opu-pitch-command-path-20261019.md) and primary [MAME source](https://github.com/mamedev/mame/blob/983e76f8cd84f8da8d14241c9f07a5ee138cc3eb/src/mame/yamaha/ympsr16.cpp); field names follow the [Yamaha voice format](https://usa.yamaha.com/files/download/other_assets/1/317511/PSS780E.PDF), printed p41.

| Field | Modulator | Carrier |
|---|---:|---:|
|AR / RKS|63 / 0|63 / 0|
|D1R / D1L|1 / 0|1 / 0|
|D2R|0|0|
|RR / SRR|8 / 5|8 / 5|
|Level, raw TL|127|13|
|Level-key-scale high / low|0 / 0|11 / 9 (`0xB9`)|
|Multiplier / detunes|1 / DT1=0, DT2=off|1 / DT1=0, DT2=off|
|Waveform / AM enable|sine / off|sine / off|

Shared fields are feedback 0, PMS 3, AMS 0 and Vibrato delay 11. The factory Vibrato and Sustain flags are both off; a nonzero sensitivity or delay does not mean that the performance effect is enabled. The upper nibble of each SRR-containing payload byte is 5 and remains unchanged; this audit assigns it no new meaning.

The [author's Synth Bass 1 recipe](https://www.pss680.com/patches.php) specifies panel controls 0–8 as `63,63,24,22,1,1,0,77,86`, starting from 99. Executing the original physical parameter-selection and Value-button handlers changes only three working-payload bytes: modulator TL127→22, modulator D2R0→24, and carrier D2R0→22. It takes 123 Value-up presses per model; the other six displayed settings already match the recipe. All inherited fields above remain unchanged. This extends the earlier [Decay macro audit](front-panel-envelope-map-20261019.md) to the complete recipe and its note-command path.

## What reaches the chip

For slot `v`, use displacement `floor(v/2)+16*(v mod2)`. The paired programmer writes these full bytes:

| Command group | Modulator base | Carrier base | Recipe bytes, mod/car | Packed interpretation |
|---|---|---|---|---|
|Attack|`$0280`|`$0288`|`$3F / $3F`|AR low6, RKS high2|
|First decay|`$02A0`|`$02A8`|`$01 / $01`|D1R low6, DT2 bit6, AM bit7|
|Second decay|`$02C0`|`$02C8`|`$18 / $16`|D2R low6, waveform high2|
|Level/release|`$02E0`|`$02E8`|`$08 / $08`|D1L high4, RR low4|

All 256 byte values are forwarded unchanged by each paired writer, on every slot, in both programs. This includes the upper RKS, waveform and enable bits. The programmer receives a cached patch and slot; it does not compute a note-dependent rate addition. Original Mode00 serial note-on/off paths agree: they do not rewrite AR, D1R or D2R for each note. Pitch and computed TL commands are separate.

There is a transient release command: note-on preparation writes carrier D1L/RR `$0F`, then the key-on service restores `$08` before key-on. This occurs across the tested notes and slots. It is not a conversion of carrier D2R22 into another decay rate. With factory Sustain off, note-off writes RR8 for both operators. The separate [release-command audit](opu-release-command-path-20261019.md) and [adopted Sustain policy](sustain-policy-20261019.md) cover SRR selection and live release refresh.

Sine99's carrier LKS `0xB9` is significant: the [CPU level-table audit](opu-level-command-path-20261019.md) establishes note-dependent, quantized TL commands. Those level changes do not alter the rate words above. A static gain difference cannot by itself change an exponential decay slope; signal-dependent effects or capture dynamics may still interact with the differing levels.

## Reverb history and interpretation of the recordings

The original Reverb button can establish global effect bit `$04`. Factory99 reload and all nine recipe edits preserve that bit. On note-on, enabled Reverb adds bit `$80` to both operator TL commands; disabled Reverb leaves that bit clear. This demonstrates a software control path, not the chip's response, threshold or elapsed timing. It does not establish that the recordings have Reverb on, either.

The [independent PCM analysis](opu-envelope-independent-20261019.md) found late fundamental declines around 24.3 and 28.4 dB/s in two sampled pitch groups. This command audit removes a possible CPU rate-macro explanation **conditional on the captured patch actually following the authored recipe**. No recorded raw dump establishes that condition, and actual gates, prior effects and capture processing remain unknown. The earlier video remains unqualified under its frozen measurement rules.

The current b13 heuristic makes RKS0 contribute zero note-dependent rate increment. Its D2R law predicts 90.509668 dB/s for 22 and 128 dB/s for 24, at every pitch; these are source calculations, not new measurements. Although the CPU forwards RKS0, the chip could still use pitch/keycode internally at that encoded setting. Neither the present command evidence nor the recording's two groups recover such a law. D1L0 stage scheduling, internal attenuation units, counter precision and the envelope update clock are likewise unresolved. No related Yamaha chip's rate table has been substituted.

## Reproduction and retained failures

Protocol SHA256 `c1a82f352973582e5b6077e4f8e8577d798bb9c0fc49b70066a2e9f494e801aa` was frozen before the formal sweep. The final run passes 27,758 cases: two complete recipes; 2,928 cached-slot/pitch cases; 244 actual serial cases; four twelve-note chords; 24,576 packed-byte tests, producing 49,152 operator writes; and four physical Reverb-history cases. A separately implemented mirrored-bus fixture supplies 16 factory-state and six physical-Reverb spot checks; these do not constitute an independent repeat of the entire sweep.

The initial harness had a syntax error, an ambiguous note-off signature, then two setup mistakes: writer extraction was one call late, and direct note-off omitted its patch argument. The failed formal run retains all 27,260 assertions and its source; actual serial, chord and effect-history groups already passed in that run. Correcting the fixture entry/arguments produced the complete passing repeat. No source bytes, assertions about hardware rates or audio thresholds were changed to rescue a result.

Run `build/opu-digital-primary-leads-20261019/venv/bin/python build/opu-envelope-command-audit-20261019/verify.py` from the repository with the previously acquired, hash-matching firmware present. The fixture uses banked read-only ROM, mirrored stack/RAM and a ready peripheral status with explicit state. It executes original routines and actual button/serial paths, not a complete instrument boot or real-time peripheral simulation. The [JSON ledger](opu-envelope-command-audit-20261019.json) binds sources, routines, decoded fields, command witnesses, counts, independent spot checks and every preserved attempt. Original firmware and full execution artifacts remain ignored. Current b13 core hashes are unchanged.
