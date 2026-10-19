# Original normal-voice allocation commands

The original PSS-780 and PSS-680 programs do not use the current engine's general stacking and oldest-voice policy in every case. Mode 00 coalesces repeated held keys and prefers a slot that previously played the same note, including a released slot. Mode 99 stacks received duplicates and searches matching note-offs from the highest slot index. Both use a saturating eight-bit event rank that gives released slots priority. These are recovered software-command behaviors, not measured envelope, oscillator-phase or elapsed-time rules. The shipping b15 engine is unchanged.

The [provenance ledger](opu-allocation-command-path-20261019.json) binds the frozen protocols, original-program identities, complete ignored observations, independent execution and [functional prototype](../Prototypes/voice-allocation-20261019/README.md). Original program identities match the [pinned primary MAME inventory](https://github.com/mamedev/mame/blob/983e76f8cd84f8da8d14241c9f07a5ee138cc3eb/src/mame/yamaha/ympsr16.cpp). Acquisition and constructed bus limits follow the earlier [pitch](opu-pitch-command-path-20261019.md) and [release](opu-release-command-path-20261019.md) investigations. The original executable files, full disassembly, factory payloads and expanded original IO traces remain ignored and are not redistributed.

## Mode 00: key edges and same-note slot reuse

In the tested serial-to-keyboard path, another note-on for a held pitch does not produce another input-bitmap edge or allocate another slot. Four note-ons for MIDI 60 therefore allocate only slot 0. The first note-off releases it; additional note-offs do not generate more OPU key commands. This behavior applies to the tested Mode 00 receiver/scan path, rather than establishing one universal duplicate policy for every MIDI mode.

For a new input edge, the normal-voice path first searches existing kind-0 slots for the stored keyboard pitch. It keeps the highest matching slot if there is more than one. The search does not require the old slot to remain held or audible. If no matching slot exists, the general rank selector supplies one. In the neutral fixture:

| Sequence | Mode 00 allocated slots | Mode 99 allocated slots |
| --- | --- | --- |
| on60, off60, on61, off61, on60 | 0, 1, 0 | 0, 1, 2 |
| Four on60 messages without an off | 0, then no further allocation | 0, 1, 2, 3 |
| Fill notes 48–59, off53, on72 | 0–11, then 5 | 0–11, then 5 |

The ordinary Mode 00 note-on path always sends keyoff to its selected slot, then configures and schedules keyon for that same slot. The earlier release investigation identifies the temporary carrier RR15 and subsequent raw-RR restoration. The present trace confirms the selected physical slot and key-command order. It does not identify the service period or establish how keyon resets the chip's phase and envelope state.

This gives a concrete alternative to the current engine's independently continuing old release on a same-note retrigger. A reused hardware slot cannot simultaneously represent two independent FM channels. Chorus/output memory and chip-side envelope transitions can still retain sound, so slot reuse alone does not specify the audible retrigger transient. The earlier [recorded interruption](retrigger-allocation-audit-20261019.md) remains compatible evidence, not a newly isolated timing measurement.

## Event rank, released voices and saturation

The general selector examines eligible kind-0 slots and chooses the strictly smallest unsigned rank below 255, keeping the lowest slot on ties. Rank bit7 separates held from released classes. The identified state operations are:

```text
mark held:     rank[selected] = 255
mark released: rank[selected] = 127
age pass:      decrement each rank except 0 and 128
```

Consequently ordinary completed held/released updates leave the selected slot at 254/126. Released ranks 0–127 outrank held ranks 128–255. Old held ranks stop at 128; old released ranks stop at 0. Once several entries reach the same floor, slot-index tie-breaking replaces unbounded chronological age. This is an actual finite-state quirk; it does not justify random memory faults or aging noise.

The rank is driven by these software events, not by the musical note's measured duration. One or eight key-service invocations between the declared events preserve the same selection behavior in these fixtures. Ordinary Mode 00 note-on performs selected-slot off and on rank updates, so it advances other ranks twice. A Mode 99 note-on into a released slot advances them once; stealing a held slot first performs its release update. These statements concern the identified normal-voice paths. Rhythm, accompaniment, other program paths and a complete keyboard main loop were not reconstructed.

## Mode 99: cached programs and highest-slot note-off

Before the general selector, Mode 99 searches released kind-0 slots whose cached program equals the requested channel program. It prefers the smallest rank in that set, with the lowest slot breaking ties. This can preserve a matching cached voice instead of selecting the globally oldest slot with another program. The cached selector was checked directly across constructed program/rank states; the complete event adapter's development sequences keep one program per case and do not implement the keyboard's whole program-change machinery.

Received note-off searches slots 11 down to 0 for matching received-channel and received-note bytes. The first match is released and its received-note byte becomes the zero sentinel. Four duplicates initially allocated 0, 1, 2, 3 are thus released 3, 2, 1, 0. This is **highest matching slot**, not a general newest-note/LIFO rule: slot reuse and wrap can change chronological order.

The original observation fixture enabled only channel 0. Its channel 1 messages were ignored by the original receive mask; those cases were retained as filter observations, not successful multichannel allocation tests. Independent instruction review identified RAM`$3E08/$3E09` as Mode 99 receive masks, separately from Mode 00's`$3E0A/$3E0B`. A new, separately frozen mask 3 fixture enables channels 0 and 1. Both original programs then allocate 0, 1, 2 for ch0/ch1/ch0 on60 and release 2, 1, 0 for matching ch0/ch1/ch0 offs. The independently authored public prototype reproduces these additional witnesses.

## Verification and limits

The first protocol was frozen before executing 456 declared sequences: both original programs, Modes 00/99, four literal panel selections and explicit 0/1/8 service schedules. Every initialization write, IO write, changed RAM value and observation remains retained. All 456 sequences completed without ROM-write or instruction-limit errors. The literal four panel numbers do not imply identical timbres across the two instruments; the independent serial witnesses use Sine99, and the shared allocator functions are checked separately.

A second, post-observation protocol froze the functional rules before 106,496 exact primitive assertions. It covers all 256 rank and kind-byte values in declared boundary configurations, slot ties, 0/128 rank floors, 4,096 deterministic random selection/cached states per model, and duplicate/empty note searches. Seven small functions are byte-identical between the two programs, with independently located entry points and span hashes. Some constructed inputs are unreachable or outside accepted serial ranges; these test the primitive's arithmetic, not new supported playing states.

The functional event adapter was authored after the initial observations, frozen, then compared with every recorded event. All 456 development cases, 22,032 events and 154,224 field comparisons pass exactly for selected pitch slots, serial/service key writes, all 12 rank bytes, keyboard notes, received-note/channel bytes and pending-key counters. This is posthoc development agreement, not an audio holdout or proof of untested program behavior.

An independent implementation of the mirrored-RAM/banked-ROM bus imports only py65 and executes 24 additional cases. Twenty-two overlapping cases reproduce 272 serial events exactly for selected pitch slots and both serial/service key commands; two mask 3 cases provide the new enabled-channel witnesses above. The parent independently recomputed that comparison. A separate reviewer replays the original sparse changes into complete RAM images, verifies all 199,250 changes against their prior values, and repeats the 154,224 adapter comparisons without a mismatch. A public fixture subset contains 16 cases, 526 events and 3,682 exact assertions, runnable with the Python standard library and no firmware files.

The pitch-slot comparison sorts unique destination slots; it does not verify pitch-write multiplicity, order or payload. Key-command ordering is compared directly. The frozen adapter comparer records the primitive-result hash but does not itself recheck that one dependency at runtime. The independent review confirms that the current bytes match the binding; a future reusable execution wrapper should enforce that guard. Neither caveat changes the retained results into evidence for a chip-internal behavior.

Initial Mode 00 rank bytes are zero in the constructed fixture. The actual Mode 99 initialization path produces 115–126 and populates cached programs; these snapshots are retained and supplied to the adapter. Neither is relabelled as a measured complete-boot state. The always-ready OPU, explicit neutral controllers, zeroed unspecified RAM and manually invoked services remain limitations. No phase reset, key-service cadence, release law, DAC behavior, additive noise, audio regression score or production default is inferred from these software checks.

The next DSP candidate needs to apply the verified slot policy while explicitly handling modern polyphony limits, MIDI/CV source ownership, patch snapshots and compatibility. Its unknown chip-timing behavior must remain labelled. Fixed recording comparisons and native/Rack event tests are still required before any shipping change; the b15 factory bank and DSP remain unchanged by this study.
