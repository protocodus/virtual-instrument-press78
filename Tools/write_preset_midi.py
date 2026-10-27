#!/usr/bin/env python3
"""Write the committed voice demo phrases, Docs/audio/midi/<NNN>-<slug>.mid.

Eight of the 100 factory voices, each from a different family (README G3,
G3a), with a phrase written for what that voice imitates: the piano plays
chords under a melody, the organ holds voicings, brass and reeds play single
lines in their own range with the mod wheel adding vibrato, the guitar bends,
the bass slaps, bells ring out and the chorus sings. NNN is the program
number. The .mid files are the committed sources the
demo renderer reads; this script records how they were written. Re-run it
only to change a phrase on purpose, and commit the changed .mid files on
their own:

    python3 Tools/write_preset_midi.py Docs/audio/midi
    python3 Tools/write_preset_midi.py --check   # the committed files match

Every file is format 0 on MIDI channel 1 at 480 PPQ, with a tempo and a track
name, and its last event falls 5.5-9.5 s in, so the renderer's 2.5 s release
tail keeps every demo within 8-12 s (G3c).
Notes use the PSS-780's 12-voice limit as the ceiling on simultaneous notes.
"""
import argparse
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
MIDI_DIR = ROOT / "Docs/audio/midi"
BANK = ROOT / "Source/DSP/FactoryVoices.h"
PPQ = 480
NAMES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def n(name: str) -> int:
    """'C4' is MIDI 60; sharps as 'F#3', flats as 'Bb2'."""
    pitch = NAMES[name[0]]
    rest = name[1:]
    if rest[0] == "#":
        pitch, rest = pitch + 1, rest[1:]
    elif rest[0] == "b":
        pitch, rest = pitch - 1, rest[1:]
    return 12 * (int(rest) + 1) + pitch


def notes(text: str):
    """'C4 E4 - G4' as pitches; '-' is a rest."""
    return [None if word == "-" else n(word) for word in text.split()]


class Phrase:
    def __init__(self, bpm: float):
        self.bpm = bpm
        self.events = []  # (beat, order, bytes); note-offs sort before note-ons

    def note(self, beat, length, pitch, velocity=96):
        pitch = n(pitch) if isinstance(pitch, str) else pitch
        self.events.append((beat, 1, bytes([0x90, pitch, velocity])))
        self.events.append((beat + length, 0, bytes([0x80, pitch, 64])))

    def chord(self, beat, length, pitches, velocity=90, spread=0.0):
        """spread staggers the notes, low to high, as a strum or a rolled chord."""
        for index, pitch in enumerate(pitches):
            self.note(beat + index * spread, length - index * spread, pitch, velocity)

    def line(self, beat, step, pitches, velocity=96, gate=0.9, accents=()):
        """Equal steps; None rests."""
        for index, pitch in enumerate(pitches):
            if pitch is not None:
                accent = 20 if index in accents else 0
                self.note(beat + index * step, step * gate, pitch, min(127, velocity + accent))

    def cc(self, beat, controller, value):
        self.events.append((beat, 2, bytes([0xB0, controller, value])))

    def ramp_cc(self, beat, length, controller, start, end, steps=24):
        for step in range(steps + 1):
            fraction = step / steps
            self.cc(beat + length * fraction, controller, round(start + (end - start) * fraction))

    def bend(self, beat, value):
        """value -1..+1 of the bend range (the plug-in's default is 2 semitones)."""
        raw = max(0, min(16383, round(8192 + value * 8191)))
        self.events.append((beat, 2, bytes([0xE0, raw & 0x7F, raw >> 7])))

    def ramp_bend(self, beat, length, start, end, steps=16):
        for step in range(steps + 1):
            fraction = step / steps
            self.bend(beat + length * fraction, start + (end - start) * fraction)

    def seconds(self) -> float:
        return max(beat for beat, _, _ in self.events) * 60 / self.bpm

    def smf(self, name: str) -> bytes:
        def vlq(value):
            out = [value & 0x7F]
            value >>= 7
            while value:
                out.append(0x80 | (value & 0x7F))
                value >>= 7
            return bytes(reversed(out))

        tempo = round(60_000_000 / self.bpm)
        track = bytearray()
        track += b"\x00\xff\x03" + vlq(len(name)) + name.encode("ascii")
        track += b"\x00\xff\x51\x03" + tempo.to_bytes(3, "big")
        last = 0
        for beat, _, message in sorted(self.events, key=lambda e: (e[0], e[1], e[2])):
            tick = round(beat * PPQ)
            track += vlq(tick - last) + message
            last = tick
        track += b"\x00\xff\x2f\x00"
        return (b"MThd" + struct.pack(">IHHH", 6, 0, 1, PPQ)
                + b"MTrk" + struct.pack(">I", len(track)) + track)


def transpose(pitches, semitones):
    return [None if p is None else p + semitones for p in pitches]


# --- Families ----------------------------------------------------------------
# Each takes the octave shift that puts the phrase in the voice's own range.

def piano(shift=0, bpm=92):
    """Left-hand chords under a right-hand melody, with the sustain pedal."""
    p = Phrase(bpm)
    chords = [["C3", "G3", "E4"], ["A2", "E3", "C4"], ["F2", "C3", "A3"], ["G2", "D3", "B3"]]
    melody = notes("E5 D5 C5 D5 E5 E5 E5 - D5 C5 D5 B4 C5 - - -")
    for bar, chord in enumerate(chords):
        p.cc(bar * 4, 64, 127)
        p.chord(bar * 4, 3.9, transpose([n(x) for x in chord], shift), 70)
        p.cc(bar * 4 + 3.95, 64, 0)
    p.line(0, 1, transpose(melody, shift), 92, gate=0.85, accents=(0, 8, 16, 24))
    return p


def organ(shift=0, bpm=84, vibrato=True):
    """Held voicings with a moving top line; the wheel brings in vibrato."""
    p = Phrase(bpm)
    voicings = [["C3", "G3", "C4", "E4"], ["F3", "A3", "C4", "F4"], ["G3", "B3", "D4", "G4"],
                ["A3", "C4", "E4", "A4"], ["F3", "A3", "D4", "F4"], ["G3", "B3", "D4", "G4"],
                ["C3", "G3", "C4", "E4"]]
    beats = [2, 2, 2, 2, 2, 2, 4]
    beat = 0
    for voicing, length in zip(voicings, beats):
        p.chord(beat, length + 0.05, transpose([n(x) for x in voicing], shift), 88)
        beat += length
    p.line(0, 1, transpose(notes("G5 E5 F5 A5 G5 B5 A5 C6 A5 F5 B5 G5 C6 - - -"), shift), 84, gate=0.95)
    if vibrato:
        p.ramp_cc(6, 6, 1, 0, 100)
    return p


def bell_melody(shift=0, bpm=72, spacing=1.0):
    """A slow melody left to ring; a few notes overlap their decays."""
    p = Phrase(bpm)
    melody = notes("E5 C5 D5 G4 - G4 D5 E5 C5 - - - E5 G5 A5 G5")
    p.line(0, spacing, transpose(melody, shift), 100, gate=2.5)
    return p


def fanfare(shift=0, bpm=108):
    """A brass call: repeated notes, a leap, a held note with wheel vibrato."""
    p = Phrase(bpm)
    call = notes("G4 G4 G4 C5 - E5 - G5 E5 C5 D5 - G4 - - - "
                 "A4 A4 A4 D5 - F5 - A5 G5 F5 E5 D5 C5 - - -")
    p.line(0, 0.5, transpose(call, shift), 104, gate=0.8, accents=(0, 3, 16, 19))
    p.note(16.5, 4, n("C5") + shift, 110)
    p.ramp_cc(17.5, 3, 1, 0, 90)
    return p


def reed_bend(shift=0, bpm=96):
    """A saxophone-style line with scoops and a fall."""
    p = Phrase(bpm)
    melody = notes("G4 Bb4 C5 D5 - F5 D5 C5 Bb4 G4 - - F4 G4 Bb4 C5 Bb4 G4 - - - - - -")
    p.line(0, 0.5, transpose(melody, shift), 96, gate=0.9, accents=(3, 13))
    for start in (1.0, 6.5):
        p.bend(start - 0.01, -0.5)
        p.ramp_bend(start, 0.25, -0.5, 0.0, steps=6)
    p.note(10, 2, n("D5") + shift, 104)
    p.ramp_cc(10.5, 1.0, 1, 0, 90, steps=8)
    p.ramp_bend(11.5, 0.5, 0.0, -1.0, steps=8)
    p.bend(12.1, 0.0)
    answer = notes("C5 D5 F5 - D5 C5 Bb4 C5 G4 - - -")
    p.line(13, 0.5, transpose(answer, shift), 92, gate=0.9, accents=(2,))
    p.note(18, 2, n("G4") + shift, 96)
    p.ramp_cc(18.5, 1.5, 1, 0, 80, steps=8)
    return p


def lead_guitar(shift=0, bpm=100):
    """A blues lead line with a held bend and release."""
    p = Phrase(bpm)
    lick = notes("A4 C5 D5 Eb5 D5 C5 A4 - G4 A4 C5 - A4 - - -")
    p.line(0, 0.5, transpose(lick, shift), 100, gate=0.85, accents=(0, 3))
    p.note(8, 3, n("D5") + shift, 112)
    p.ramp_bend(8.5, 0.5, 0.0, 1.0, steps=8)
    p.ramp_bend(10, 0.5, 1.0, 0.0, steps=8)
    p.line(12, 0.5, transpose(notes("C5 A4 G4 E4 A4 - - -"), shift), 96, gate=0.9)
    p.ramp_cc(15, 2, 1, 0, 90, steps=8)
    return p


def slap_bass(shift=0, bpm=100):
    """Slapped octaves with dead notes between."""
    p = Phrase(bpm)
    groove = notes("E1 - E2 E1 - G1 A1 - E1 - E2 - D2 - B1 -")
    for bar in range(4):
        p.line(bar * 4, 0.25, transpose(groove, shift), 108, gate=0.4, accents=(2, 10))
    p.note(16, 1.5, n("E1") + shift, 110)
    return p


def choir(shift=0, bpm=66):
    """Slow choral chords with the wheel adding vibrato."""
    p = Phrase(bpm)
    for bar, chord in enumerate([["C3", "G3", "E4", "C5"], ["A2", "E3", "C4", "A4"],
                                 ["F2", "C3", "A3", "F4"], ["G2", "D3", "B3", "G4"]]):
        p.chord(bar * 3, 3.1, [n(x) + shift for x in chord], 86)
    p.ramp_cc(1, 9, 1, 0, 70)
    return p


# Voice number (0-based; the file's <NNN> is one more) -> phrase. Eight of the
# 100 factory voices, each a different family: the FM electric piano, a drawbar
# organ under the wheel, a trumpet call, a saxophone's scoops and fall, a bent
# rock lead, slap bass, tubular bells and a chorus.
PHRASES = {
    2: lambda: piano(bpm=104), 13: lambda: organ(bpm=112), 22: lambda: fanfare(bpm=132),
    32: lambda: reed_bend(bpm=128), 53: lambda: lead_guitar(bpm=110), 62: lambda: slap_bass(bpm=112),
    84: lambda: bell_melody(-12, bpm=112), 92: lambda: choir(bpm=80),
}


def voice_names():
    names = re.findall(r'\{\d+, "([^"]+)", \{\{', BANK.read_text(encoding="utf-8"))
    if len(names) != 100:
        raise SystemExit(f"{BANK}: expected 100 factory voices, found {len(names)}")
    return names


def slug(name: str) -> str:
    # The renderer's slug rule: lowercase alphanumerics, other runs as one '-'.
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def files():
    names = voice_names()
    result = {}
    for index, build in PHRASES.items():
        name = names[index]
        phrase = build()
        seconds = phrase.seconds()
        if not 5.5 <= seconds <= 9.5:
            raise SystemExit(f"{name}: last event at {seconds:.1f} s, outside 5.5-9.5 s")
        sounding = peak = 0
        for _, order, _ in sorted(phrase.events, key=lambda e: (e[0], e[1])):
            sounding += 1 if order == 1 else -1 if order == 0 else 0
            peak = max(peak, sounding)
        if peak > 12:
            raise SystemExit(f"{name}: {peak} notes sound at once, above the 12 voices")
        result[f"{index + 1:03d}-{slug(name)}.mid"] = phrase.smf(slug(name))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("output", type=Path, nargs="?", default=MIDI_DIR)
    parser.add_argument("--check", action="store_true", help="compare with the committed files")
    args = parser.parse_args()
    expected = files()
    if args.check:
        found = {p.name: p.read_bytes() for p in args.output.glob("*.mid")}
        if found != expected:
            stale = sorted(set(found) ^ set(expected) | {k for k in expected if found.get(k) != expected[k]})
            print(f"{args.output} differs from {Path(__file__).name} in: {', '.join(stale[:5])}", file=sys.stderr)
            return 1
        print(f"{len(expected)} demo phrases match {Path(__file__).name}")
        return 0
    args.output.mkdir(parents=True, exist_ok=True)
    for name, data in expected.items():
        (args.output / name).write_bytes(data)
    print(f"wrote {len(expected)} phrases to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
