# Complete normal Mode00 command frontend

A new research-only C++17 frontend now emits the **complete ordered normal
Mode00 OPU commands** for note-on, note-off, key service, vibrato-delay service,
CC64 and program selection within its declared domain. This replaces the
previous ordinary-event allocation-only stub with composable pitch, level and
release/control plans. It remains disconnected from the instrument. No audible
silicon response, production DSP, default, preset, UI, noise or package changed.

The [source and reproduction guide](../../Tools/prototypes/mode00-complete-command-20261019/README.md)
and [machine-readable receipt](mode00-complete-command-2026-10-19.json) retain
the prospective design, implementation bindings, every final result and all
earlier failures. The completed waveform audits did not identify a justified
feedback-delay or phase-reset correction; this component instead implements
directly verifiable original software behavior.

## Evidence and exact scope

The original PSS-680 and PSS-780 executable identities match the
[pinned primary MAME inventory](https://github.com/mamedev/mame/blob/983e76f8cd84f8da8d14241c9f07a5ee138cc3eb/src/mame/yamaha/ympsr16.cpp).
Acquisition and constructed-state bus limitations follow the existing
[pitch](opu-pitch-command-path-2026-10-19.md),
[level](opu-level-command-path-2026-10-19.md),
[release](opu-release-command-path-2026-10-19.md) and
[allocation](opu-allocation-command-path-2026-10-19.md) ledgers. Field meanings
follow Yamaha's [exact owner manual](https://usa.yamaha.com/files/download/other_assets/1/317511/PSS780E.PDF).
Original firmware, recordings, factory-derived fixture payloads and expanded
traces remain local and ignored.

The accepted domain is the full normal twelve-slot pool, source 0, notes 36–96,
shared working-patch cache tags `$FF`, and ordinary pending key counters 0/1.
Explicit snapshots supply stable raw bend MSB, signed span, fine offset, volume
index, global effect state and twelve actual vibrato-delay counters. Construction
does not imply boot. Invalid snapshots, undocumented TL bit7 inputs and
out-of-domain events reject before authoritative mutation.

One existing `Mode00ProgramCommands` instance owns allocation, held edges,
program/patch cache and global effects. There is no second allocator and no
second stale effects snapshot. Program selection changes that owner's factory
Vibrato/Sustain flags while retaining Reverb. Independent active delay counters
survive program reload; the retained 40 original factory-selection witnesses
contain no writes to their RAM range `$248E–$2499`.

The claimed IO domain is `$0200–$02FF`. The compared event traces also contain
24,024 writes to peripheral `$0327`; these are counted separately and excluded
explicitly. This is not full instrument/MIDI-output emulation. Mode99, CV,
accompaniment, physical-key polling, portamento, live pitch-message queues,
physical volume/Vibrato/Reverb button handlers and a timed scheduler are not
implemented. Stable controller snapshots and explicit service invocations are
the boundary, rather than invented timing or empty success stubs.

## Complete command order

For a newly accepted edge selecting a normal slot, note-on emits nine words:

1. Old modulator and carrier RR/SRR words, then paired key-off.
2. Both integer key-scaled TL words, with carrier-only volume and separate
   Reverb control bit.
3. Three exact packed pitch words.
4. Temporary carrier D1L/RR with RR15.

The original mapped note is used for key-level lookup; the independently bent
and fine-shifted coordinate is used only for pitch. Raw nonzero Mode00
velocities coalesce into the same functional key input. Velocity zero dispatches
off. This research behavior does not change the expressive modern presets.

One **key-service invocation** visits pending slots in order and emits PMS/AMS
control with delay initialisation, restores the raw carrier D1L/RR byte, and
asserts the paired key-on bits. The restored rate is raw RR, not SRR. Its
vibrato-delay counter is initialised to twice cached VDT even when Vibrato is
disabled; nonzero delay suppresses PMS at this point.

One separate **vibrato-service invocation** decrements nonzero delay counters.
A counter reaching zero emits the cached PMS/AMS word only when runtime Vibrato
is enabled. This can happen after note-off; key-off does not erase the counter.
No milliseconds or synthesis tick rate are assigned to either service.

Ordinary note-off emits both selected RR/SRR words and paired key-off. Every
accepted CC64 message, including a repeated value, replaces the global Sustain
state and refreshes all 24 normal-cache release words. Zero selects RR; every
nonzero raw value selects SRR. It does not delay key-off or clear other effects.

Program selection delegates the already independently verified complete
[target-specific plan](mode00-native-command-bridge-2026-10-19.md). PSS-780 clears
serial keys in descending pitch order before the 168-word reload; PSS-680
preserves the declared input/pending state. Neither is mapped to an audio panic,
history reset or unverified phase restart.

## Controller quantization and a real negative-range quirk

Supported stable pitch inputs are bend MSB 0–127, signed span ±1…±12 and fine
steps −16…+16 in 1/32 semitones. Volume indices 1–9 are the normal physical
panel range; index 0 is an explicitly supported constructed-fixture table value,
not an inferred default.

Negative bend spans are documented in Yamaha's Melody Memory PBR format,
printed p42. The earlier original pitch-state execution exhaustively checked
both signs, all twelve spans and all 128 MSBs. The negative case reverses the
**input byte first**: 0→127, 127→0, otherwise `128−MSB`. The positive table's
exceptional MSB62→61 and MSB127→128 rules are then applied. Simply negating an
already rounded positive bend is wrong at some steps.

For span −12, the offsets below are in 1/32-semitone units:

| Raw MSB | Actual negative-range offset | Negated positive-range shortcut |
| --- | ---: | ---: |
| 0 | +384 | +384 |
| 62 | +12 | +18 |
| 66 | −18 | −12 |
| 127 | −384 | −384 |

The new bounded original-program matrix verifies composition with negative
span, selected MSBs, signed fine offsets, all effect masks, several pitches and
volume boundaries on both models. The native arithmetic checks cover the full
accepted pitch-controller domain. These are functional command outputs, not
newly measured cents, accumulator precision, native-clock division or internal
LFO quantization.

## Validation, history and limitations

Each final optimized and ASan/UBSan build passes:

| Evidence family | Cases | Compared events | Complete OPU words |
| --- | ---: | ---: | ---: |
| Existing allocation traces, explicitly posthoc development | 216 | 10,872 | 37,944 |
| Existing release/effects fixtures | 256 | 1,280 | 4,224 |
| Prospectively frozen composition matrix | 320 | 3,200 | 44,400 |
| Corrected prospective VDT controls | 24 | 96 | 480 |

Together with initial-state rows and 24 explicit unsupported-fixture rejections,
this is 16,288 rows, 241,336 exact fields and 87,048 full OPU words per build.
The allocation and prospective families reconstruct 127,041 previous-RAM byte
values before applying changes. The release fixtures retain full word lists but
do not supply full post-event RAM; they are not claimed as another raw-state
proof. Optimized and sanitized stream output is byte-identical.

Both builds also pass 322,802 synthetic assertions: atomic rejection, complete
word order, positive/negative controller arithmetic, raw velocity equivalence,
CC64 cache refresh, delay expiry after off, program effects/cache continuity and
structural capacity boundaries. Per-call maxima are 9 ordinary on, 3 off, 36 key
service, 12 vibrato service, 24 CC64 and 204 program words. The fixed plan has
capacity 204; there is no truncating success path. Fixture aggregation repeats
single-invocation service calls outside this plan API.

The tested frontend occupies 312 bytes, its snapshot 264, and a returned plan
840 on this platform. The stream probe observes zero `new`/`new[]` calls around
component operations. It does not instrument every allocator mechanism or test
an integrated audio host. ASan/UBSan pass; unavailable LeakSanitizer is not
claimed.

All initial failures remain:

- A synthetic-test range loop copied a large plan and stopped compilation under
  `-Werror`. Using a const reference fixed the warning before native execution.
- The first complete comparison reported 336 field mismatches. Thirty-two
  retained release setups imported effect flags without the real Vibrato
  button's all-slot delay initialisation. Their corrected setup uses actual
  already-collected neutral-controller post-effect RAM, without changing any
  expected command word.
- The original 24 supplementary VDT setups omitted the original cache loader's
  required zero-page `$03=$FF` selector, producing unsupported cache tags 5.
  Their original data remain retained; faithful cache-tag serialization now
  tests all 24 for atomic rejection. A separately frozen amendment collected
  the corrected 24 cases with the explicit selector. The 320 main cases were
  not rerun or selected after inspecting their results.
- `detect_leaks=1` stopped the sanitized processes before execution because
  LeakSanitizer is unsupported on this platform. Supported ASan/UBSan then ran
  with `detect_leaks=0`; no memory/UB failure was suppressed.
- A binding's chronology sentence incorrectly placed three read-only getters
  after the collector binding. The actual header hashes in both bindings were
  already identical. The prose correction preserves both original bindings.

No command-law header change was needed after the first native comparison; the
final header edit changes only the word “backend” to “frontend” in a comment.
All original executed sources and failed receipts remain bound. This is not a
new hardware recording, a recovered YM3420 circuit or a passed audio adoption
gate.

The integer level helper is an unchanged extraction from the previously public
[candidate patch](../../Tools/prototypes/key-level-20261019/candidate.patch),
matching its original 3,679-byte artifact hash. Its generator is archived inside
that patch. Only command math is reused; the candidate's failed Bowed Bass audio
gate, amplitude conversion and production rejection remain unchanged. Pitch
plans likewise use exact command packing without calling the empirical
frequency conversion.

The useful next integration boundary is a command consumer with one authoritative
ownership state. Key-on phase, finite sine/log tables, feedback delay and level
placement, envelope cadence, Reverb mode, TL-to-amplitude/DAC transfer and supply
sensitivity still require independent evidence. The present engine's two delayed
feedback samples and zeroed per-note phases cannot be relabelled as measured
silicon behavior merely because the software now produces exact command words.
