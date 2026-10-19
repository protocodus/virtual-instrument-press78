# Executable Mode00 program-load commands

The new [research adapter](../../Tools/prototypes/mode00-program-load-20261019/README.md)
reproduces the tested program-load register writes and normal-slot state without
executing firmware. It is separate from production DSP and generates no audio.
All 60 local original-program cases match exactly: the previous 40 factory-entry
and eight serial-caller witnesses, plus 12 prospectively declared ordering cases.
The [JSON ledger](mode00-program-command-adapter-2026-10-19.json) binds the design,
source, original observations and verification receipts.

## A necessary ordering distinction

The earlier [program-load study](opu-mode00-program-load-2026-10-19.md) filled its
mixed cache in ascending pitch order. Its observed descending released-slot
sequence therefore did not distinguish a slot scan from a musical-key scan.
Before implementing the adapter, original instruction review identified the
PSS-780's two virtual-key clearing passes and ordinary key scanner. A separate
protocol froze six serial sequences on both original programs before execution:
shuffled held keys, shuffled held/released/pending keys, descending insertion,
paired pending keys, repeated off/on cache reuse, and thirteen held inputs in
twelve slots. All slot state was constructed through original serial events and
explicit service calls, not by injecting chosen slot RAM.

**PSS-780 processes the cleared keys in descending musical-pitch order, not in a
general descending-slot order.** In the shuffled case it visits cached slots
`2,5,7,9,11,0,6,10,4,8,1,3`, corresponding to pitches
`96,84,72,67,61,60,57,56,55,49,48,36`. Inserting those same pitches in descending
order instead produces release slots `0,1,2,3,4,5,6,7,8,9,10,11`.
The original PSS-780 clears the upper serial-key group 57–96 before 36–56;
the scanner's row/bit order produces the descending sequence in these normal
fixtures. Each edge uses the ordinary highest matching cached-pitch lookup.

The thirteen-held-input witness also retains the stolen input's virtual bit.
Program loading clears that input without inventing a thirteenth cached slot or
release command. PSS-680 emits no corresponding release prefix and preserves its
serial input, rank, paired-key and pending state in all six new cases. This new
ordering evidence complements the previous study; its original observations and
the previously retained erroneous cross-model postprocessor remain unchanged.

## What the adapter implements

`ProgramLoader` composes the unchanged, firmware-free normal-slot allocator with
an explicit program-load operation. On PSS-780, each applicable cleared serial
edge writes the old working patch's two RR/SRR words, preserves the other key's
bits in the paired key command, applies ordinary rank aging, and cancels that
slot's pending keyon. PSS-680 preserves those states. Cached pitches survive on
both targets, and all normal slots retain the shared working-patch tag `$FF`.

Both targets then emit the same ordered 14-write reload for each of the 12 slots:
two TL127 writes, the masked feedback/control word, ten raw operator words, and
the masked second control word. The two channel-control writes encode odd-slot
selection in their high bit. The complete suffix is **168 writes, including 24
TL127 writes and no replacement actual note-level writes**. Reselecting identical
patch data still emits that sequence. Existing cached-pitch ownership is not
erased by the reload.

The caller supplies an already-resolved 32-byte shared working patch and internal
program identifier. In particular, byte23 must contain the factory-effect flags
which the original loader resolved separately before storing the working patch.
The adapter includes no factory bank or panel-number translation table. It seeds
the new Vibrato/Sustain state from those supplied flags while retaining Reverb
and uses the old state for the release prefix. The original 60-case comparison
starts from Sine99 with Reverb off; additional nonzero RR/SRR/control coverage is
synthetic arithmetic testing, not another original-CPU effect-state sweep.

Ordinary `serial()` and `service()` methods deliberately expose only the existing
allocator's selected pitch slots, paired key writes and associated state. They
do not claim complete note-on/service IO: pitch-word and level construction,
carrier-RR restoration and other service writes remain outside that view. A
service count denotes invocations, not milliseconds. The native candidate's
immediate-keyon implementation is not used as a timing oracle.

## Verification and limits

The first frozen comparison passes all 60 cases and 10,422 complete ordered OPU
program-selection writes. It checks 16,536 state/command fields, reconstructs
49,816 RAM changes against their prior bytes, and compares 1,104 surrounding
serial/service events. These are post-observation development comparisons; the
12 new original executions had their own prospective design. No CPU execution
or audio rendering occurs in the comparison script.

The exported standard-library tests pass 12,332 synthetic assertions and 132
state/key assertions across the 12 new retained cases. The latter use freshly
authored synthetic sound fields, so they distribute no factory payload. The
unchanged allocator's existing 16-case, 526-event regression also passes its
3,682 assertions. The public state subset does not replace the complete local
command-word comparison, whose original traces remain ignored. All new original
executions and the first adapter comparison completed without errors; no failure
was discarded or retuned away.

Scope is normal twelve-slot Mode00 operation, shared `$FF` caches and the declared
channel0 serial fixture over notes36–96. Physical-key matrix polling, complete
boot, accompaniment, rhythm, Mode99 program selection, source/CV host ownership,
other pending-counter branches and a complete main-loop scheduler are excluded.
The adapter rejects unsupported cache/mode/range inputs rather than extending
the evidence to all 128 host notes.

These command facts do not establish how a live YM3420 responds audibly to TL127,
parameter replacement or keyoff. Envelope restart, oscillator phase, residual
sound, Reverb response and analog/BBD memory remain separate questions. In
particular, the command plan is not an `allSoundOff()` instruction or a recovered
hardware silence/retimbre algorithm. No shipping source, native wrapper, preset,
default, audio fixture or completed benchmark changed here.
