# PSS-780 Reverb and Sustain: release evidence

Reviewed 2026-10-18. This note records evidence only; no DSP changes or fitted release constants accompany it. Target 93 (Human Voice 1) was observed with Reverb on and Sustain off in the existing video audit. Those are separate conditions, not interchangeable release settings.

## Yamaha's exact-model documentation

The [PSS-780 owner's manual](https://www.nurykabe.com/dump/docs/PSS/manuals/PSS-780_00.pdf), printed p.9, describes Sustain as extending sound after key release, with voice-dependent duration. Reverb is described by its spacious sound, with voices 92–94 specifically suggested. The page supplies no Reverb envelope law, threshold, delay, or time constant. Effects apply to FM voices rather than PCM drums.

Printed p.41, voice SysEx format 00, documents separate four-bit RR and SRR values for both operators, and separate V/S enable flags. Its envelope sketch shows a longer SRR branch. No field is named Reverb in that voice format; undocumented bits do not establish a hidden Reverb parameter.

Reverb is nevertheless documented performance state. Printed p.42, melody-memory format 01, gives effect-status events with distinct Reverb and Sustain bits alongside Portamento and Vibrato. Printed p.9 says effect settings are stored separately for each melody bank. Thus “not in the voice dump” does not mean “absent from the performance,” nor does it mean a single immutable global setting for every melody bank. These documented interfaces do not specify how Reverb interacts with RR/SRR internally.

## Firsthand observation on the actual PSS-780

CYBERYOGI's [TableHooters PSS-780 review](http://weltenschule.de/TableHooters/Yamaha_PSS-780.html) explicitly attributes its Reverb to modification of the FM envelope. This is an original owner's qualitative account of the exact model, not a Yamaha specification or a measured register-level reconstruction. It supports investigating an envelope effect rather than assuming an audio echo.

The author also says the hardware had not been analyzed. The same page guesses DAC resolution and characterizes chorus as panning; neither description is precise circuit evidence. The Reverb claim therefore does not establish a release multiplier, RR-to-SRR substitution, operator-selection rule, threshold, or exact timing. The original HTTP page was accessible; its HTTPS endpoint had a certificate mismatch, which was not bypassed.

## Related Yamaha mechanism: analogy, not an OPU specification

Yamaha's official [TX81Z owner's manual](https://usa.yamaha.com/files/download/other_assets/9/316769/TX81ZE.pdf), printed p.23 (PDF page 24), documents envelope-based pseudo-reverb. On that instrument, OP1 reaching −18 dB triggers a slower release rate for all operators; the selectable Reverb Rate runs from 1 through 7, and an already slower release is unaffected. OP1's output level and enabled state do not select the trigger. The figure explicitly shows a change in the release slope, rather than repeated audio.

This is an OPZ/TX81Z family precedent, not documentation for the two-operator YM3420 OPU in the PSS-780. In particular, −18 dB and rates 1–7 must not be presented as recovered PSS-780 constants. The differing chip identities are catalogued by the original [Yamaha-chip investigator](https://www.dtech.lv/techarticles_yamaha_chips.html); that catalogue supplies no OPU Reverb algorithm.

## Supported conclusion and remaining uncertainty

A missing Reverb-dependent envelope behavior is a plausible contributor to the longer recorded Human Voice 1 tail. The source evidence does not yet identify that behavior quantitatively or establish that it explains the whole discrepancy. Sustain being off is not evidence that Reverb has no effect. Conversely, the longer tail does not justify enabling SRR, replacing the factory RR, or copying the TX81Z threshold as an established PSS-780 correction.

Useful separating evidence would be matched notes with Reverb/Sustain independently toggled and identical gate durations, including note-offs during attack and after settling. No such controlled exact-device pair was recovered in this bounded pass.

## Local verification provenance

- Existing exact-model scans visually checked: `research/v3-owner-effects-p9.png` and `research/owner-sysex-p41.png` in the frozen historical experiment.
- PSS-780 printed p.42 was rendered from the cached original PDF and visually checked at `build/release-research/pss780-45.png` in this repository.
- Official TX81Z printed p.23 was downloaded, rendered and visually checked at `build/release-research/tx81z-24.png`.
- Original TableHooters HTML/text were retained under `build/release-research/tablehooters-pss780-http.*` for this review; no historical experiment files were modified.
