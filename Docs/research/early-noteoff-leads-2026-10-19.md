# Early note-off behavior: new primary-source leads — 19 October 2026

An original PSS-480 owner reports a sound-changing early-note-off behavior that deserves a controlled test. It is not yet evidence for adding a special envelope-freeze rule to Press78. No DSP or factory patch changes accompany this note.

## Firsthand musical observation

In an [August 2019 post](https://www.reddit.com/r/synthesizers/comments/csa43y/), the composer JakeForReal describes making a soundtrack with a PSS-480. The author reports that releasing a key before the envelopes reach their held stage can make one operator appear to freeze while the other continues. The post also says that hidden parameters differ between factory voices, despite identical front-panel settings.

The author points to two own recordings: [So That's What It Tastes Like](https://jakesmo.bandcamp.com/track/so-thats-what-it-tastes-like), described as using two patches with different results from short and long gates, and the snare-like sound around 1:50 in [Slapstick Is The Only Ethical Comedy](https://jakesmo.bandcamp.com/track/slapstick-is-the-only-ethical-comedy). Their public pages identify the same artist and August 2019 album. They are composed musical demonstrations, not raw-patch/gate measurements. No patch dump, isolated stem, transmitted MIDI log or dry/effect-off comparison was recovered from those pages. No purchase, download checkout or outreach was performed.

This is a primary account of the owner's experience, not a manufacturer algorithm description. In particular, its colloquial held/sustain terminology cannot identify an internal D1/D2 transition or which operator freezes.

## A necessary competing explanation

The documented voice format already has independent RR and SRR values for both operators. Under the **current model**, ordinary release at raw RR0/RKS0 is only 2.828 dB/s, versus 45.255 dB/s at RR4 and 724.077 dB/s at RR8. Over 100 ms the RR0 operator loses only 0.283 dB, which can sound nearly frozen while the other operator changes quickly. Note-off during a slow modulator attack also preserves a very different FM index from note-off after its peak. These are calculations of the existing hypothesis, not measurements of a PSS-480.

Consequently the anecdote is compatible with ordinary asymmetric release parameters as well as a special early-note-off state, performance Reverb/Sustain, or another unknown mechanism. It must not be converted into a production rule that freezes an operator merely because a key was released during attack or D1.

The discriminating fixture is an independently authored raw patch with **known equal nonzero RR/SRR values**, separately chosen slow and instant attacks, D1/D2 settings and fixed early/late gates. Measure each operator's effect through a pure carrier and a controlled modulated sound, with physical Reverb/Sustain independently off/on. An isolated short-gate timbre change alone is insufficient.

## Newly located separate tutorial

The original author Simeon Soden's [2026 PSS-680 tutorial post](https://www.reddit.com/r/MusicGear/comments/1rsl961/) links [a hardware/editor video](https://www.youtube.com/watch?v=eiIw-ffhzXM). Its declared chapters include front-panel editing at 3:25 and advanced editor controls at 15:16. This is a genuinely separate acquisition lead from the previously studied PSS-480 editor demonstration. Its description's reference to MIDI CC does not establish the transport protocol; the exact SysEx/parameter behavior must be checked from the demonstration and editor implementation.

The [separate source audit](soden-pss680-source-audit-2026-10-19.md) records acquisition, visible settings and whether any segment can supply an independent envelope constraint. This lead is not itself a calibration constant or a claim that the hardware's hidden state has been recovered.

## Related material excluded from envelope calibration

The original [Reverb Machine PS-48 product page](https://reverbmachine.com/sounds/ps48-yamaha-pss-480-samples/) describes a sampled PSS-480/580 sound set with adjustable sampler envelopes and built-in effects. Its public musical demos are not raw OPU gate-off fixtures, and the sample product requires purchase. Nothing was bought or treated as an unmodified envelope reference.

The [Furnace Yamaha-chip discussion](https://github.com/tildearrow/furnace/discussions/2203) is a useful chip-identification lead, not a numerical YM3420 envelope implementation or a working reference core. A common portable-FM label does not justify importing OPL timing.

All observations above were reviewed from publicly accessible primary pages on 19 October 2026. The new early-off account supplies a separating test requirement, not a confirmed hardware quirk. These leads do not alter the user's prohibition on artificial noise.
