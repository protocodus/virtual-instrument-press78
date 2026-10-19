# MIDI event order and one-frame overlaps — 19 October 2026

The retained binary MIDI has **no same-channel overlapping notes or held duplicate note-ons**. Its193 contiguous same-channel retriggers explicitly place note-off before note-on within the same track. The historical benchmark exporter turns some of those boundaries into one-frame overlaps by rounding onset and gate separately. This establishes a fixture artifact; it does not explain every failed allocator comparison or justify adopting that candidate.

The [JSON evidence](midi-event-order-audit-2026-10-19.json) binds the original file, parser, four timing maps, eight existing event files, exact binary-message locations and every affected boundary. This is a post-benchmark source audit, not a new audio experiment. No event file, timing map, score, DSP, preset, package or artificial-noise policy changed.

## What is actually available

The original experiment retains the publicly linked [Mutopia Eugenia MIDI](https://www.mutopiaproject.org/ftp/JoplinS/eugenia/eugenia.mid),15,128bytes, SHA256 `7ab6f4551b8116590d52dd0566c3f5a7fad89097eb1b64ddf97b60fba47167cf`. It is SMF format1, three tracks,384ticks/quarter. Two identical tick-zero tempo messages specify882,352microseconds/quarter. The exact final time is181.323336s.

The [recording's original uploader](https://www.youtube.com/watch?v=ONfIvtDOog0), AndrewsVintageKeyboards, names Eugenia by Scott Joplin and a MIDI file from the Mutopia Project. This supports the retained candidate's identity, but no checksum, sender project, transmitted-byte log or receiver configuration establishes that these exact bytes were sent unchanged in2017. Public-domain attribution in the existing acquisition ledger concerns the Mutopia score/MIDI; it does not clear the recording or factory bank for redistribution. No media is included here.

An independent decoder preserves every event's track, ordinal, tick and file-byte span. It reconstructs1,779 notes:842 on zero-based channel0 and937 on channel1, all velocity127. All original `start/end/gate/midi/channel/velocity/track/tick` fields match the retained notes JSON exactly. There are no zero-length or negative gates. The existing Mode00 range filter retains1,761 notes and removes18 pitches below36:29×2,34×13,35×3, all on channel1. This filter is distinct from rounding and does not remove zero-gate notes.

Exact rational tempo integration differs from the old accumulated floating seconds by at most1.279×10⁻¹²s for starts/ends and4.663×10⁻¹⁴s for gates. Repeating historical rounding with those exact times changes **zero** accepted onset or gate frames across all four maps. Parser floating drift is therefore not the cause of these overlaps.

## Where overlap appears

The exporter uses, at48kHz:

```text
on  = round(48000 × (offset + scale × source_start))
gate = round(48000 × scale × source_gate)
off = on + gate
```

It then sorts by frame, patch first, off second, on third. Python's nearest/ties-to-even rounding is used; no code adds an inclusive-end `+1`. Rounding two summands independently need not equal rounding their sum. A raw contiguous boundary can consequently become a one-frame gap, stay contiguous, or become a one-frame overlap. One frame here is20.833microseconds.

All eight existing full/Mode00-filtered event files reproduce byte-for-byte from these rules. For the193 same-channel contiguous pairs:

| Fixed timing map | One-frame overlap | Still contiguous | One-frame gap | All merged-MIDI duplicate-ons |
|---|---:|---:|---:|---:|
| Unchanged |16|128|49|17|
| Old scale / median offset |16|126|51|17|
| Nominal scale / median intercept |10|116|67|11|
| Equal-patch robust affine |35|152|6|37|

The raw MIDI also contains one genuine simultaneous same-pitch event on different channels: both channels start MIDI62 at tick40704, with channel1 ending at40896 and channel0 at41184. Both notes are valid in their separate channel streams. If both channels reach the tested Mode00 shared key bitmap, the second on is a held duplicate; the first off clears that shared key. Actual receiver acceptance of both channels remains conditional.

There is one additional cross-channel contiguous boundary, MIDI51 at tick58368. Its canonical track-index merge places off before on, but that intertrack order is not established serial delivery. The robust map makes this boundary a one-frame overlap, explaining its extra merged duplicate count. The other extra merged duplicate is the genuine MIDI62 event.

As an in-memory diagnostic only, directly rounding each mapped source end puts all193 same-channel and all194 global contiguous boundaries at the same frame as their next onset. No corrected event file or audio was generated. Direct endpoints alone would still leave the genuine cross-channel overlap, original message-order loss and unknown sender timing.

## Message order was also discarded

The original parser retains notes but finally sorts simultaneous starts by start time, track and pitch. The exporter subsequently sorts event categories and uses this note-list order. It therefore does not reproduce all original within-track byte order even when frame times coincide. Across every map,492 within-track ON/ON pair orders reverse; chord note-ons have been reordered by pitch.

The complete counts below are **pair inversions**, not numbers of affected notes or audible errors. They compare messages at the same original tick within the same original track; changes between separate tracks are retained separately because actual intertrack transmission order is unknown. The first count column counts each tick once across tracks if it contains any within-track inversion; it is not a count of distinct (track,tick) groups.

| Fixed map | Ticks with within-track inversions | ON/ON inversions | OFF/OFF inversions | Raw OFF-before-ON pairs reversed |
|---|---:|---:|---:|---:|
| Unchanged |317|492|474|77|
| Old scale / median offset |318|492|476|76|
| Nominal scale / median intercept |314|492|475|50|
| Equal-patch robust affine |360|492|453|671|

No distinct-tick message ordering changes were found. The smallest positive spacing between accepted note-message ticks is96ticks. These results show what the fixture changed relative to the retained file; they do not establish how the actual MIDI player merged or serialized tracks. Program commands in the benchmark are100 separately inferred timeline events, not messages found in this MIDI.

## The final Sine99 retrigger

For the final repeated MIDI75, raw track1 places note-off at tick78720 in bytes7197–7200 and the next note-on at the same tick in bytes7209–7212. These are zero-based file offsets with inclusive last bytes. This is an explicit off-before-on sequence, not a raw held duplicate.

| Fixed map | Previous off frame | Next on frame | Exported gap |
|---|---:|---:|---:|
| Unchanged |8,723,419|8,723,419|0|
| Old scale / median offset |8,725,441|8,725,440|−1|
| Nominal scale / median intercept |8,726,164|8,726,164|0|
| Equal-patch robust affine |8,726,017|8,726,018|+1|

In the unchanged and old-offset maps, other Sine99 retriggers also acquire one-frame overlaps. In the two previously fixed Sine supports, global duplicate-on counts are:

| Map |176.1–184.2s|181.55–182.20s|
|---|---:|---:|
| Unchanged |3|0|
| Old scale / median offset |4|1|
| Nominal scale / median intercept |0|0|
| Equal-patch robust affine |0|0|

The nominal and robust maps still failed the earlier Sine audio regression gates despite having no duplicate-ons in either support. Therefore the artifact cannot be used to explain all failed gates. The comparison remains negative for promotion. Message order, allocator-to-voice embedding, sender delivery and the existing envelope/phase/capture uncertainties remain separate issues.

## Recorded mode and unknown delivery

The existing [mode/effect audit](recording-mode-effects-audit-2026-10-19.md) visually reports c.00 at all300 preset snapshots and six late Sine99 snapshots. This pass independently rechecked its existing181.5s frame: preset99 and c.00 are visible. The cached original manual's printed31 explicitly labels c.00 Keyboard Assign and c.99 Sound Source. This is positive sampled evidence for Mode00, rather than an inference from the presence of two MIDI channels.

It does **not** establish the receive-channel filter/mask or uninterrupted state between snapshots. The binary MIDI contains only note-on/off channel messages and18meta events: no CC, program change or SysEx establishes receiver mode, masks or effects. The original-program ownership witness explicitly seeds Mode00 and masks1/3; it establishes that enabled channels share a key bitmap in those constructed tests, not which channels the recording accepted. No serial capture establishes actual arrival times, same-tick track merge or upstream remapping.

A future fixture can prospectively preserve each message's original tick and within-track ordinal, map each tick once, and declare an intertrack merge policy. That would be a new conditional experiment, not a repair of this failed benchmark or a reconstruction of unrecorded wire timing. The current files and failures remain unchanged.

## Reproduction evidence

The ignored audit directory is `build/midi-event-order-audit-20261019`. Its frozen source-only protocol has SHA256 `d853d90c26f7a43606c80c44427136061b6a9cd6051bfb858af3759fd6ffd17d`. `audit.py` independently decodes the binary and reproduces every historical export; `audit_order_loss.py` compares original same-tick byte order with exported order. Complete decoded events/notes, every adjacency, raw/rounded Boolean edge logs and every negative exported gap remain hash-bound in the JSON ledger. The scripts refuse to overwrite their result files. No audio was extracted, measured or rendered, and all audited existing input hashes still match.
