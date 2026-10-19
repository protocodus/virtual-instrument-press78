# Native command frontend for original program loading

A bounded C++17 research bridge now reproduces the verified Mode00 program-load
command/state behavior while reusing the frozen native allocator helper. It is
disconnected from the instrument and produces no audio. The design was frozen
before implementation and tests; no production, wrapper, GUI, preset or default
changed.

The current native candidate has several deliberately different boundaries.
`Press78Engine::setPatch(..., false)` retains old voice snapshots and affects
future voices. Its original allocation branch calls `allocator.service(1)`
immediately after starting a voice, preserving its existing delivery behavior.
The helper's `allNotesOff()` visits ascending host notes in two source namespaces;
`allSoundOff()` additionally clears signal histories. None is a substitute for
the recovered original program-load sequence.

The bridge instead owns a validated full twelve-slot normal Mode00 state, with
no exposed CV namespace, first-N pool extension or timed scheduler. Its accepted
serial range is 36–96. A caller-supplied resolved working patch carries the actual
factory-effect flags at byte 23; no factory bank or panel-number map is included.
The same unchanged native allocator supplies rank aging, highest cached-note
reuse, key-edge coalescing, paired key bits and pending counters.

For PSS-780, program loading visits the held serial keys in descending musical
pitch order and sends each matching slot's old release words before its keyoff.
This preserves the permutation evidence: descending pitch order need not mean
descending slot order. It also clears a stolen input without inventing a cached
voice. PSS-680 preserves those states. Both targets then replace shared metadata
and emit the ordered 168-write operator reload for all twelve slots, retaining
cached pitches and `$FF` tags. The reload contains 24 TL127 writes and no later
actual note-level values within the same operation.

`ProgramPlan` stores at most 204 register writes without allocation. The bound is
structural: distinct held pitches can match at most twelve slots, giving at most
36 old-release/key writes before the fixed 168-word suffix. Unsupported snapshots,
targets, pools, source 1 bits, slot source IDs, cache flags, note ranges and pending
counters are rejected before mutation. Manual services operate only on accepted
counter 0/1 states, so the helper's twelve-key result capacity is sufficient.

The native fixture was frozen against all 60 original cases, with no new firmware
execution. Each case is exercised by sequential event replay and separately from
its original pre-load snapshot. Optimized and ASan/UBSan builds both pass 1,344
rows, 18,696 exact fields and 120 full plans containing 20,844 program-load words.
The fixture preparation also checks 2,268 commands against the independently
expressed Python adapter and verifies 49,816 retained RAM previous-byte values.
Both builds pass 81,361 synthetic assertions covering control masks, register
addresses, old RR/SRR selection, both target policies, maximum plans, unsupported
scope and atomic rejection. There were no compile, sanitizer or comparison
failures.

The first generated receipt initialized an `allocations: 0` field for both
binaries, although only the stream probe instruments allocations. That metadata
mistake is preserved in the original receipt and corrected in
`validation-scoped.json` without changing source or rerunning tests. The actual
stream probe observes zero `new`/`new[]` calls around 1,344 frontend operations per
build. It does not instrument every allocation mechanism or validate a Reason
host. Measured native sizes are 280 bytes for the frontend, 232 for its snapshot
and 856 for a returned plan; these are not an integrated wrapper budget.

The bridge is a concrete interface for a future command-driven backend, not a
claim that the existing analytical DSP already implements the commanded hardware
behavior. The next composable pieces would be the verified pitch-word compiler,
the exact level/key-scaling command builder, and live CC64 RR/SRR refresh. They
must share one authoritative cache/ownership state and retain register order.
Their command correctness does not by itself identify TL-to-amplitude transfer,
Reverb envelope behavior, keyon phase, an envelope clock or service cadence.
Those pieces are a roadmap only; no additional command APIs or audio laws were
implemented in this task.

Only program selection returns a complete normal OPU plan. The ordinary
note/service event results remain an allocation-only subset, excluding ordinary
note-off RR writes as well as pitch, levels and carrier-RR restoration. The three
auxiliary cache arrays reproduce the fields copied by reload, not their later
vibrato-service or main-loop evolution; their raw comparisons apply at reload.

In particular, the program-load writes must not be translated silently into a
host panic or output-history reset. The chip's response to live TL127 and other
parameter writes, and residual analog/BBD state, still require separate evidence
or clearly labeled hypotheses. Physical-key polling, accompaniment, rhythm,
Mode99 program loading and modern CV policy remain excluded. The original traces
are reused development evidence, not a new audio holdout.

An independent read-only review passes 126,751 checks, including every output
row, all 120 complete plans per build, raw-state reconstruction, source/capacity
guards and the allocation-measurement correction. It performs no new native,
original-program or audio execution. Its initial source-scan false positive
matched explanatory comments; that checker-only failure and correction remain
retained in the independent receipt.

The [source and synthetic tests](../Prototypes/mode00-native-command-20261019/README.md)
and [machine-readable ledger](mode00-native-command-bridge-20261019.json) are
exported without original firmware, factory payloads or expanded source traces.
The preceding [Python command adapter](mode00-program-command-adapter-20261019.md)
contains the ordering investigation; the native component reuses that evidence.
