# Optional PSS-780 envelope capture protocol — 18 October 2026

This kit prepares the controlled recordings missing from the current hardware evidence. It generates files only: no MIDI port is opened, nothing is played, and no hardware or runtime state is changed. Its measurements have not been performed.

**If deliberately played on a PSS-780, these MIDI files repeatedly replace DIGITAL SYNTHESIZER user bank5 (raw bank4) with temporary calibration voices, then select program104 on MIDI channel1. Back up the user voice banks and current setup before routing or playing a file. Bank5 must be restored from that backup afterwards.** Importing a file into a DAW should not automatically route it to hardware.

## Manufacturer verification

The original Yamaha [PSS-780 operating manual](https://www.nurykabe.com/dump/docs/PSS/manuals/PSS-780_00.pdf) was visually checked, including its printed pp35,41 and46. The reviewed scan's SHA-256 is recorded in the JSON.

Printed p41 specifies raw banks0–4 for user banks1–5, a33-byte voice represented as66 transmitted nibbles with the high nibble first, and the7-bit two's-complement data checksum. The generated wire message is72 bytes: `F0 43 76 00`,66 nibbles, checksum, `F7`.

Printed pp35/46 map program bytes100–104 to banks1–5 on channels1–15. Mode99 recognizes note velocity, pitch bend, CC1 Vibrato and CC64 Sustain. Its physical Reverb/Chorus controls remain available. CC123 is not recognized; none is emitted. No documented MIDI Reverb controller was found, so Reverb is a physical setup condition.

This deliberately uses Mode99. Physical Sustain switching is not relied upon there: the same dry patch defaults to Sustain off, and the selected file sends documented CC64 after every program change.

## Generated files

Run from the repository:

```sh
python3 Tools/generate_hardware_capture.py \
  --output build/hardware-capture-kit-20261018 \
  --protocol-json Docs/research/hardware-capture-protocol-2026-10-18.json
python3 Tools/generate_hardware_capture.py \
  --output build/hardware-capture-kit-20261018 --validate-only
```

The generated directory is ignored by Git. It contains six SMF0 MIDI files, `cases.json`, `cases.csv`, a separately decoded `events.csv`, `protocol.json`, `validation.json`, a recording-metadata template and an operator README. The33-byte calibration voices are independently constructed; no factory bank is imported or copied.

| File | Duration | Cases | Physical Reverb | CC64 Sustain |
|---|---:|---:|---|---|
| `00_gain_check.mid` | 14 s | 1 | Off | Off |
| `01_calibration_dry.mid` | 255 s | 35 | Off | Off |
| `10_release_reverb_off_sustain_off.mid` | 54.5 s | 6 | Off | Off |
| `11_release_reverb_on_sustain_off.mid` | 54.5 s | 6 | On | Off |
| `12_release_reverb_off_sustain_on.mid` | 54.5 s | 6 | Off | On |
| `13_release_reverb_on_sustain_on.mid` | 54.5 s | 6 | On | On |

Every test uses C4/MIDI60, velocity127, carrier ratio1/sine, RKS0, flat level scaling, no detuning, feedback, pitch/amplitude modulation or Vibrato. The modulator has minimum level and AR0. Raw don't-care fields are zero. The SMF has1000 PPQ at1000000 microseconds per quarter note, giving exact intended millisecond times. Each case waits1 second after its voice write before note-on. All notes have explicit note-offs; no transport, clock or unsupported reset message is sent.

The dry sequence has:

- Seven nonmonotonic static carrier-TL holds: raw0,12,24,36,48,24,0. Repeats expose gain-history changes. A0.75 dB/raw-code law is **not** asserted as an OPU specification.
- AR0,20,24,28,32,36,41,48,63, including the deliberate AR0 silence control.
- D2R12,16,20,24,28,32 with9-second gates.
- D1R12,20,28 towards raw D1L8, with D2R0 and10-second gates.
- D1R0/raw-D1L0 versus1, both with D2R20, to distinguish bypass from an indefinite peak hold.
- RR4,5,6,7,8,10,12,15 following a settled1-second hold, with1–8 seconds of post-note-off observation.

The four matched effect files repeat six simple release probes: AR32 or63, gates30/220/2000 ms, D1R1/D1L0/D2R0, RR7/SRR5. These are a pure-carrier interaction fixture, not a Human Voice1 preset recreation. Their33 raw patch bytes and gates are identical between files. Only documented Sustain messages and the required physical Reverb setup differ.

## Capture and interpretation

Use AUX L/R into two line inputs, recording stereo48 kHz24-bit PCM WAV. Deliberately use the highest-level gain-check file to set unclipped interface/master gain; then keep both fixed. Disable AGC, normalization, compressor, limiter, gate, denoise, EQ, external effects, resampling, time stretching and pitch correction. Record the actual software settings, supply, tuning, modifications, routing and physical effect LEDs in the metadata template. Chorus stays off. No effect changes should occur within a file.

File gates are intended event times, not measured hardware-arrival times. A MIDI loopback capture alongside the audio is useful if available. Embedded SysEx/program messages must survive the chosen player; observe the actual device state rather than assuming successful routing.

Post-note-off silences are finite observation windows. If energy remains at the next patch write, that write censors the tail; it does not prove the envelope completed. Preserve the recording and mark the case accordingly. Generate a **separate** longer follow-up kit with `--tail-scale 2` or greater to extend all tail windows without changing gates. No particular envelope cutoff, decay time or Reverb mechanism is assumed.

This separates the unresolved questions in the recording audit: capture transfer/gain history, attack shape, D1/D2 rates, release rates, zero-distance D1 behavior, and the distinct effects of Reverb and Sustain. It cannot supply those answers until an actual instrument is recorded.

## Validation scope

The generator independently reads its emitted SMF byte stream and Yamaha payloads. It checks header/track lengths, tempo, one-bank addressing, payload nibble order, checksum, program destination, permitted controllers, matched note-offs, intended gates, sweep coverage and identical effect-pair patches. It reads the CSV back against the case manifest. Negative witnesses reject malformed/checksum-invalid SysEx, an incorrect bank, truncated SMF, a wrong program, a mismatched note-off and an incorrect Sustain condition.

These checks establish file syntax and the intended capture schedule. They are not evidence that a keyboard received a message, that a recording is dry, or that the model matches hardware.
