# Original OPU release and effect commands

Execution of the original PSS-780 and PSS-680 programs now separates two previously unresolved controls. Sustain selects the stored sustain-release rate and still sends keyoff. Reverb adds a control bit to both operator-level commands; the traced note-off path does not replace RR with a slower numerical value. This establishes firmware command behavior, not the YM3420's internal Reverb envelope law. Production DSP, presets and defaults are unchanged.

The [JSON ledger](opu-release-command-path-20261019.json) records sources, routines, representative commands, complete local artifact hashes and limitations. The original program files have the identities published by the [primary MAME driver](https://github.com/mamedev/mame/blob/983e76f8cd84f8da8d14241c9f07a5ee138cc3eb/src/mame/yamaha/ympsr16.cpp); their ordinary public acquisition is documented in the [pitch-command investigation](opu-pitch-command-path-20261019.md). Original ROMs, full disassembly and complete source-derived traces remain ignored and are not distributed. A matching ROM identity does not establish redistribution permission. Field names follow Yamaha's [PSS-780 owner manual](https://usa.yamaha.com/files/download/other_assets/1/317511/PSS780E.PDF), especially the voice format on printed p41 and effects/performance state on pp9 and42.

## What the original program writes

For a voice slot, the release routine preserves the D1L high nibble and chooses the low nibble from RR or SRR:

```text
release_word = (raw_D1L_RR & 0xf0)
             | ((sustain_enabled ? raw_SRR : raw_D1L_RR) & 0x0f)
```

For slot0 these words go to `$02E0` and `$02E8`, followed by keyoff at `$0208`. Sustain does not withhold that keyoff. Across twelve occupied slots the key command preserves the other voice's bits in each paired slot. The exact register interpretation comes from the software's writes; no internal envelope clock or rate table is inferred.

The PSS-780 focus voices give these release nibbles. D1L remains unchanged in every case.

| PSS-780 displayed voice | Modulator RR → SRR | Carrier RR → SRR | Modulator/carrier D1L |
|---|---:|---:|---:|
| 65 Bowed Bass | 4 → 3 | 6 → 5 | 1 / 0 |
| 93 Human Voice 1 | 3 → 1 | 7 → 5 | 1 / 0 |
| 97 Musical Saw | 3 → 1 | 6 → 4 | 0 / 0 |
| 99 Sine Wave | 8 → 5 | 8 → 5 | 0 / 0 |

Reverb instead adds `$80` to both operator-level/control writes, leaving their low seven bits unchanged. In the neutral note74 Human Voice 1 fixture, the two level commands are decimal36/54 with Reverb off and164/182 with it on. Normal noteoff remains `$02E0=19`, `$02E8=7`, `$0208=0`; with Sustain enabled it becomes17/5/0, regardless of Reverb. The last zero refers to this single occupied slot; it is not a universal keyoff byte for polyphony.

This directly identifies a Reverb-controlled chip input. It supports investigating a chip-side envelope mode, but does **not** recover its trigger threshold, release slope, timing, or interaction with envelope stages. In particular, the TX81Z's −18 dB mechanism remains a different-chip precedent, not an OPU constant. The earlier [Reverb evidence note](reverb-release-evidence.md) and [Human Voice 1 tail comparison](human-voice1-release-audit.md) remain historical observations; no tail multiplier was fitted here.

## Live controls and scheduling

All128 CC64 values were executed on both ROMs in both modes. Zero disables Sustain; every nonzero value, including1 and63, enables it. In Mode00 this changes global state. In Mode99 it changes the receiving channel's state. Both paths refresh RR/SRR commands on matching cached slots, including a slot already sent keyoff. A firmware command update is observed; the resulting instantaneous hardware envelope slope has not been measured.

The physical Sustain button is different in Mode99: it changes global state and emits MIDI output, but does not refresh the received channel's voice in the tested path. The physical Reverb button produces no immediate operator writes for held or released notes in these fixtures. Its state is incorporated when the level builder runs; it is not an immediate RR rewrite. These distinctions matter when comparing keyboard controls, received MIDI, and a modern plugin's pedal behavior.

A new note initially puts1 in its key-on service counter and temporarily writes carrier RR15. One key service pass restores the carrier's raw RR and sends keyon. If noteoff arrives before that pass, the firmware clears the counter and no later keyon appears. These are invocation-order results, not measured milliseconds. The service code contains additional counter branches, but this report does not assign them a measured retrigger or voice-stealing duration.

After ordinary keyoff,32 invocations of the identified key-on and vibrato-delay services produced no further RR or operator-level writes. Of512 main cases,480 produced no writes and32 retained pending vibrato-only writes at `$0218`–`$021D`. All are preserved. This bounded check must not be described as a complete main-loop timing simulation or proof that no other firmware path can ever update the voice.

## Coverage, numbering and limits

The current fixtures pass1,280 asserted checks:512 combinations of two ROMs, two modes, four panel programs, four notes and eight effects;128 velocity-zero note-off equivalences;512 CC64 value cases;64 matched-payload cross-ROM cases; and64 early-off cancellation cases. Another96 held/released control transitions and four twelve-slot sequences are retained as observations. There was no audio measurement, fit or new hardware holdout.

Factory numbering needs care. PSS-780 panel65/93/97/99 maps to internal35/94/98/99. The PSS-680 uses identity ordering for the tested panel values. Its exact32-byte payload matches for those four PSS-780 voices occur at panel35/94/98/99, and64 matched-payload cases produce identical noteon, key-service and noteoff IO writes across the two programs. The main sweep also retains the originally requested literal65/93/97/99 on each model; it does not call the PSS-680's literal93 Human Voice 1. A Mode99 wire program is not automatically a PSS-780 display number, and no earlier Mode00 audio result was relabelled.

The bus models read-only ROM, bank switching, mirrored stack RAM and an always-ready peripheral. Tests execute original factory load, mode initialization, serial parsing, panel edges and voice services with explicit neutral controller RAM. This is constructed-state software execution, not full boot or hardware emulation. All original factory/mode initialization writes remain in the ignored result. An initial assertion incorrectly expected RR writes before Mode00 peripheral `$0327` writes; its256 failures are preserved. The corrected assertion checks ordering within OPU `$0200`–`$02FF` while still retaining every `$0200`–`$03FF` write. Exploratory fixtures that omitted key-on service are also explicitly superseded rather than used as evidence.

The current Press78 engine uses a conventional pedal that defers release, and chooses a patch's SRR at voice creation. Those choices differ from the recovered CC64 command behavior and dynamic RR refresh. It also lacks the recovered Reverb mode behavior. These are concrete implementation gaps, but the command evidence alone does not justify changing the analytical envelope rates or inventing the chip's Reverb law. Any future compatibility policy and envelope implementation require separate review.

Reproduction uses the retained py65 environment to run `verify_release.py`, `verify_transitions.py`, `verify_matched_payloads.py` and `verify_early_off.py` in ignored `build/opu-release-command-path-20261019`, with the original local files and hashes recorded in the ledger. The PSS-780 entry points are serial`$B334`, Mode00 scan`$A01C`, effect scan`$E0A7`, RR writer`$C984`, noteoff`$CA74` and key service`$C944`; the ledger supplies corresponding PSS-680 addresses and dependencies.
