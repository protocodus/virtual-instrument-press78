# Mode 00 factory loading rewrites existing slots

**The original PSS-780 program loader does more than select a patch for future notes.** It clears the tested serial-key state, releases held or pending normal slots, and then rewrites all 12 normal slots. The PSS-680 also rewrites all 12 slots, but preserves their held/pending input state in the tested path. Neither behavior is reproduced by the plugin’s current future-voice-only `setPatch(..., false)` contract. No production code, allocator candidate, audio, or completed benchmark changed in this investigation.

The [machine-readable ledger](opu-mode00-program-load-2026-10-19.json) binds the prospective protocols, original source identities, all 48 witnesses, compact state results and retained failure. The original program identities match the [pinned primary MAME inventory](https://github.com/mamedev/mame/blob/983e76f8cd84f8da8d14241c9f07a5ee138cc3eb/src/mame/yamaha/ympsr16.cpp); acquisition and bus limitations follow the existing [pitch](opu-pitch-command-path-2026-10-19.md), [release](opu-release-command-path-2026-10-19.md) and [allocation](opu-allocation-command-path-2026-10-19.md) ledgers. Executable program files, full disassembly, factory payloads and expanded traces remain ignored and are not redistributed.

## Existing evidence and new scope

The independently audited [Sustain-policy investigation](sustain-policy-2026-10-19.md) already retained Human Voice→Musical Saw program-load traces. Those showed a shared working-patch reload in Mode00 and explained why the plugin’s future-only patch contract was an explicit adaptation. The present pass checks the previously unreported pending counters, rank updates, cached pitches and virtual-key bitmap.

A protocol was frozen before 40 original-CPU executions: two verified programs, Sine99 as the source, four destinations and five slot states. The destinations are Bowed Bass, Human Voice1, Musical Saw and a same-Sine99 control. Their panel numbers are 65/93/97/99 on PSS-780 and matched-payload 35/94/98/99 on PSS-680. The state cases are empty, pending keyon, held after one key service, released by noteoff, and twelve cached normal slots containing held, released and pending subsets. Actual serial/key-scan routines construct these states; slot RAM is not injected.

Eight further cases were separately frozen before execution to confirm the complete serial `C0` Program Change caller with a held note. Every caller’s complete OPU write sequence and relevant final state matches its own model’s factory-entry witness. This is not merely a behavior inferred from an isolated helper’s name.

The constructed bus uses mirrored RAM, read-only original ROM, bank switching and an always-ready peripheral. Neutral controller state, volume index9 and initially disabled Reverb are explicit fixture inputs. Neither a complete machine boot nor the keyboard’s physical key-matrix polling loop is simulated.

## What the original instructions do

On PSS-780, factory entry `$D936` first calls the zero-mode input-clearing routines `$BE14` and `$BE3F`. Their scans cause ordinary noteoff processing, including old release-rate writes, key commands, pending-counter cancellation and the established release/rank aging. The selected factory payload is copied into the shared working patch by `$D8F4`; `$C6EE` iterates eligible slots and `$C6C3` writes each slot. The actual Mode00 serial program handler `$B574` calls `$D936` at `$B587` for the tested program values.

PSS-680 entry `$D831` lacks that input-clearing prefix. It stores the new program and reaches the working-patch copy `$D7EF` and slot reload `$C5E9`. The difference is visible in the original instructions and retained outputs, not an audio-derived interpretation.

| Operation in these normal-slot witnesses | PSS-780 | PSS-680 |
| --- | --- | --- |
| Reload existing slot parameters | All 12 slots | All 12 slots |
| Level commands during reload | Code127 to both operators in every slot | Same |
| Held/pending slots before reload | Ordinary keyoff/release processing | No keyoff from program selection |
| Virtual serial-key bitmap | Cleared | Preserved |
| Pending key counters | Cancelled | Preserved |
| Rank bytes | Ordinary release/aging updates | Unchanged |
| Cached keyboard pitches and shared-patch tag `$FF` | Preserved | Preserved |
| Repeated MIDI note-on after load, without off | Accepted because its virtual bit was cleared | Still coalesced for a held input |

The parameter reload is **168 OPU writes: 14 per slot**, including 24 level-code127 writes. The remaining writes configure operator/control fields from the selected working patch. The final168-write reload sequence and working-patch payload agree across both programs for every matched destination and state. The complete program-selection sequences differ when PSS-780 adds keyoff processing first. Even selecting Sine99 again invokes the reload; identical patch data does not make it a no-op.

An empty or already-released case has168 OPU writes. A PSS-780 case with one held or pending note has171: two old release words and one key command precede the reload. Its mixed twelve-cache case has198, releasing ten held/pending slots. PSS-680 has168 in each of these cases. The cached pitches survive: the loader does not reset the allocator into an empty-note-cache state.

After loading, eight explicit key-service invocations produce no OPU writes on PSS-780. On PSS-680, the pending cases retain their counters and emit the corresponding key commands on service. This says nothing about how many milliseconds those invocations represent. A fresh off/on edge still schedules and services a note in every case.

## Verification, correction and implication

All40 factory witnesses and8 serial-caller witnesses completed without execution errors. Postprocessing checks1,436 explicit state/command facts and reconstructs all30,647 retained RAM changes against their previous values. It verifies all12 operator reloads, both models’ distinct rank/bitmap behavior, cross-ROM reload equality and exact caller equivalence. Full IO writes include original instruction addresses; no source observations were dropped.

The first postprocessor incorrectly expected the PSS-780’s key-clearing behavior on both models. It failed on the PSS-680 pending-note case. That script, error and raw observations are retained. The corrected analysis distinguishes the models; it does not rerun the firmware until it agrees. A provisional message that generalized the PSS-780 result was corrected before this report.

These are **software command facts**, not a recovered audible retimbre or stop law. Code127 writes and keyoff do not by themselves measure the YM3420’s live level response, envelope restart, oscillator phase, or residual chorus/output memory. Likewise, physical-key polling or other later main-loop activity is outside the constructed serial-key fixture. Reverb was initially off here; the actual recording’s effect state is not reconstructed by this task.

The completed hardware comparison keeps old patch snapshots on held and releasing plugin voices. It therefore omits the original full-slot rewrite and, for PSS-780, the observed program-change key clearing. Its results remain frozen with that limitation; the new evidence must not retroactively change its timings or scores. A future isolated comparison would need a prospectively declared program-load policy and event order, plus a separately justified audible response. This pass makes no default, DSP or benchmark change.
