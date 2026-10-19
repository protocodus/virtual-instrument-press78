#!/usr/bin/env python3
"""Write the committed per-voice demo phrases, Docs/audio/midi/<NNN>-<slug>.mid.

One phrase per factory voice (README G3a), written for what that voice
imitates: pianos play chords under a melody, organs hold voicings, winds and
brass play single lines in their own range with the mod wheel adding
vibrato, guitars strum or bend, basses walk, bells and mallets ring out,
percussion plays its pattern. The .mid files are the committed sources the
demo renderer reads; this script records how they were written. Re-run it
only to change a phrase on purpose, and commit the changed .mid files on
their own:

    python3 Tools/write_preset_midi.py Docs/audio/midi
    python3 Tools/write_preset_midi.py --check   # the committed files match

Every file is format 0 on MIDI channel 1 at 480 PPQ, with a tempo and a track
name, and its last event falls 8-16 s in, before the renderer's release tail.
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


def harpsichord(shift=0, bpm=100):
    """A baroque two-voice line in running eighths."""
    p = Phrase(bpm)
    upper = notes("C5 E5 G5 C6 B5 G5 D5 G5 A5 C6 E6 A5 G5 E5 C5 E5 "
                  "F5 A5 C6 F5 E5 G5 C6 E5 D5 F5 B5 D5 C5 E5 G5 C6")
    lower = notes("C3 - G3 - G2 - B2 - A2 - C3 - E3 - F2 - A2 - C3 - G2 - C3 - - - - -")
    p.line(0, 0.5, transpose(upper, shift), 96, gate=0.8)
    p.line(0, 0.5, transpose(lower, shift), 84, gate=1.6)
    return p


def clavi(shift=0, bpm=104):
    """A syncopated funk riff with ghosted offbeats."""
    p = Phrase(bpm)
    riff = notes("E3 - E3 G3 - A3 - E3 B3 - A3 G3 - E3 - D3")
    for bar in range(5):
        p.line(bar * 4, 0.25, transpose(riff, shift), 96, gate=0.5, accents=(0, 3, 8))
    p.chord(20, 1.5, transpose(notes("E3 G3 B3 D4"), shift), 110)
    return p


def bell_melody(shift=0, bpm=72, spacing=1.0):
    """A slow melody left to ring; a few notes overlap their decays."""
    p = Phrase(bpm)
    melody = notes("E5 C5 D5 G4 - G4 D5 E5 C5 - - - E5 G5 A5 G5")
    p.line(0, spacing, transpose(melody, shift), 100, gate=2.5)
    return p


def accordion(shift=0, bpm=150):
    """A waltz: bass, two chord beats, melody above."""
    p = Phrase(bpm)
    harmony = [("C3", ["E4", "G4", "C5"]), ("G2", ["D4", "G4", "B4"]), ("C3", ["E4", "G4", "C5"]),
               ("F2", ["F4", "A4", "C5"]), ("C3", ["E4", "G4", "C5"]), ("G2", ["D4", "F4", "B4"]),
               ("C3", ["E4", "G4", "C5"]), ("C3", ["E4", "G4", "C5"])]
    for bar, (bass, chord) in enumerate(harmony):
        p.note(bar * 3, 0.9, n(bass) + shift, 84)
        for beat in (1, 2):
            p.chord(bar * 3 + beat, 0.7, [n(x) + shift for x in chord], 70)
    melody = notes("G5 - E5 F5 G5 A5 G5 - D5 E5 - C5 G5 - E5 A5 G5 F5 E5 D5 C5 C5 - -")
    p.line(0, 1, transpose(melody, shift), 96, gate=0.9)
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


def brass_ensemble(shift=0, bpm=96):
    """Sustained brass chords with a swell."""
    p = Phrase(bpm)
    chords = [["C3", "G3", "C4", "E4"], ["Bb2", "F3", "Bb3", "D4"], ["F2", "C3", "F3", "A3"],
              ["G2", "D3", "G3", "B3"], ["C3", "G3", "C4", "E4"]]
    for bar, chord in enumerate(chords):
        length = 4 if bar < 4 else 3
        p.chord(bar * 4, length, [n(x) + shift for x in chord], 80 + 8 * (bar % 2))
    return p


def wind(shift=0, bpm=88):
    """A cantabile single line; the wheel adds vibrato on the long notes."""
    p = Phrase(bpm)
    melody = notes("D5 E5 F5 A5 G5 - F5 E5 D5 - - C5 D5 E5 C5 A4 - - "
                   "D5 F5 A5 C6 Bb5 A5 G5 E5 D5 - - -")
    p.line(0, 0.5, transpose(melody, shift), 92, gate=0.95)
    for start in (2.0, 8.0, 12.5):
        p.ramp_cc(start, 1.5, 1, 0, 80, steps=8)
        p.cc(start + 2.0, 1, 0)
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


def whistle(shift=0, bpm=126):
    """Bright repeated figures, as a whistle or kazoo plays them."""
    p = Phrase(bpm)
    figure = notes("C6 C6 G5 C6 E6 - C6 - D6 D6 B5 D6 G6 - D6 -")
    for bar in range(3):
        p.line(bar * 8, 0.5, transpose(figure, shift), 100, gate=0.6, accents=(0, 4))
    p.note(24, 1.5, n("C6") + shift, 110)
    return p


def strum(shift=0, bpm=96):
    """Down and up strums of open chords."""
    p = Phrase(bpm)
    shapes = [["E2", "B2", "E3", "G#3", "B3", "E4"], ["A2", "E3", "A3", "C#4", "E4"],
              ["D3", "A3", "D4", "F#4"], ["E2", "B2", "E3", "G#3", "B3", "E4"]]
    for bar, shape in enumerate(shapes * 1 + shapes[:1]):
        for beat, (down, velocity) in enumerate([(True, 100), (True, 80), (False, 70), (True, 90)]):
            pitches = [n(x) + shift for x in (shape if down else reversed(shape))]
            p.chord(bar * 4 + beat, 0.95, pitches, velocity, spread=0.02)
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


def bass(shift=0, bpm=104):
    """A walking line under an implied blues."""
    p = Phrase(bpm)
    walk = notes("C2 E2 G2 A2 Bb2 A2 G2 E2 F2 A2 C3 D3 Eb3 D3 C3 A2 "
                 "C2 E2 G2 A2 Bb2 A2 G2 E2 G2 B2 D3 F3 F2 A2 C3 Eb3 C2 - - -")
    p.line(0, 0.5, transpose(walk, shift), 100, gate=0.8, accents=(0, 8, 16, 24, 32))
    return p


def slap_bass(shift=0, bpm=100):
    """Slapped octaves with dead notes between."""
    p = Phrase(bpm)
    groove = notes("E1 - E2 E1 - G1 A1 - E1 - E2 - D2 - B1 -")
    for bar in range(4):
        p.line(bar * 4, 0.25, transpose(groove, shift), 108, gate=0.4, accents=(2, 10))
    p.note(16, 1.5, n("E1") + shift, 110)
    return p


def bowed_bass(shift=0, bpm=60):
    """Long bowed notes, arco."""
    p = Phrase(bpm)
    p.line(0, 2, transpose(notes("C2 G1 A1 E1 F1 G1"), shift), 90, gate=1.0)
    return p


def plucked_folk(shift=0, bpm=112, tremolo=False):
    """Pentatonic picking; tremolo repeats each note as a mandolin does."""
    p = Phrase(bpm)
    tune = notes("D5 E5 G5 A5 G5 E5 D5 B4 A4 B4 D5 E5 D5 B4 A4 G4") * 2
    step = 0.5
    for index, pitch in enumerate(transpose(tune, shift)):
        if tremolo:
            for r in range(4):
                p.note(index * step + r * step / 4, step / 4 * 0.8, pitch, 84 + (r % 2) * 12)
        else:
            p.note(index * step, step * 0.9, pitch, 96)
    p.chord(len(tune) * step, 3, transpose(notes("G3 D4 G4 B4 D5"), shift), 96, spread=0.03)
    if not tremolo:
        p.line(len(tune) * step + 4, step, transpose(tune[::2], shift), 90, gate=0.9)
    return p


def harp(shift=0, bpm=80):
    """Glissandi up and down, then a rolled chord."""
    p = Phrase(bpm)
    scale = [n(x) + shift for x in "C3 D3 E3 G3 A3 C4 D4 E4 G4 A4 C5 D5 E5 G5 A5 C6".split()]
    for index, pitch in enumerate(scale):
        p.note(index * 0.125, 1, pitch, 80 + index)
    for index, pitch in enumerate(reversed(scale)):
        p.note(4 + index * 0.125, 1, pitch, 96 - index)
    p.chord(8, 6, [n(x) + shift for x in "F2 C3 F3 A3 C4 F4 A4".split()], 90, spread=0.12)
    return p


def eastern_pluck(shift=0, bpm=84):
    """A modal line with grace-note slides, as sitar, shamisen or koto play."""
    p = Phrase(bpm)
    line = notes("D4 - E4 F4 A4 - G4 F4 E4 - D4 - A3 - D4 - "
                 "F4 G4 A4 Bb4 A4 - G4 - F4 E4 D4 - - - - -")
    p.line(0, 0.5, transpose(line, shift), 100, gate=0.9, accents=(0, 4, 16))
    for start in (2.0, 9.0):
        p.bend(start - 0.01, -0.5)
        p.ramp_bend(start, 0.3, -0.5, 0.0, steps=6)
    return p


def strings(shift=0, bpm=72, legato_line=True):
    """A legato melody, or sustained section chords."""
    p = Phrase(bpm)
    if legato_line:
        line = notes("A4 B4 C5 E5 D5 C5 B4 G#4 A4 - C5 E5 A5 G5 F5 E5")
        p.line(0, 0.75, transpose(line, shift), 92, gate=1.05)
        p.ramp_cc(3, 8, 1, 0, 70)
    else:
        for bar, chord in enumerate([["A2", "E3", "C4", "A4"], ["F2", "C3", "A3", "F4"],
                                     ["C3", "G3", "E4", "C5"], ["G2", "D3", "B3", "G4"]]):
            p.chord(bar * 3.5, 3.6, [n(x) + shift for x in chord], 84)
    return p


def synth_stabs(shift=0, bpm=118):
    """Short brassy chord stabs on the offbeats, a swell at the end."""
    p = Phrase(bpm)
    for bar in range(5):
        for beat in (0.5, 1.5, 2.75):
            p.chord(bar * 4 + beat, 0.35, [n(x) + shift for x in ["C4", "Eb4", "G4", "Bb4"]], 104)
    p.chord(20, 2.5, [n(x) + shift for x in ["F3", "C4", "Eb4", "A4"]], 96)
    return p


def synth_bass(shift=0, bpm=120):
    """An octave-jumping sequence."""
    p = Phrase(bpm)
    seq = notes("C2 C3 C2 Bb2 C2 G2 C2 Eb2 F1 F2 F1 Eb2 G1 G2 G1 D2")
    for bar in range(3):
        p.line(bar * 4, 0.25, transpose(seq, shift), 104, gate=0.6, accents=(0, 8))
    p.line(12, 0.25, transpose(seq[:8], shift), 104, gate=0.6)
    p.note(14, 2, n("C2") + shift, 110)
    return p


def drum_pattern(pitches, bpm=100, rolls=False):
    """A fill pattern over the given drum pitches; rolls end each phrase."""
    p = Phrase(bpm)
    pattern = [0, None, 0, 1, None, 1, 2, None, 0, 0, 1, None, 2, 1, 0, None]
    for bar in range(4):
        p.line(bar * 4, 0.25, [None if i is None else pitches[i % len(pitches)] for i in pattern],
               100, gate=0.5, accents=(0, 8))
        if rolls:
            for r in range(8):
                p.note(bar * 4 + 3 + r * 0.125, 0.1, pitches[-1], 70 + r * 5)
    p.note(16, 2, pitches[0], 120)
    return p


def steel_drum(shift=0, bpm=100):
    """A calypso melody with double strikes."""
    p = Phrase(bpm)
    tune = notes("C5 C5 E5 G5 - G5 A5 G5 E5 - C5 D5 E5 D5 C5 - "
                 "F5 F5 A5 C6 - A5 G5 E5 D5 - E5 D5 C5 - - -")
    p.line(0, 0.5, transpose(tune, shift), 100, gate=0.5, accents=(0, 3, 16, 19))
    p.chord(16, 2, transpose(notes("C5 E5 G5"), shift), 104)
    return p


def mallets(shift=0, bpm=104, rolls=False):
    """Mallet arpeggios; rolls repeat each held note."""
    p = Phrase(bpm)
    arps = [["C4", "E4", "G4", "C5"], ["A3", "C4", "E4", "A4"], ["F3", "A3", "C4", "F4"], ["G3", "B3", "D4", "G4"]]
    beat = 0.0
    for shape in arps * 2:
        for pitch in shape + list(reversed(shape))[1:3]:
            p.note(beat, 0.5, n(pitch) + shift, 96)
            beat += 0.25 * 1.5
    if rolls:
        for r in range(16):
            p.note(beat + r * 0.125, 0.12, n("C5") + shift, 70 + (r % 4) * 8)
        beat += 2
    p.chord(beat, 3, [n(x) + shift for x in ["C4", "E4", "G4", "C5"]], 104)
    return p


def vibraphone(shift=0, bpm=92):
    """Jazz voicings with the pedal down, then a melody."""
    p = Phrase(bpm)
    for bar, chord in enumerate([["D4", "F4", "A4", "C5"], ["G3", "B3", "D4", "F4"],
                                 ["C4", "E4", "G4", "B4"], ["A3", "C#4", "E4", "G4"]]):
        p.cc(bar * 2, 64, 127)
        p.chord(bar * 2, 1.0, [n(x) + shift for x in chord], 90)
        p.cc(bar * 2 + 1.95, 64, 0)
    p.line(8, 0.5, transpose(notes("A5 F5 D5 C5 B4 D5 G5 F5 E5 - G5 - C6 - - -"), shift), 100, gate=0.7)
    return p


def choir(shift=0, bpm=66):
    """Slow choral chords with the wheel adding vibrato."""
    p = Phrase(bpm)
    for bar, chord in enumerate([["C3", "G3", "E4", "C5"], ["A2", "E3", "C4", "A4"],
                                 ["F2", "C3", "A3", "F4"], ["G2", "D3", "B3", "G4"]]):
        p.chord(bar * 3, 3.1, [n(x) + shift for x in chord], 86)
    p.ramp_cc(1, 9, 1, 0, 70)
    return p


def voice_line(shift=0, bpm=76):
    """A sung single line, phrased with breaths."""
    p = Phrase(bpm)
    line = notes("E4 G4 A4 - A4 C5 B4 A4 G4 - - - E4 G4 A4 B4 C5 D5 E5 - - - - - "
                 "D5 C5 B4 A4 G4 A4 - - E4 - - -")
    p.line(0, 0.5, transpose(line, shift), 90, gate=0.98)
    p.ramp_cc(4, 2, 1, 0, 80, steps=8)
    p.cc(6.1, 1, 0)
    return p


def ice_block(shift=0, bpm=100):
    """Sparse knocks in a broken rhythm."""
    p = Phrase(bpm)
    hits = notes("C5 - - G4 - C5 - - E5 - D5 - - C5 G4 -")
    for bar in range(4):
        p.line(bar * 4, 0.25, transpose(hits, shift + (bar % 2) * 2), 104, gate=0.4)
    p.note(16, 1, n("C5") + shift, 120)
    return p


def musical_saw(shift=0, bpm=60):
    """Long notes joined by slow pitch glides and deep wheel vibrato."""
    p = Phrase(bpm)
    for index, pitch in enumerate(notes("E5 C5 G5 E5")):
        p.note(index * 2.5, 2.4, pitch + shift, 90)
        p.ramp_bend(index * 2.5 + 1.8, 0.6, 0.0, 0.5 if index % 2 == 0 else -0.5, steps=8)
        p.bend(index * 2.5 + 2.45, 0.0)
    p.ramp_cc(0.5, 4, 1, 0, 110)
    return p


def music_box(shift=0, bpm=96):
    """A high, quick lullaby figure."""
    p = Phrase(bpm)
    tune = notes("E6 D6 C6 D6 E6 E6 E6 - D6 D6 D6 - E6 G6 G6 - "
                 "E6 D6 C6 D6 E6 E6 E6 E6 D6 D6 E6 D6 C6 - - -")
    p.line(0, 0.5, transpose(tune, shift), 96, gate=0.4)
    p.line(0, 2, transpose(notes("C4 G3 F3 G3 C4 G3 G3 C4"), shift + 12), 70, gate=0.3)
    return p


def sine(shift=0, bpm=80):
    """Pure tones: an octave sweep of single notes, then a held interval with vibrato."""
    p = Phrase(bpm)
    p.line(0, 0.5, transpose(notes("C3 G3 C4 G4 C5 G5 C6 G5 C5 G4 C4 G3"), shift), 90, gate=0.9)
    p.chord(6.5, 5, [n("C4") + shift, n("G4") + shift], 90)
    p.ramp_cc(8, 3, 1, 0, 110)
    return p


# Voice number -> phrase, in bank order (Source/DSP/FactoryVoices.h names them).
PHRASES = {
    0: lambda: piano(), 1: lambda: piano(), 2: lambda: piano(bpm=84), 3: lambda: piano(bpm=84),
    4: lambda: piano(bpm=112), 5: lambda: piano(12, bpm=108),
    6: lambda: organ(), 7: lambda: organ(-12, bpm=72, vibrato=False), 8: lambda: organ(-12, bpm=72, vibrato=False),
    9: lambda: organ(bpm=72, vibrato=False), 10: lambda: organ(bpm=96), 11: lambda: organ(bpm=104),
    12: lambda: organ(bpm=88), 13: lambda: organ(bpm=112), 14: lambda: accordion(bpm=168),
    15: lambda: harpsichord(), 16: lambda: harpsichord(bpm=92), 17: lambda: clavi(),
    18: lambda: bell_melody(12, bpm=96), 19: lambda: bell_melody(12, bpm=88),
    20: lambda: accordion(), 21: lambda: accordion(bpm=132),
    22: lambda: fanfare(), 23: lambda: fanfare(bpm=96), 24: lambda: reed_bend(), 25: lambda: fanfare(bpm=116),
    26: lambda: fanfare(-12, bpm=88), 27: lambda: fanfare(-12, bpm=84), 28: lambda: fanfare(-12, bpm=96),
    29: lambda: fanfare(-24, bpm=84), 30: lambda: brass_ensemble(),
    31: lambda: wind(), 32: lambda: reed_bend(), 33: lambda: reed_bend(-12), 34: lambda: wind(-12),
    35: lambda: wind(-24, bpm=80), 36: lambda: wind(), 37: lambda: wind(-24, bpm=84), 38: lambda: whistle(),
    39: lambda: wind(), 40: lambda: wind(bpm=76), 41: lambda: wind(bpm=96), 42: lambda: wind(bpm=80),
    43: lambda: brass_ensemble(12, bpm=88), 44: lambda: wind(-12, bpm=100), 45: lambda: reed_bend(),
    46: lambda: bass(12, bpm=96), 47: lambda: whistle(-12, bpm=116), 48: lambda: whistle(bpm=140),
    49: lambda: strum(), 50: lambda: plucked_folk(-12, bpm=108), 51: lambda: eastern_pluck(),
    52: lambda: vibraphone(-12, bpm=96), 53: lambda: lead_guitar(), 54: lambda: lead_guitar(bpm=112),
    55: lambda: lead_guitar(-12, bpm=96), 56: lambda: musical_saw(-12), 57: lambda: strum(bpm=84),
    58: lambda: strum(bpm=104),
    59: lambda: bass(), 60: lambda: bass(bpm=96), 61: lambda: bass(bpm=112), 62: lambda: slap_bass(),
    63: lambda: bass(bpm=92), 64: lambda: bass(bpm=100), 65: lambda: bowed_bass(),
    66: lambda: plucked_folk(bpm=128), 67: lambda: strum(12, bpm=112), 68: lambda: plucked_folk(tremolo=True),
    69: lambda: harp(), 70: lambda: eastern_pluck(), 71: lambda: eastern_pluck(bpm=96),
    72: lambda: eastern_pluck(bpm=90), 73: lambda: eastern_pluck(12, bpm=78),
    74: lambda: strings(12), 75: lambda: strings(12, bpm=80), 76: lambda: strings(-12, bpm=66),
    77: lambda: strings(legato_line=False),
    78: lambda: synth_stabs(), 79: lambda: synth_bass(),
    80: lambda: drum_pattern([n("A2"), n("E2"), n("C2")], bpm=104),
    81: lambda: bell_melody(), 82: lambda: bell_melody(12), 83: lambda: bell_melody(bpm=80),
    84: lambda: bell_melody(-12, bpm=66), 85: lambda: drum_pattern([n("C2"), n("G1"), n("F1")], bpm=88, rolls=True),
    86: lambda: steel_drum(), 87: lambda: steel_drum(bpm=108), 88: lambda: mallets(12),
    89: lambda: mallets(), 90: lambda: mallets(rolls=True), 91: lambda: vibraphone(),
    92: lambda: choir(), 93: lambda: voice_line(), 94: lambda: voice_line(bpm=70), 95: lambda: whistle(bpm=112),
    96: lambda: ice_block(), 97: lambda: musical_saw(), 98: lambda: music_box(), 99: lambda: sine(),
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
    if sorted(PHRASES) != list(range(len(names))):
        raise SystemExit("PHRASES must give every factory voice one phrase")
    result = {}
    for index, name in enumerate(names):
        phrase = PHRASES[index]()
        seconds = phrase.seconds()
        if not 8.0 <= seconds <= 16.0:
            raise SystemExit(f"{name}: last event at {seconds:.1f} s, outside 8-16 s")
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
