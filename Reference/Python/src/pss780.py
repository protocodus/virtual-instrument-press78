"""Reproducible PSS-780 *behavioral* FM experiment, not a YM3420 die emulator.

Documented voice data is decoded exactly. Transfer laws in MODEL_DEFAULTS are
explicit, adjustable hypotheses: see research/digital-model.md. No Yamaha ROM,
OPLL implementation, or third-party synthesis code is embedded here.
"""
from __future__ import annotations

from copy import deepcopy
from bisect import bisect_right
import json
import math
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
from scipy.signal import resample_poly
try:
    from numba import njit
except ImportError:
    def njit(*args, **kwargs):
        return lambda f: f


MODEL_VERSION = "v3-program-performance"
MODEL_DEFAULTS = {
    "internal_sample_rate": 48000,  # Simulation hypothesis, NOT recovered OPU rate.
    "attack_seconds_at_rate_zero": 8.0,
    "decay_seconds_96db_at_rate_zero": 48.0,
    "rate_steps_per_halving": 4.0,
    "tl_db_per_step": 0.75,
    "d1l_db_per_step": 3.0,
    "modulation_index_max": 8.0 * math.pi,
    "feedback_max_radians": 4.0 * math.pi,
    "fine_detune_cents_per_step": 1.5,
    "lks_db_per_semitone_step": 0.0625,
    "vibrato_hz": 6.1,
    "vibrato_delay_seconds_per_step": 0.01,
    "lfo_waveform": 0,  # 0 sine (v2); 1 triangle (related-hardware hypothesis).
    "lfo_global_phase": False,  # Program renderer can share one clock.
    "lfo_time_offset_seconds": 0.0,
    "velocity_amplitude_exponent": 1.0,
    "velocity_modulation_exponent": 0.0,
    "phase_bits": 0,  # Disabled: internal precision is not established.
    "output_bits": 0,  # Disabled: DAC encoding is not established.
    "squared_sine_signed": True,
    "gain": 0.8,
}


def read_sysex(message: bytes, name: str = "Imported voice") -> dict:
    """Read one 72-byte F0 43 76 00 voice with strict nibble/checksum checks.

    Reserved bits survive in raw_data and write_sysex() round trips them.
    """
    b = bytes(message)
    if len(b) != 72 or b[:4] != b"\xf0\x43\x76\x00" or b[-1] != 0xF7:
        raise ValueError("Expected one 72-byte Yamaha PSS-x80 FM voice SysEx")
    if any(x > 15 for x in b[4:70]):
        raise ValueError("Voice payload must consist of 66 four-bit nibbles")
    if b[70] > 127 or (sum(b[4:70]) + b[70]) % 128:
        raise ValueError("Invalid Yamaha voice checksum")
    raw = [(b[i] << 4) | b[i + 1] for i in range(4, 70, 2)]
    patch = {"name": name, "bank": raw[0], "raw_data": raw}
    for key, k in (("modulator", 0), ("carrier", 1)):
        dt = raw[1 + k] >> 4
        patch[key] = {
            "mul": raw[1 + k] & 15,
            "dt1": -(dt & 7) if dt & 8 else dt & 7,
            "tl": raw[3 + k] & 127,
            "lks_hi": raw[5 + k] >> 4,
            "lks_lo": raw[5 + k] & 15,
            "rks": raw[7 + k] >> 6,
            "ar": raw[7 + k] & 63,
            "am_enable": raw[9 + k] >> 7,
            "dt2": (raw[9 + k] >> 6) & 1,
            "d1r": raw[9 + k] & 63,
            "wave": raw[11 + k] >> 6,
            "d2r": raw[11 + k] & 63,
            "d1l": raw[13 + k] >> 4,
            "rr": raw[13 + k] & 15,
            "srr": raw[20 + k] & 15,
        }
    patch.update(feedback=(raw[15] >> 3) & 7, pms=(raw[16] >> 4) & 7,
                 ams=raw[16] & 3, vibrato_delay=raw[22] & 127,
                 vibrato=bool(raw[24] & 128), sustain=bool(raw[24] & 64))
    return patch


def _integer(value, low, high, name):
    if isinstance(value, (bool, np.bool_)):
        value = int(value)
    if not isinstance(value, (int, np.integer)) or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return int(value)


def validate_patch(patch: Mapping) -> None:
    limits = {"mul": (0, 15), "dt1": (-7, 7), "tl": (0, 127),
              "lks_hi": (0, 15), "lks_lo": (0, 15), "rks": (0, 3),
              "ar": (0, 63), "am_enable": (0, 1), "dt2": (0, 1),
              "d1r": (0, 63), "wave": (0, 3), "d2r": (0, 63),
              "d1l": (0, 15), "rr": (0, 15), "srr": (0, 15)}
    for op in ("modulator", "carrier"):
        for field, (low, high) in limits.items():
            _integer(patch[op][field], low, high, f"{op}.{field}")
    for field, high in (("feedback", 7), ("pms", 7), ("ams", 3),
                        ("vibrato_delay", 127)):
        _integer(patch[field], 0, high, field)


def write_sysex(patch: Mapping) -> bytes:
    """Serialize all documented fields; preserve unmodeled original bits."""
    validate_patch(patch)
    raw = list(patch.get("raw_data", [0] * 33))
    if len(raw) != 33:
        raise ValueError("raw_data must have 33 bytes")
    for x in raw:
        _integer(x, 0, 255, "raw_data byte")
    raw[0] = _integer(patch.get("bank", 0), 0, 255, "bank")
    for key, k in (("modulator", 0), ("carrier", 1)):
        p = patch[key]
        dt = abs(p["dt1"]) | (8 if p["dt1"] < 0 else 0)
        # Keep the negative-zero detune encoding if it was in the original.
        if p["dt1"] == 0 and raw[1+k] >> 4 == 8:
            dt = 8
        raw[1 + k] = (dt << 4) | p["mul"]
        raw[3 + k] = (raw[3 + k] & 128) | p["tl"]
        raw[5 + k] = (p["lks_hi"] << 4) | p["lks_lo"]
        raw[7 + k] = (p["rks"] << 6) | p["ar"]
        raw[9 + k] = (p["am_enable"] << 7) | (p["dt2"] << 6) | p["d1r"]
        raw[11 + k] = (p["wave"] << 6) | p["d2r"]
        raw[13 + k] = (p["d1l"] << 4) | p["rr"]
        raw[20 + k] = (raw[20 + k] & 240) | p["srr"]
    raw[15] = (raw[15] & ~56) | (patch["feedback"] << 3)
    raw[16] = (raw[16] & ~115) | (patch["pms"] << 4) | patch["ams"]
    raw[22] = (raw[22] & 128) | patch["vibrato_delay"]
    raw[24] = (raw[24] & 63) | (int(patch["vibrato"]) << 7) | (int(patch["sustain"]) << 6)
    nibbles = [n for byte in raw for n in (byte >> 4, byte & 15)]
    return bytes([240, 67, 118, 0, *nibbles, (-sum(nibbles)) & 127, 247])


_bank = json.loads(Path(__file__).with_name("factory_voices.json").read_text())
FACTORY_PATCHES = {}
for _voice in _bank["voices"]:
    _patch = read_sysex(bytes.fromhex(_voice["sysex_hex"]), _voice["name"])
    _patch["number"] = _voice["number"]
    _patch["provenance"] = "published PSS-780 ROM SysEx; unverified on local hardware"
    FACTORY_PATCHES[_voice["number"]] = _patch
PATCHES = {p["name"].replace(" ", "_").replace("-", "_"): p for p in FACTORY_PATCHES.values()}


def get_patch(patch: Mapping | int | str) -> dict:
    """Return an independent patch copy by dict, number 0..99 or slug."""
    if isinstance(patch, Mapping):
        return deepcopy(dict(patch))
    if isinstance(patch, (int, np.integer)):
        return deepcopy(FACTORY_PATCHES[int(patch)])
    return deepcopy(PATCHES[patch])


def _model(patch):
    m = dict(MODEL_DEFAULTS)
    m.update(patch.get("model", {}))
    if any(not np.isfinite(float(x)) for x in m.values()):
        raise ValueError("Model constants must be finite")
    for k in ("attack_seconds_at_rate_zero", "decay_seconds_96db_at_rate_zero",
              "rate_steps_per_halving", "tl_db_per_step", "gain"):
        if m[k] <= 0:
            raise ValueError(f"{k} must be positive")
    for k in ("phase_bits", "output_bits"):
        _integer(m[k], 0, 24, k)
    _integer(m["lfo_waveform"], 0, 1, "lfo_waveform")
    _integer(m["lfo_global_phase"], 0, 1, "lfo_global_phase")
    _integer(m["internal_sample_rate"], 8000, 384000, "internal_sample_rate")
    return m


def _effective_rate(rate, rks, midi):
    if rate == 0:
        return 0.0
    return float(np.clip(rate + (midi - 60) * (0.0, 0.0625, 0.125, 0.25)[rks], 0.25, 63))


@njit(cache=True)
def _envelope(n, gate_n, sr, ar, d1r, d2r, d1l, rr, attack_base, decay_base, rate_step, d1l_step):
    """Explicit A/D1/D2/R state machine; output is linear amplitude."""
    result = np.zeros(n, dtype=np.float64)
    if ar == 0:
        return result
    attenuation = 96.0
    # Exponential attenuation trajectory creates a concave rising amplitude.
    attack_seconds = attack_base * 2.0 ** (-ar / rate_step)
    attack_mul = math.exp(-math.log(1000.0) / max(1.0, sr * attack_seconds))
    decay1 = 0.0 if d1r == 0 else 96.0 / (sr * decay_base * 2.0 ** (-d1r / rate_step))
    decay2 = 0.0 if d2r == 0 else 96.0 / (sr * decay_base * 2.0 ** (-d2r / rate_step))
    release = 96.0 / (sr * decay_base * 2.0 ** (-rr / rate_step))
    decay_target = 93.0 if d1l == 15 else d1l * d1l_step
    stage = 0
    for i in range(n):
        if i >= gate_n:
            stage = 3
        if stage == 0:
            attenuation = 0.0 if ar >= 63 else attenuation * attack_mul
            if attenuation <= 0.096:
                attenuation = 0.0
                stage = 1
        elif stage == 1:
            attenuation += decay1
            if attenuation >= decay_target:
                stage = 2
        elif stage == 2:
            attenuation += decay2
        else:
            attenuation += release
        if attenuation >= 96.0:
            if stage != 0:
                break
            result[i] = 0.0
        else:
            result[i] = 10.0 ** (-max(0.0, attenuation) / 20.0)
    return result


def envelope(op, midi=60, duration=3.0, gate=1.5, sr=48000, sustain=False, model=None):
    """Operator A/D1/D2/R amplitude envelope, useful for measurement plots."""
    m = dict(MODEL_DEFAULTS)
    m.update(model or {})
    rates = [_effective_rate(op[x], op["rks"], midi) for x in ("ar", "d1r", "d2r")]
    rr = 4 * op["srr" if sustain else "rr"] + 2
    rr = _effective_rate(rr, op["rks"], midi)
    return _envelope(round(duration * sr), round(gate * sr), sr, *rates,
                     op["d1l"], rr, m["attack_seconds_at_rate_zero"],
                     m["decay_seconds_96db_at_rate_zero"], m["rate_steps_per_halving"],
                     m["d1l_db_per_step"])


def _keyscale_db(op, midi, model):
    # Yamaha's chart centers on C3 (MIDI 60 in its octave naming).
    value = op["lks_hi"] if midi >= 60 else op["lks_lo"]
    # Direction/order from the manual; numerical slopes are unmeasured.
    # High codes 11..15 are curved in the diagram, unlike codes 4..10.
    if midi >= 60:
        slope = (0, -3, -2, -1, 1, 2, 3, 5, 6, 8, 10, 3, 4.5, 6.5, 8.5, 10.5)[value]
        distance = abs(midi - 60)
        if value >= 11:
            distance = 36 * (distance / 36) ** 1.5
    else:
        slope = 0 if value == 0 else (value - 8 if value < 8 else value - 7)
        distance = abs(midi - 60)
    return slope * distance * model["lks_db_per_semitone_step"]


@njit(cache=True)
def _wave(phase, wave, phase_steps, signed_squared):
    if phase_steps > 0:
        phase = math.floor(phase * phase_steps / (2.0 * math.pi)) * (2.0 * math.pi / phase_steps)
    s = math.sin(phase)
    if wave >= 2 and s < 0:
        return 0.0
    if wave == 1 or wave == 3:
        return s * abs(s) if signed_squared else s * s
    return s


@njit(cache=True)
def _synthesize(env_m, env_c, freq_m, freq_c, sr, wave_m, wave_c, index, feedback,
                vibrato_depth, vibrato_hz, delay_n, tremolo_m, tremolo_c,
                phase_steps, output_steps, signed_squared, lfo_waveform=0, lfo_phase=0.0):
    n = len(env_m)
    y = np.zeros(n, dtype=np.float64)
    pm, pc = 0.0, 0.0
    prev1, prev2 = 0.0, 0.0
    for i in range(n):
        lfo = math.sin(2.0 * math.pi * vibrato_hz * i / sr + lfo_phase)
        if lfo_waveform == 1:
            lfo = 2.0 / math.pi * math.asin(lfo)
        pitch = 2.0 ** (vibrato_depth * lfo / 1200.0) if i >= delay_n else 1.0
        pm = (pm + 2.0 * math.pi * freq_m / sr * pitch) % (2.0 * math.pi)
        pc = (pc + 2.0 * math.pi * freq_c / sr * pitch) % (2.0 * math.pi)
        am_m = 10.0 ** (-tremolo_m * (lfo + 1.0) / 40.0)
        am_c = 10.0 ** (-tremolo_c * (lfo + 1.0) / 40.0)
        mod = _wave(pm + feedback * (prev1 + prev2) * 0.5, wave_m, phase_steps, signed_squared) * env_m[i] * am_m
        prev2, prev1 = prev1, mod
        value = _wave(pc + index * mod, wave_c, phase_steps, signed_squared) * env_c[i] * am_c
        if output_steps > 0:
            value = round(value * output_steps) / output_steps
        y[i] = value
    return y


def _render_at_rate(patch, midi=60, velocity=100, duration=3.0, gate=1.5, sr=48000):
    """Original behavioral oscillator at a specified simulation rate."""
    p = get_patch(patch)
    validate_patch(p)
    midi = _integer(midi, 0, 127, "midi")
    velocity = _integer(velocity, 0, 127, "velocity")
    sr = _integer(sr, 8000, 384000, "sr")
    if not np.isfinite(duration) or not 0 <= duration <= 600:
        raise ValueError("duration must be finite and between 0 and 600 seconds")
    if not np.isfinite(gate) or gate < 0:
        raise ValueError("gate must be finite and nonnegative")
    n = round(duration * sr)
    if velocity == 0 or gate == 0 or n == 0:
        return np.zeros(n, dtype=np.float64)
    model = _model(p)
    base = 440.0 * 2.0 ** ((midi - 69) / 12.0)
    envs, freqs = [], []
    for key in ("modulator", "carrier"):
        op = p[key]
        env = envelope(op, midi, duration, gate, sr, p["sustain"], model)
        # 99+ is a documented panel zero; factory sine uses raw 127.
        gain = 0.0 if op["tl"] >= 99 else 10 ** (-(op["tl"] * model["tl_db_per_step"] + _keyscale_db(op, midi, model)) / 20)
        envs.append(env * min(gain, 4.0))
        ratio = 0.5 if op["mul"] == 0 else float(op["mul"])
        cents = op["dt2"] * 600 + op["dt1"] * model["fine_detune_cents_per_step"]
        freqs.append(base * ratio * 2 ** (cents / 1200))
    envs[0] *= (velocity / 127) ** model["velocity_modulation_exponent"]
    envs[1] *= (velocity / 127) ** model["velocity_amplitude_exponent"] * model["gain"]
    fb = 0.0 if p["feedback"] == 0 else model["feedback_max_radians"] * 2.0 ** (p["feedback"] - 7)
    vibrato = (0, 3.4, 6.7, 10, 14, 20, 40, 80)[p["pms"]] if p["vibrato"] else 0
    am_db = (0.0, 1.4, 5.9, 11.8)[p["ams"]]
    return _synthesize(envs[0], envs[1], *freqs, sr, p["modulator"]["wave"],
                       p["carrier"]["wave"], model["modulation_index_max"], fb,
                       vibrato, model["vibrato_hz"], round(p["vibrato_delay"] * model["vibrato_delay_seconds_per_step"] * sr),
                       am_db * p["modulator"]["am_enable"], am_db * p["carrier"]["am_enable"],
                       2 ** model["phase_bits"] if model["phase_bits"] else 0,
                       2 ** (model["output_bits"] - 1) - 1 if model["output_bits"] else 0,
                       model["squared_sine_signed"], model["lfo_waveform"],
                       2 * math.pi * model["vibrato_hz"] * model["lfo_time_offset_seconds"])


def render_note(patch, midi=60, velocity=100, duration=3.0, gate=1.5, sr=48000,
                *, clock_mode="fixed"):
    """Render mono float64 at output rate sr, without gain normalization.

    v2 runs oscillators, envelopes and feedback at the fixed 48 kHz simulation
    clock before rational resampling. This preserves timbre when output rate
    changes; it does not establish the hardware clock. Override the hypothesis
    with patch['model']['internal_sample_rate']. clock_mode='legacy_host'
    reproduces v1, in which the requested output rate also clocks the engine.
    gate starts at note-on; duration includes release; velocity zero is silent.
    """
    if clock_mode not in ("fixed", "legacy_host"):
        raise ValueError("clock_mode must be 'fixed' or 'legacy_host'")
    sr = _integer(sr, 8000, 384000, "sr")
    p = get_patch(patch)
    internal = sr if clock_mode == "legacy_host" else _model(p)["internal_sample_rate"]
    y = _render_at_rate(p, midi, velocity, duration, gate, internal)
    if internal == sr:
        return y
    wanted = round(duration * sr)
    if not len(y) or not wanted:
        return np.zeros(wanted, dtype=np.float64)
    divisor = math.gcd(sr, internal)
    y = resample_poly(y, sr // divisor, internal // divisor)
    if len(y) < wanted:
        y = np.pad(y, (0, wanted - len(y)))
    return y[:wanted]


def render_sequence(events: Iterable[Mapping], duration, sr=48000, max_voices=12,
                    *, clock_mode="fixed"):
    """Mix events {start, gate, midi, velocity, patch} with oldest-voice stealing.

    Released tails count toward the pool. A stolen voice has a 1 ms fade to
    avoid an arbitrary click. Allocation/fade is a host policy, not verified
    Yamaha firmware behavior. Simultaneous notes are deterministic in input order.
    """
    _integer(max_voices, 1, 128, "max_voices")
    _integer(sr, 8000, 384000, "sr")
    if not np.isfinite(duration) or not 0 <= duration <= 600:
        raise ValueError("duration must be finite and between 0 and 600 seconds")
    output = np.zeros(round(duration * sr), dtype=np.float64)
    voices = []
    for event in sorted(events, key=lambda e: e["start"]):
        start = event["start"]
        if not np.isfinite(start) or start < 0:
            raise ValueError("event start must be finite and nonnegative")
        if start >= duration:
            continue
        begin = round(start * sr)
        sample = render_note(event["patch"], event["midi"], event.get("velocity", 100),
                             duration-start, event["gate"], sr, clock_mode=clock_mode)
        # Never allocate silent note-ons or dead tails.
        if not np.any(sample):
            continue
        voices = [v for v in voices if v[2] > begin]
        if len(voices) >= max_voices:
            victim = voices.pop(0)
            old_begin, old_sample, old_end = victim
            cut = begin - old_begin
            rest = old_sample[cut:]
            subtract_end = min(len(output), begin + len(rest))
            output[begin:subtract_end] -= rest[:subtract_end-begin]
            count = min(round(sr * .001), len(rest), len(output)-begin)
            output[begin:begin+count] += rest[:count] * np.linspace(1, 0, count)
        end = min(len(output), begin + len(sample))
        output[begin:end] += sample[:end-begin]
        audible = np.flatnonzero(np.abs(sample) > 1e-8)
        voices.append((begin, sample, begin + int(audible[-1]) + 1 if len(audible) else begin))
    return output


def _voice_duration_bound(patch, midi, gate, sr):
    """Conservative end of the carrier's release, including roundoff margin.

    The current envelope reaches exact zero at 96 dB attenuation. Release
    always increases attenuation, so starting from zero is the longest case.
    This bounds work; it does not alter the envelope or truncate its sound.
    """
    model = _model(patch)
    carrier = patch["carrier"]
    rate = 4 * carrier["srr" if patch["sustain"] else "rr"] + 2
    rate = _effective_rate(rate, carrier["rks"], midi)
    release = model["decay_seconds_96db_at_rate_zero"] * 2 ** (-rate / model["rate_steps_per_halving"])
    # resample_poly's default FIR extends beyond an exact-zero envelope; retain
    # its complete ringout, including for up/downsampling after release ends.
    return gate + release + 32 / min(sr, model["internal_sample_rate"])


def render_program_sequence(notes: Iterable[Mapping], programs: Iterable[Mapping],
                            duration, sr=48000, max_voices=12, *, start_time=0.0,
                            model=None, initial_patch=0, clock_mode="fixed"):
    """Render a MIDI-style performance, preserving context before an excerpt.

    Notes contain absolute ``start``, ``gate``, ``midi`` and optional velocity.
    Programs contain absolute ``time`` and ``patch``. Every change affects
    subsequent note-ons on all channels; earlier notes keep their original
    patch and release envelope. A note at the change's output sample uses the
    new patch; timestamps quantize to the same frames as note placement.
    This global program policy matches the investigated demonstration; it is
    not a general multitimbral MIDI player or verified Yamaha held-note policy.

    The output spans [start_time, start_time+duration). Earlier notes and voice
    stealing are rendered from time zero, then cropped, preserving oscillator
    phase and envelopes. The analytically bounded release avoids rendering a
    long all-zero tail for every note. No per-note normalization is applied.
    """
    sr = _integer(sr, 8000, 384000, "sr")
    _integer(max_voices, 1, 128, "max_voices")
    if clock_mode not in ("fixed", "legacy_host"):
        raise ValueError("clock_mode must be 'fixed' or 'legacy_host'")
    if not np.isfinite(start_time) or start_time < 0:
        raise ValueError("start_time must be finite and nonnegative")
    if not np.isfinite(duration) or duration < 0 or start_time+duration > 600:
        raise ValueError("performance endpoint must be finite and at most 600 seconds")
    schedule = sorted(list(programs), key=lambda e: e["time"])
    times, patches = [], []
    for change in schedule:
        timestamp = change["time"]
        if not np.isfinite(timestamp) or timestamp < 0:
            raise ValueError("program time must be finite and nonnegative")
        patch = get_patch(change["patch"])
        validate_patch(patch)
        if model:
            patch["model"] = {**patch.get("model", {}), **model}
        _model(patch)
        times.append(round(timestamp * sr))
        patches.append(patch)
    fallback = get_patch(initial_patch)
    validate_patch(fallback)
    if model:
        fallback["model"] = {**fallback.get("model", {}), **model}
    _model(fallback)
    endpoint = start_time + duration
    # Allocate by rounded output frames, matching render_sequence's convention.
    begin_crop = round(start_time * sr)
    wanted = round(duration * sr)
    output = np.zeros(max(round(endpoint * sr), begin_crop+wanted), dtype=np.float64)
    voices = []
    for note in sorted(notes, key=lambda e: e["start"]):
        start, gate = note["start"], note["gate"]
        if not np.isfinite(start) or start < 0:
            raise ValueError("note start must be finite and nonnegative")
        if not np.isfinite(gate) or gate < 0:
            raise ValueError("note gate must be finite and nonnegative")
        midi = _integer(note["midi"], 0, 127, "midi")
        velocity = _integer(note.get("velocity", 100), 0, 127, "velocity")
        if start >= endpoint or not velocity or not gate:
            continue
        begin = round(start * sr)
        index = bisect_right(times, begin) - 1
        patch = patches[index] if index >= 0 else fallback
        if _model(patch)["lfo_global_phase"]:
            patch = get_patch(patch)
            patch["model"] = {**patch.get("model", {}), "lfo_time_offset_seconds": start}
        # Additional synthesis context lets output resampling see future input
        # at an excerpt boundary, just as it does in the full performance.
        note_duration = min(endpoint-start+.01, _voice_duration_bound(patch, midi, gate, sr))
        sample = render_note(patch, midi, velocity, note_duration, gate, sr, clock_mode=clock_mode)
        if not np.any(sample):
            continue
        voices = [voice for voice in voices if voice[2] > begin]
        if len(voices) >= max_voices:
            old_begin, old_sample, old_end = voices.pop(0)
            rest = old_sample[begin-old_begin:]
            subtract_end = min(len(output), begin+len(rest))
            output[begin:subtract_end] -= rest[:subtract_end-begin]
            count = min(round(sr*.001), len(rest), len(output)-begin)
            output[begin:begin+count] += rest[:count] * np.linspace(1, 0, count)
        end = min(len(output), begin+len(sample))
        output[begin:end] += sample[:end-begin]
        audible = np.flatnonzero(np.abs(sample) > 1e-8)
        voices.append((begin, sample, begin+int(audible[-1])+1 if len(audible) else begin))
    return output[begin_crop:begin_crop+wanted]


if __name__ == "__main__":
    import argparse
    from scipy.io import wavfile
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--patch", type=int, default=2)
    parser.add_argument("--midi", type=int, default=60)
    parser.add_argument("--seconds", type=float, default=4.0)
    parser.add_argument("--sample-rate", type=int, default=48000)
    parser.add_argument("--clock-mode", choices=("fixed", "legacy_host"), default="fixed")
    args = parser.parse_args()
    audio = render_note(args.patch, args.midi, duration=args.seconds,
                        sr=args.sample_rate, clock_mode=args.clock_mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(args.output, args.sample_rate, audio.astype(np.float32))
