# Mode00 MIDI ownership and comparison correction, 2026-10-19

Enabled MIDI channels share one received-key state in the tested original Mode00 paths. They must not be interpreted as independent MIDI/CV owners in a recording comparison. This extends the [original allocation study](opu-allocation-command-path-20261019.md); no production DSP or patch changes follow yet.

Eight constructed Sine99 sequences on the hash-identified PSS-780 and PSS-680 programs contain 36 serial messages. The test explicitly sets Mode00's receive mask at RAM `3E0A/3E0B`, first enabling channel 0 alone and then channels 0 and 1. With both enabled, channel-0 on 60, channel-1 on 60, channel-0 off 60 and channel-1 off 60 leave the received-key byte at `24C5` as `1,1,0,0`. Only the first on selects a new slot. The first off clears the common key even while the other channel has not sent off. Distinct pitches sent across the channels select cached slots `0,1,0` on the tested on/off sequence. A channel excluded by mask 1 has no corresponding effect.

The first frozen test retains **two failed auxiliary assertions**. It incorrectly compared a selected slot number with the raw packed key-port byte: a keyoff with neither paired voice active writes zero for either slot, rather than byte 1 for slot 1. All eight prospective pitch-slot arrays were correct. A separate review checks literal port bytes and the received-key RAM byte; a root recomputation from the unchanged raw RAM/IO reproduces all 32 observed-field assertions. Neither review reruns the firmware or repairs the original result. The [machine-readable evidence](opu-mode00-midi-ownership-20261019.json) retains the failures, protocol and artifact hashes alongside these qualified observations.

## Consequence for the audio comparison

Each of the four existing timing scenarios contains 842 on/off pairs tagged channel 0 and 919 tagged channel 1, plus 100 program events. Those tags came from the source MIDI file. The old fixture passed them directly as engine owners 0 and 1, although owner 1 means CV in the Rack wrapper. The correction does not alter, delete, reorder, retime or otherwise edit an event.

The separately frozen comparison now has three lanes:

- Historical Legacy preserves the old channel-to-owner mapping and must reproduce the four retained complete WAV hashes.
- Merged Legacy sends all accepted MIDI channels through owner 0 and must equal an independently compiled unchanged b15 engine using that same mapping.
- Original uses the same owner 0 input and the candidate Mode00 allocator. Original-minus-Merged-Legacy therefore isolates allocation; Merged-Legacy-minus-Historical reports the source-policy difference separately.

All 100 voice supports, two previously selected Sine99 supports, four timing scenarios, primary metrics and promotion limits remain fixed before candidate recording renders. V1's source-policy error and v2's optional-diagnostic/reporting fixes are retained as superseded pre-audio designs. V3 changes neither the comparison gates nor the sound model. No new recording scores existed when this note was written.

These are constructed CPU-command observations, not a full boot, observed serial delivery, chip phase reset or measured service cadence. The real recording's receive filters and MIDI arrival times remain unknown. Normal plugin MIDI and CV inputs still need independent ownership; the shared original MIDI bitmap does not justify merging those two host inputs.
