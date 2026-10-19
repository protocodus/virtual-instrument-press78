# Soden / ako PSS-680 source audit — 2026-10-19

This is a useful independent owner's demonstration with readable editor settings, but it does not supply a defensible new numeric envelope, detune, TL or feedback calibration in this pass. The strongest new procedural fact is that the linked PSS-680 editor sends complete voice SysEx and Program Changes, and includes a one-second auto-put timer. A visible control edit is therefore not a measured hardware parameter-arrival time, and an interruption during editing is not automatically a normal key release.

No DSP, presets, host state, packages or production constants changed. No artificial noise, MIDI transmission, outreach or purchases were introduced. All third-party media remains in ignored local analysis storage. The [JSON audit](soden-pss680-source-audit-20261019.json) preserves sanitized metadata, four complete editor snapshots, conditional raw-byte mappings, rejected opportunities and 411 artifact hashes.

## Source and acquisition

The [YouTube tutorial](https://www.youtube.com/watch?v=eiIw-ffhzXM) is uploaded by **ako**, channel `UC28-rz0VLwyvHsIMFGxFu1A`, with metadata publication date **2026-03-13** and duration **1765 seconds / 29:25**. The [author's own Reddit post](https://www.reddit.com/r/MusicGear/comments/1rsl961/) under `simeonsoden` links the tutorial and its chapters. This is a 2026 demonstration, separate from the 2019 owner anecdote discussed in the [early-noteoff leads](early-noteoff-leads-20261019.md).

The advanced chapter spans original source **916–1274 seconds / 15:16–21:14**. The front-panel section begins at 205 seconds. Later lead, composed PSS-480 music and factory-song examples are not treated as calibration fixtures.

Ordinary public `yt-dlp` access acquired the original metadata/captions, format-137 1920×1080/30 fps video and format-251 Opus audio. No accounts, cookies, authentication or access bypass were used. Audio for 916–1274 seconds was decoded to stereo float32 at 48 kHz; the origin is the requested full-source decode time, not a stream-copy filename with unknown preroll. The raw downloader metadata remains ignored because it can contain signed media URLs; tracked JSON contains only selected public fields and hashes.

All 358 one-second frame samples covering 916–1273 seconds were reviewed in coverage sheets. Readable overlays and the parameter changes around 1039–1182 seconds were inspected at original resolution, with another overlay at 1231–1239 seconds. One-second scene coverage cannot guarantee that every short intermediate knob value was captured. It establishes the chapter's procedure and readable opportunities; no hardware gates are recovered from it.

## Visible settings

The numbers below are **editor displays**, not captured hardware SysEx. Each snapshot is an actual source-frame reading. The highlighted preset is a starting-point label: later edits mean it is not an unmodified factory patch. The independent reviewer separately confirmed the 1120- and 1180-second readings.

| Source time | Highlight | Feedback / PMS / AMS / Vibrato delay | Vibrato / Sustain |
| --- | --- | --- | --- |
| 1040 s / 17:20 | 28 Tremolo Organ | 0 / 3 / 0 / 0 | Off / Off |
| 1120 s / 18:40 | 31 Accordion | 0 / 2 / 0 / 45 | On / Off |
| 1180 s / 19:40 | 31 Accordion, edited | 3 / 2 / 0 / 45 | On / Off |
| 1235 s / 20:35 | 31 Accordion, edited | 3 / 2 / 0 / 45 | On / Off |

Modulator values:

| Time | Mult / coarse / fine | AR / D1R / D2R / D1L | RR / SRR / RKS | LKS low / high | Level | Wave / AM |
| --- | --- | --- | --- | --- | ---: | --- |
| 1040 | 1 / 0 / +5 | 60 / 31 / 0 / 13 | 8 / 2 / 1 | 5 / 7 | 75 | Square sine / Off |
| 1120 | 2 / 0 / 0 | 47 / 18 / 0 / 15 | 5 / 2 / 1 | 1 / 4 | 64 | Sine / Off |
| 1180 | 8 / +600ct / −7 | 31 / 36 / 0 / 15 | 5 / 2 / 1 | 1 / 4 | 64 | Half sine / On |
| 1235 | 8 / +600ct / −7 | 31 / 36 / 30 / 15 | 5 / 2 / 1 | 1 / 4 | 70 | Half sine / On |

Carrier values:

| Time | Mult / coarse / fine | AR / D1R / D2R / D1L | RR / SRR / RKS | LKS low / high | Level | Wave / AM |
| --- | --- | --- | --- | --- | ---: | --- |
| 1040 | 1 / 0 / −3 | 60 / 1 / 0 / 15 | 11 / 5 / 0 | 9 / 5 | 83 | Sine / Off |
| 1120 | 1 / 0 / 0 | 37 / 16 / 0 / 15 | 8 / 5 / 0 | 9 / 11 | 87 | Sine / Off |
| 1180 | 7 / 0 / 0 | 37 / 16 / 0 / 15 | 8 / 5 / 0 | 9 / 11 | 87 | Half sine / On |
| 1235 | 7 / 0 / 0 | 37 / 16 / 0 / 15 | 8 / 5 / 0 | 9 / 11 | 87 | Half sine / On |

The [panel author's download](https://ctrlr.martintarenskeen.nl/yamaha-pss680-20220225.bpanelz), version 20220225, corroborates the UI-to-data mapping. Its level display converts to `TL = max(99 − display, 0)` and D1L to `15 − display`; rate fields encode directly. Thus carrier Level87 represents TL12, and D1L15 represents raw attenuation code0. Coarse `+600ct` is the panel's label for its DT2 choice; fine is a signed code, not a measured cents or hertz increment. The JSON gives individual derived fields, not an invented complete transmitted patch. Actual video binary identity and actual delivered bytes are not recovered.

## Transport and timing caveat

The video calls the advanced route “MIDI CC.” The [linked author's PSS-680 panel](https://ctrlr.martintarenskeen.nl/) instead builds 72-byte SysEx voice messages with prefix `F0 43 76 00`, nibble encoding, checksum and `F7` terminator. Its put routine follows the dump with two Program Changes selecting the user bank. Auto-put routines contain 1000 ms timers; duplicate definitions exist in the downloaded source. These are source-code facts, not measurements of the video's exact executable, delivered latency or held-note behavior.

Consequently, screen edits, bank delivery, program selection and physical key events cannot be equated. A complete single-voice dump or its following Program Changes could affect sounding voices; that possibility was not measured for this video. The source does not establish direct ordinary-CC control of the individual operator fields, nor demonstrate that every on-screen change reaches hardware immediately. No MIDI wire recording was supplied.

## Physical effects and recording chain

The preceding physical-panel frame at **915 seconds** shows the effect-indicator positions appearing unlit, including Reverb and Stereo Chorus. The earlier front-panel demonstration explicitly visits Sustain, Reverb, Portamento and Chorus around 837–884 seconds. This is useful visible context, but the camera/setup cut into the advanced chapter prevents using the 915-second frame as continuous proof of a dry advanced recording.

At 1120, 1180 and 1235 seconds the editor shows Vibrato on and Sustain off. Physical Reverb, Portamento, Chorus and Duet states are not jointly visible with the readable editor in the candidate audio windows. Their advanced-chapter state therefore remains unknown. Ableton and studio equipment are visible; no unprocessed-line, constant-gain, no-compressor or no-gate recording guarantee was established.

## Opportunities inspected and rejected

| Candidate | What can be recovered | Why it is not a numeric calibration |
| --- | --- | --- |
| Carrier RR11 at 1040 s versus RR8 at 1120 s | Clearly visible different rates with RKS0 | Different patches, nonzero modulation, AR/LKS/level changes, unknown gates and physical effect bridge. |
| Vibrato delay edits around 1113–1118 s | Display25, then55, then45; qualitative delayed modulation | Key-on timing and settled single-note reference absent; editor delivery has its own timer. |
| Modulator coarse/fine edits around 1129–1133 s | Display0 to+600ct and fine to−7 | Changes overlap and played pitch is not documented. Audio includes several component groups; UI timing is not delivered timing. |
| Carrier multiplier1→9→7 around 1133–1136 s | Readable rapid edits | Notes/gaps and delivery change concurrently; a fixed exploratory 1133.7–1134.0 s window is effectively silent. |
| Feedback0→3 around 1172–1173 s | Readable feedback change | Nearby waveform, AM and modulator AR edits; no equal-level, same-note before/after fixture. |
| Modulator D2R30 at 1235 s | Conditional known-setting example | Two half-sine operators, feedback3, changing modulation and unknown gates; output amplitude is not the modulator envelope. |
| TL/compression response | Several displayed levels across edited patches | No static carrier-TL sweep with everything else held constant. |
| Early-noteoff freeze | No documented fixed-patch long/short-gate pair found | Actual note-off, parameter delivery and global states are not known; unrelated owner anecdotes cannot fill these gaps. |

A small fixed-window spectral inventory was used only to assess whether the tuning edits formed a simple same-pitch fixture. It did not recover a uniquely identified carrier/modulator pair or physical note. Its spectra and declared windows remain in JSON, explicitly exploratory. No detune ratio, oscillator multiplier law or envelope slope is inferred from them.

The chapter provides useful qualitative demonstrations and exact visible settings, including an independently recorded RR8/RKS0 edited patch. It does not isolate that carrier from the modulator or capture enough timing/transport information to make it a new hardware-rate fixture. The appropriate result is to retain the source and rejected opportunities, rather than tune production constants to an underconstrained passage.
