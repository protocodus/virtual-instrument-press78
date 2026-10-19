# Front-panel Decay mapping — 19 October 2026

The PSS-780 panel's **Decay parameters 2 and 3 edit the modulator and carrier D2R fields directly**. They do not edit D1R or combine several envelope stages. Starting from Sine 99, carrier display `3.21`, `3.22` or `3.31` means raw carrier D2R 21, 22 or 31. D1R remains 1, D1L remains 0 and RR remains 8. This resolves the parameter ambiguity that prevented interpretation of the producer's held-note decay recordings.

These are original-firmware software findings. No DSP law, preset, output noise, native adapter or UI was changed. The full 32-byte before/after snapshots remain local in ignored research artifacts; this note reports functional changes without distributing firmware or a disassembly.

## Verified path

The program identity and normal public acquisition are recorded in the [pitch-command research](opu-pitch-command-path-20261019.md). The files match the primary [MAME ROM identities](https://github.com/mamedev/mame/blob/983e76f8cd84f8da8d14241c9f07a5ee138cc3eb/src/mame/yamaha/ympsr16.cpp). Envelope field names follow the exact [Yamaha owner manual's voice format](https://usa.yamaha.com/files/download/other_assets/1/317511/PSS780E.PDF), printed p41; the panel is described on printed pp27–28.

The PSS-780 fixture executes the actual factory-selection routine at `$D936`, then simulated Decay-button edges through `$DCDD`. A Decay-button edge selects parameter 2, and the next selects parameter 3. Value-button processing at `$DD2C` reaches the parameter dispatcher `$72F9`; this calls `$6FBA` for modulator Decay or`$702B` for carrier Decay. The editor reads and writes the 32-byte working voice at `$2659..$2678`.

| Panel parameter | Working-payload offset | SysEx payload offset, including bank byte | Meaning |
|---|---:|---:|---|
|2, modulator Decay|10|11|D2R, lower six bits|
|3, carrier Decay|11|12|D2R, lower six bits|

Both editors preserve the upper two waveform bits. Plus/minus changes D2R by one, bounded at 0 and 63. Pressing both Value buttons restores the selected factory voice's D2R while preserving the working waveform. The remaining 31 payload bytes are unchanged, including D1R, D1L, RR, sustain-release rate, attack and rate key scaling.

Each edit refreshes the two D2R/waveform bytes for every slot using the working voice. For slot `v`, address displacement is `floor(v/2)+16*(v mod2)`: modulator at `$02C0+displacement`, carrier at `$02C8+displacement`. In the fixture all 12 slots reference the working voice, so each edit makes 24 such writes. It does not write the D1R or D1L/RR ports. The fixture's ready-busy flag and explicit RAM state do not model the latency of a real button press or parameter change.

## Sine 99 and the producer recipe

Actual factory selection produces the same 32-byte voice payload as the existing published Sine 99 SysEx. The separate all-factory check finds that all 100 published payloads match their PSS-780 firmware-selected payloads exactly. This verifies data identity; it makes no new licensing claim.

For Sine 99, the relevant fields before editing are identical for both operators: AR 63, D1R 1, D2R 0, D1L 0, RR 8, SRR 5 and RKS 0. Applying only the producer's two Decay settings gives:

| Operator | Panel setting | D1R | D2R | D1L | RR | SRR | RKS |
|---|---|---:|---:|---:|---:|---:|---:|
|Modulator|`2.24`|1|24|0|8|5|0|
|Carrier|`3.22`|1|22|0|8|5|0|

This table covers the Decay edits only; it does not assert the recipe's other controls, the recorded effects state or an isolated carrier in every captured window. With D1L 0, a sustained post-attack decrease is consistent with changing D2R even though D1R is unchanged. The earlier interpretation of these panel values as D1R was incorrect.

The producer's samples use a PSS-680. A separate fixture executes that program's factory selection, physical Decay/Value handlers and editor. Its entire 16 KiB bank 2 editor/code region matches the PSS-780 bank byte for byte, and its Sine 99 payload is identical, although stored at a different ROM offset. The distinct fixed-ROM handler addresses are retained in the ledger rather than assumed to be the same.

## Validation and limits

The PSS-780 suite passes 1,901 checks: all 100 factory payloads; every 64-value × 4-waveform × 2-operator × 3-edit-direction combination; 200 factory-reset cases; 64 sequential button-edited values; and the combined 24/22 recipe. The separate PSS-680 suite passes 1,602 checks, repeating the complete value/wave/operator/direction coverage and requested sequential/recipe fixtures; the combined total is 3,503. Both use a standard 65C02 interpreter with MAME's mirrored stack/RAM mapping, banked reads and read-only ROM. These are constructed-state software tests, not a complete instrument boot or hardware-envelope measurement.

The frozen native b11 law with RKS 0 predicts the following sustained D2R slopes. These are calculated from its existing expression, `2 × 2^(D2R/4)` dB/s; they are not new measurements or fitted parameters.

| D2R | Native b11 decay, dB/s | Time to fall 60 dB, seconds |
|---:|---:|---:|
|21|76.1093|0.7883|
|22|90.5097|0.6629|
|24|128.0000|0.4688|
|25|152.2185|0.3942|
|31|430.5390|0.1394|

Recovering the mapping makes a known-setting recording useful for testing this law. It does not validate the full decay curve, recover the chip's envelope clock or justify applying a measured ratio at D2R 22 to every rate, attack and release. The author's edited video still has no qualified rate fit under the current gate/floor controls; recognizing `3.31` and `3.21` does not change that exclusion. No new audio fit was performed here.

The [JSON ledger](front-panel-envelope-map-20261019.json) records routines, raw-field changes, complete hardware-write lists for the selected settings, source and fixture hashes, test counts and local snapshot paths. Reproduction uses the retained py65 environment to run `verify_panel.py` and `verify_panel680.py` under ignored `build/front-panel-envelope-map-20261019`. Original firmware must already be present with the recorded hashes.
