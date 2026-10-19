# Human Voice 1 release: frozen-core diagnosis

2026-10-18. No production DSP or default parameters were changed. Re-run `python3 build/release-analysis/analyze.py` from the repository root. The probe compiles the current engine and exposes its existing state for observation only; `release-core-report.json` records all relevant source hashes.

**The short release is a model assumption, not an import or allocator failure for the baseline recording.** Native C++ and frozen Python agree on the factory data and current envelope law. The exact keyboard's Reverb performance state is absent from both engines.

## Settings and predictions

Preset93 carrier raw byte14 is `0x07`: D1L0/RR7. Its separate SRR is5, RKS0, AR32, D1R1 and D2R0. The modulator has RR3/SRR1/RKS1. Raw effect byte24 is `0x80`, giving Vibrato on and Sustain off. Enabling Sustain would alter both operators and cannot be equated to Reverb.

The current behavioral law maps effectiveRR=`4*RR+2+keyscale` and release slope to `96/(48*2**(-effectiveRR/4))` dB/s. These numerical laws have not been recovered from the YM3420. They make each one-step reduction in rawRR double release duration:

| Carrier setting | 18dB fall | 60dB fall | Full96dB interval |
|---|---:|---:|---:|
| RR7, unchanged preset |49.718ms|165.728ms|265.165ms|
| RR6, explanatory scenario |99.437ms|331.456ms|530.330ms|
| RR5, explanatory scenario |198.874ms|662.913ms|1060.660ms|

Carrier AR32 completes its attack after about31.25ms. A single D1 step then leaves about0.00004955dB attenuation before the D2 hold. Actual notes74/77 have220.542ms gates, so both are settled before release. The hard cutoff occurs at96dB attenuation, about0.00001585 of full envelope amplitude. Earlier note-offs during attack leave less distance to that cutoff; the72 tests include gates10/30/100/220.542/500/2000ms at notes60/74/77/82 for RR7/6/5. All native/Python completion ticks agree. This verifies the port, not the hardware law.

## Actual performance and tail cleanup

The complete source MIDI/program replay was advanced from frame0 through168s. Program changes snapshot future voices and do not replace a releasing voice's preset. The baseline reaches at most10 active voices during preset93, and none of its voices are stolen.

| Voice | Note-off, source time | Carrier finishes | Explanation |
|---|---:|---:|---|
|74/D5|166.299708s|166.564854s|12728 release ticks; ordinary96dB cutoff|
|77/F5|166.520250s|166.785396s|12728 release ticks; survives program94 at166.740813s|

These state times precede the native engine's nominal32-sample output delay. The analysis WAVs remove that fixed delay. There is no MIDI sustain-pedal event, premature noteOff, tail-duration bound, or oldest-voice cut shortening these baseline notes.

The RR6/RR5 full-performance scenarios do increase voice pressure. With RR5, note82 is stolen at166.299708s, only220.542ms after note-off and at19.961dB attenuation, followed by the engine's1ms stealing fade. This explains the abrupt candidate drop and is not the release equation. Note74 survives until166.740813s in both scenarios,441.104ms after note-off, then is stolen at79.848dB (RR6) or39.924dB (RR5). Thus the reference analysis window150–350ms after note74off is free of this candidate stealing, while later windows are not. Through168s, target-voice steals are0/1/17 for RR7/RR6/RR5. The tested candidate event prefixes were verified against the reference agent's event files: only preset93 carrierRR differs.

## Isolated auditions and next evidence

Six WAVs pair `isolated74-rr7`, `rr6`, and `rr5` with `-raw` or `-recorded`. Each has sample0 at video165.9s, note-on166.079166667s, note-off166.299708333s, and end168s. Same velocity127/master1 throughout; no normalization, limiter, noise, tone, or DC block. Recorded versions add the related PSS480 host48k circuit and frozen RecordedV3 chorus at the source's absolute epoch. The32-sample FM latency is removed without advancing the chorus epoch. Files are finite, unclipped and use the same gain. Raw native/Python audio comparisons are also recorded in the JSON.

These are carrierRR-only explanatory auditions, not adopted hardware corrections. No two-stage release has been inserted. Evidence for a Reverb-dependent envelope mechanism, and the limits of the related TX81Z analogy, are documented in [the research note](reverb-release-evidence.md). The manual distinguishes Reverb from Sustain and recommends Reverb for voices92–94, but supplies no numerical Reverb law. The original PSS780 owner's qualitative description supports investigating this missing state, not selecting a multiplier from the current recording.

The useful next controlled fixture is the same exact-device note/gate with Reverb off/on and Sustain independently off/on, including10/30/100/500/2000ms gates and at least three pitches. Captures should include several seconds after release with no new notes. That separates attack interruption, release slope, any slope-change threshold, key scaling and allocation. Current polyphonic footage cannot uniquely identify those rules.
