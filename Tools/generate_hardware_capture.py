#!/usr/bin/env python3
"""Generate and independently read back an optional PSS-780 capture kit.

Filesystem only: this module has no MIDI-port or playback dependency. The emitted
MIDI FILES contain SysEx writes to USER BANK 5 and must only be played deliberately
after backing up that bank. See the generated README before routing any file.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / 'build/hardware-capture-kit-20261018'
PROTOCOL_ID = 'press78-hardware-capture-20261018-v1'
PPQ = 1000
TEMPO_US = 1000000  # Exactly one millisecond per tick.
BANK_RAW = 4
PROGRAM = 104
CHANNEL = 0  # Human MIDI channel 1; channel 16 is deliberately never used.
NOTE = 60  # Scientific C4. Some Yamaha displays use a different octave label.
VELOCITY = 127
WARNING = 'OPTIONAL HARDWARE TEST: REPLACES PSS-780 USER BANK 5. BACK UP FIRST.'
MANUAL_URL = 'https://www.nurykabe.com/dump/docs/PSS/manuals/PSS-780_00.pdf'
MANUAL_SHA = 'e1382c76aa9f6351fb3de191228b3209def0cf4ceba54ca6a20406c1e2db0adb'


class InvalidCapture(ValueError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise InvalidCapture(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pure_carrier(**values: int) -> bytes:
    """Independently authored 33-byte voice; no factory bank is read or copied."""
    p = dict(ar=63, d1r=0, d1l=0, d2r=0, rr=15, srr=5, tl=24)
    p.update(values)
    raw = bytearray(33)
    raw[0] = BANK_RAW
    raw[1] = raw[2] = 1  # Ratios1, no fine/coarse detune.
    raw[3], raw[4] = 127, p['tl']  # Minimum modulator level; carrier TL is varied.
    raw[5] = raw[6] = 0  # Flat level scaling, both keyboard halves.
    raw[7] = 0  # Modulator AR0: no attack. Its TL127 is additionally minimum.
    raw[8] = p['ar']  # RKS0 for both operators.
    raw[9], raw[10] = 0, p['d1r']
    raw[11], raw[12] = 0, p['d2r']  # Sine tables0; AM and DT2 both off.
    raw[13], raw[14] = 15, (p['d1l'] << 4) | p['rr']
    raw[20], raw[21] = 15, p['srr']
    # Feedback/PMS/AMS/VDT/V/S and all don't-care bits are independently zero.
    return bytes(raw)


def voice_sysex(raw: bytes) -> bytes:
    require(len(raw) == 33 and raw[0] == BANK_RAW, 'voice must address raw bank4')
    data = bytes(n for b in raw for n in (b >> 4, b & 15))
    checksum = (-sum(data)) & 127
    return bytes((0xF0, 0x43, 0x76, 0)) + data + bytes((checksum, 0xF7))


def vlq(n: int) -> bytes:
    require(0 <= n <= 0x0FFFFFFF, 'VLQ value outside SMF range')
    result = [n & 127]
    n >>= 7
    while n:
        result.insert(0, (n & 127) | 128)
        n >>= 7
    return bytes(result)


def meta(kind: int, text: str | bytes) -> bytes:
    data = text.encode('ascii') if isinstance(text, str) else text
    return bytes((0xFF, kind)) + vlq(len(data)) + data


def make_smf(events: list[tuple[int, bytes]], end_ms: int) -> bytes:
    track = bytearray()
    prior = 0
    for tick, data in sorted(events, key=lambda x: x[0]):
        require(tick >= prior, 'events not chronological')
        track.extend(vlq(tick - prior))
        # In an SMF, F0's length includes the final F7 but excludes F0 itself.
        track.extend(bytes((0xF0,)) + vlq(len(data) - 1) + data[1:]
                     if data[0] == 0xF0 else data)
        prior = tick
    track.extend(vlq(end_ms - prior) + meta(0x2F, b''))
    return b'MThd' + struct.pack('>IHHH', 6, 0, 1, PPQ) + b'MTrk' + struct.pack('>I', len(track)) + track


def read_smf(blob: bytes) -> list[dict]:
    """Separate byte reader; does not use the encoder, patch builder or VLQ writer."""
    if len(blob) < 22 or blob[:4] != b'MThd':
        raise InvalidCapture('missing SMF header')
    size, form, tracks, division = struct.unpack('>IHHH', blob[4:14])
    require((size, form, tracks, division) == (6, 0, 1, 1000), 'unexpected SMF header')
    require(blob[14:18] == b'MTrk', 'missing track')
    n = int.from_bytes(blob[18:22], 'big')
    require(n == len(blob) - 22, 'track length/trailing bytes mismatch')
    data = blob[22:]
    pos = tick = 0
    rows = []
    ended = False

    def take(count: int) -> bytes:
        nonlocal pos
        require(pos + count <= len(data), 'truncated SMF event')
        out = data[pos:pos + count]
        pos += count
        return out

    def number() -> int:
        value = 0
        for _ in range(4):
            b = take(1)[0]
            value = (value << 7) | (b & 127)
            if b < 128:
                return value
        raise InvalidCapture('SMF variable integer too long')

    while pos < len(data):
        require(not ended, 'events after end-of-track')
        tick += number()
        status = take(1)[0]
        row = dict(tick=tick, seconds=tick / 1000)
        if status == 0xFF:
            kind = take(1)[0]
            payload = take(number())
            require(kind in (1, 3, 6, 0x51, 0x2F), 'unexpected meta type')
            if kind == 0x51:
                require(tick == 0 and payload == b'\x0f\x42\x40', 'tempo must be1000000us at tick0')
            if kind == 0x2F:
                require(payload == b'', 'end-of-track has data')
                ended = True
            row.update(kind='meta', meta_type=kind, data_hex=payload.hex())
        elif status == 0xF0:
            payload = take(number())
            row.update(kind='sysex', data_hex=(b'\xf0' + payload).hex())
        else:
            lengths = {0x80: 2, 0x90: 2, 0xB0: 2, 0xC0: 1, 0xE0: 2}
            high, channel = status & 0xF0, status & 15
            require(high in lengths and channel == 0, 'unexpected MIDI status/channel')
            payload = take(lengths[high])
            require(all(b < 128 for b in payload), 'non-data byte in channel message')
            row.update(kind='channel', status=status, data=list(payload),
                       data_hex=(bytes((status,)) + payload).hex())
        rows.append(row)
    require(ended, 'missing end-of-track')
    require(sum(r.get('meta_type') == 0x51 for r in rows) == 1, 'one tempo required')
    return rows


def inspect_voice(message: bytes) -> dict:
    # Independent wire decoder/checksum: explicitly excludes the4-byte header andF7.
    require(len(message) == 72, 'voice SysEx must contain72 bytes')
    require(message[:4] == b'\xf0\x43\x76\x00' and message[-1] == 0xF7,
            'wrong Yamaha voice header or terminator')
    nibbles, check = message[4:70], message[70]
    require(len(nibbles) == 66 and all(b <= 15 for b in nibbles), 'invalid nibble payload')
    require(check < 128 and (sum(nibbles) + check) % 128 == 0, 'incorrect Yamaha checksum')
    raw = bytes(16 * nibbles[i] + nibbles[i + 1] for i in range(0, 66, 2))
    require(raw[0] == 4, 'kit must only write user bank5/raw4')
    require(raw[1:4] == bytes((1, 1, 127)), 'unexpected ratios/modulator level')
    require(raw[5:8] == b'\x00\x00\x00', 'scaling/modulator attack must be zero')
    require(raw[8] <= 63 and raw[10] <= 63 and raw[12] <= 63, 'carrier rate/scaling invalid')
    require(raw[9] == 0 and raw[11] == 0, 'modulator AM/detune/wave/rate changed')
    require(raw[13] == 15 and raw[15:20] == bytes(5), 'feedback/LFO/reserved data changed')
    require(raw[20] == 15 and raw[21] <= 15 and raw[22:] == bytes(11),
            'SRR/LFO/flags/reserved data changed')
    require(raw[4] <= 127, 'TL exceeds7-bit range')
    return dict(raw_hex=raw.hex(), bank_raw=raw[0], ar=raw[8], d1r=raw[10],
                d1l=raw[14] >> 4, d2r=raw[12], rr=raw[14] & 15,
                srr=raw[21], tl=raw[4], rks=0)


def case(name: str, family: str, gate: int, tail: int, **patch: int) -> dict:
    return dict(case_id=name, family=family, gate_ms=gate, tail_ms=tail, patch=patch)


def calibration_cases() -> list[dict]:
    rows = []
    for i, tl in enumerate((0, 12, 24, 36, 48, 24, 0)):
        rows.append(case(f'tl-{i:02d}-{tl}', 'static_tl', 3000, 1000, tl=tl))
    for ar in (0, 20, 24, 28, 32, 36, 41, 48, 63):
        rows.append(case(f'ar-{ar}', 'attack', 4000, 1000, ar=ar))
    for rate in (12, 16, 20, 24, 28, 32):
        rows.append(case(f'd2r-{rate}', 'decay2', 9000, 1000, d2r=rate))
    for rate in (12, 20, 28):
        rows.append(case(f'd1r-{rate}-target8', 'decay1', 10000, 1000, d1r=rate, d1l=8))
    for target in (0, 1):
        rows.append(case(f'd1zero-target{target}', 'decay1_zero_endpoint', 5000, 1000,
                         d1r=0, d1l=target, d2r=20))
    for rr, tail in ((4, 8000), (5, 6000), (6, 4000), (7, 3000), (8, 2000),
                     (10, 1000), (12, 1000), (15, 1000)):
        rows.append(case(f'rr-{rr}', 'release', 1000, tail, rr=rr))
    return rows


def release_cases() -> list[dict]:
    # Deliberately constructed simple probe, not a Human Voice1 preset copy.
    return [case(f'rr7-ar{ar}-gate{gate}', 'effect_release_interaction', gate, 6000,
                 ar=ar, d1r=1, d1l=0, d2r=0, rr=7, srr=5)
            for ar in (32, 63) for gate in (30, 220, 2000)]


def definitions(tail_scale: float = 1.0) -> list[dict]:
    files = [dict(name='00_gain_check.mid', role='Gain check at highest test level',
                  reverb='OFF', sustain=0,
                  cases=[case('gain-full-level', 'gain_check', 3000, 2000, tl=0)]),
             dict(name='01_calibration_dry.mid', role='Main pure-carrier calibration',
                  reverb='OFF', sustain=0, cases=calibration_cases())]
    for i, (reverb, sustain) in enumerate((('OFF', 0), ('ON', 0), ('OFF', 127), ('ON', 127)), 10):
        files.append(dict(name=f'{i}_release_reverb_{reverb.lower()}_sustain_{"on" if sustain else "off"}.mid',
                          role='Matched release interaction', reverb=reverb,
                          sustain=sustain, cases=release_cases()))
    for file in files:
        for row in file['cases']:
            row['tail_ms'] = round(row['tail_ms'] * tail_scale)
    return files


def write_file(spec: dict) -> tuple[bytes, list[dict]]:
    events = [(0, meta(0x51, TEMPO_US.to_bytes(3, 'big'))),
              (0, meta(3, spec['name'])), (0, meta(1, WARNING))]
    now = 4000
    rows = []
    for definition in spec['cases']:
        raw = pure_carrier(**definition['patch'])
        syx = voice_sysex(raw)
        onset = now + 1000
        offset = onset + definition['gate_ms']
        events.extend([(now, meta(6, definition['case_id'])), (now, syx),
                       (now + 100, bytes((0xC0, PROGRAM))),
                       (now + 200, bytes((0xB0, 1, 0))),
                       (now + 250, bytes((0xB0, 64, spec['sustain']))),
                       (now + 300, bytes((0xE0, 0, 64))),
                       (onset, bytes((0x90, NOTE, VELOCITY))),
                       (offset, bytes((0x80, NOTE, 0)))])
        row = dict(file=spec['name'], case_id=definition['case_id'], family=definition['family'],
                   midi_channel=1, note=NOTE, velocity=VELOCITY, patch_ms=now,
                   program_ms=now + 100, note_on_ms=onset, note_off_ms=offset,
                   gate_ms=definition['gate_ms'], tail_ms=definition['tail_ms'],
                   reverb_required=spec['reverb'], sustain_cc64=spec['sustain'],
                   **inspect_voice(syx), sysex_hex=syx.hex(), sysex_sha256=digest(syx))
        rows.append(row)
        now = offset + definition['tail_ms']
    events.extend([(now, bytes((0xB0, 64, 0))), (now + 10, bytes((0xB0, 1, 0)))])
    return make_smf(events, now + 4000), rows


def csv_bytes(rows: list[dict], fields: list[str]) -> bytes:
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore', lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode('utf-8')


def verify_file(blob: bytes, cases: list[dict]) -> dict:
    events = read_smf(blob)
    patches = {r['patch_ms']: r for r in cases}
    expected_on = {r['note_on_ms']: r for r in cases}
    expected_off = {r['note_off_ms']: r for r in cases}
    current = active = None
    expected_cc64 = {r['patch_ms'] + 250: r['sustain_cc64'] for r in cases}
    final_tail_end = cases[-1]['note_off_ms'] + cases[-1]['tail_ms']
    controllers_seen = set()
    found = dict(sysex=0, program=0, note_on=0, note_off=0)
    for event in events:
        tick = event['tick']
        if event['kind'] == 'sysex':
            require(active is None, 'patch write while a MIDI gate is open')
            require(tick in patches, 'unexpected patch write time')
            decoded = inspect_voice(bytes.fromhex(event['data_hex']))
            current = patches[tick]
            require(all(decoded[key] == current[key] for key in decoded), 'patch differs from manifest')
            found['sysex'] += 1
        elif event['kind'] == 'channel':
            status, data = event['status'], event['data']
            if status == 0xC0:
                require(current is not None and data == [104] and tick == current['program_ms'],
                        'wrong user-bank program or program time')
                found['program'] += 1
            elif status == 0xB0:
                require(data[0] in (1, 64) and data[1] in (0, 127), 'undocumented kit controller')
                if data[0] == 1:
                    require(data[1] == 0, 'Vibrato must remain disabled')
                elif tick in expected_cc64:
                    require(data[1] == expected_cc64[tick], 'Sustain condition/time differs from manifest')
                    controllers_seen.add(tick)
                else:
                    require(tick == final_tail_end and data[1] == 0, 'unexpected Sustain event')
            elif status == 0xE0:
                require(data == [0, 64], 'pitch bend must be centered')
            elif status == 0x90:
                require(tick in expected_on and current == expected_on[tick], 'unexpected note-on')
                require(data == [60, 127] and active is None, 'wrong/overlapping note')
                require(tick - current['patch_ms'] >= 1000, 'insufficient patch settle time')
                active = current
                found['note_on'] += 1
            elif status == 0x80:
                require(tick in expected_off and active == expected_off[tick], 'unmatched note-off')
                require(data == [60, 0], 'wrong note-off')
                require(tick - active['note_on_ms'] == active['gate_ms'], 'gate differs from case')
                active = None
                found['note_off'] += 1
    require(controllers_seen == set(expected_cc64), 'missing Sustain condition events')
    require(active is None and found == dict.fromkeys(found, len(cases)), 'missing/duplicate cases')
    return dict(status='PASS', cases=len(cases), events=len(events), counts=found,
                end_seconds=events[-1]['seconds'], midi_sha256=digest(blob))


def mutation_checks(blob: bytes, first_case: dict) -> list[str]:
    messages = []
    original = bytearray.fromhex(first_case['sysex_hex'])
    for label, mutant in [('bad-checksum', original[:-2] + bytes((original[-2] ^ 1, 0xF7))),
                          ('truncated-sysex', original[:-1]),
                          ('bank0', original[:])]:
        if label == 'bank0':
            mutant[4:6] = b'\x00\x00'
            mutant[70] = (-sum(mutant[4:70])) & 127
        try:
            inspect_voice(bytes(mutant))
        except InvalidCapture:
            messages.append(label)
        else:
            raise InvalidCapture(f'mutation unexpectedly accepted: {label}')
    try:
        read_smf(blob[:-1])
    except InvalidCapture:
        messages.append('truncated-smf')
    else:
        raise InvalidCapture('truncated SMF accepted')
    return messages


def validate_directory(output: Path) -> dict:
    manifest = json.loads((output / 'cases.json').read_text())
    rows = manifest['cases']
    checks = []
    for file in manifest['files']:
        cases = [r for r in rows if r['file'] == file['name']]
        blob = (output / file['name']).read_bytes()
        require(digest(blob) == file['sha256'], 'MIDI hash differs from cases.json')
        checks.append(dict(file=file['name'], **verify_file(blob, cases)))
    require([r['ar'] for r in rows if r['family'] == 'attack'] == [0, 20, 24, 28, 32, 36, 41, 48, 63],
            'AR sweep coverage changed')
    require([r['d2r'] for r in rows if r['family'] == 'decay2'] == [12, 16, 20, 24, 28, 32],
            'D2 sweep coverage changed')
    require([r['rr'] for r in rows if r['family'] == 'release'] == [4, 5, 6, 7, 8, 10, 12, 15],
            'RR sweep coverage changed')
    # The effect files use exactly the same33 raw patch bytes and gates. Only
    # documented CC64 and required physical Reverb state differ.
    effect = [[r for r in rows if r['file'] == file['name']]
              for file in manifest['files'] if file['name'].startswith(('10_', '11_', '12_', '13_'))]
    require(len(effect) == 4 and all(len(group) == 6 for group in effect), 'four effect pairs required')
    for group in effect[1:]:
        require([(r['raw_hex'], r['gate_ms']) for r in group] ==
                [(r['raw_hex'], r['gate_ms']) for r in effect[0]], 'effect patches/gates differ')
    csv_rows = list(csv.DictReader((output / 'cases.csv').open(newline='')))
    require(len(csv_rows) == len(rows), 'CSV case count differs')
    for emitted, expected in zip(csv_rows, rows):
        require(all(str(expected[key]) == value for key, value in emitted.items()), 'CSV schedule differs from manifest')
    mutations = mutation_checks((output / manifest['files'][0]['name']).read_bytes(), rows[0])
    # These remain syntactically valid MIDI; the independent schedule checker
    # must still reject their semantically wrong destination/note/effect state.
    tests = [('wrong-program', '00_gain_check.mid', b'\xc0\x68', b'\xc0\x67'),
             ('wrong-noteoff', '00_gain_check.mid', b'\x80\x3c\x00', b'\x80\x3d\x00'),
             ('wrong-sustain-condition', '12_release_reverb_off_sustain_on.mid', b'\xb0\x40\x7f', b'\xb0\x40\x00')]
    for label, filename, before, after in tests:
        blob = (output / filename).read_bytes()
        require(before in blob, 'mutation witness unavailable')
        mutant = blob.replace(before, after, 1)
        try:
            verify_file(mutant, [r for r in rows if r['file'] == filename])
        except InvalidCapture:
            mutations.append(label)
        else:
            raise InvalidCapture('semantic mutation accepted: ' + label)
    return dict(status='PASS', protocol=PROTOCOL_ID, files=checks, total_cases=len(rows),
                checksum_and_smf_rejections=mutations,
                explicit_limits=['Syntax and intended schedules only; no MIDI playback, hardware or audio verified.'])


def protocol() -> dict:
    return dict(protocol_id=PROTOCOL_ID, optional=True, filesystem_only=True,
                generated_files_transmit_if_deliberately_played=True,
                bank_write=dict(user_bank=5, raw_bank=4, program_change_byte=104, midi_channel=1,
                                behavior='Repeatedly replaces user bank5 with temporary independent test voices.',
                                prerequisite='Back up all user voice banks and record setup before deliberate playback.'),
                manufacturer_sources=[dict(url=MANUAL_URL, local_reviewed_sha256=MANUAL_SHA,
                    printed_pages=[35, 41, 46], facts=['Raw0..4 selects banks1..5; two nibbles per byte, most significant first.',
                    'PC100..104 selects user banks1..5 on channels1..15.',
                    'Mode99 recognizes CC1 and CC64; physical Reverb/Chorus remain operable.',
                    'No documented Reverb CC is used; CC123 is not recognized and is not emitted.'])],
                recording=dict(connection='AUX L/R into two line inputs; record both independently.',
                    format='48kHz,24-bit PCM WAV; constant gain and instrument master volume.',
                    processing='No AGC, normalization, compressor, limiter, gate, denoise, EQ or external effects.',
                    gain='Use gain-check file deliberately; choose input/master gain with highest-level C4 safely below clipping, then leave fixed.',
                    clocks='No resampling, time stretching or pitch correction.',
                    evidence='Record instrument serial/modifications, supply, tuning, routing, physical LEDs and actual capture software settings.'),
                musical=dict(midi_note=60, scientific_name='C4', velocity=127, rks=0,
                             patch_source='Independent33-byte pure-carrier construction, no factory-bank copy.',
                             event_units='SMF0,1000PPQ,1000000us/quarter;1tick=1ms.',
                             schedule_limit='Intended SMF gates, not measured hardware-arrival times; capture MIDI loopback if available.'),
                effect_conditions=dict(reverb='Set physical Reverb LED to each filename condition; no Reverb controller fabricated.',
                    sustain='Mode99 panel Sustain is not relied on. The same patch defaultsS0; CC64=0/127 follows every PC104.',
                    other='Chorus off, Vibrato off, no rhythms/accompaniment; record actual states.'),
                interpretation_limits=['TL step response tests capture transfer; an assumed0.75dB/code is not asserted as an OPU specification.',
                    'No anticipated time constant or96/48dB cutoff is encoded as measured hardware truth.',
                    'This kit is not sent, played or auto-routed by its generator.'])


def generate(output: Path, protocol_path: Path | None, tail_scale: float = 1.0) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    all_cases, files = [], []
    for spec in definitions(tail_scale):
        blob, rows = write_file(spec)
        (output / spec['name']).write_bytes(blob)
        all_cases.extend(rows)
        parsed = read_smf(blob)
        files.append(dict(name=spec['name'], role=spec['role'], reverb_required=spec['reverb'],
                          sustain_cc64=spec['sustain'], cases=len(rows),
                          seconds=parsed[-1]['seconds'], bytes=len(blob), sha256=digest(blob)))
    source = protocol()
    source['tail_scale'] = tail_scale
    source['tail_window_limit'] = 'Finite observation window; a subsequent patch write censors any remaining tail. Never infer completion merely from the scheduled silence.'
    source['generator_sha256'] = digest(Path(__file__).read_bytes())
    source['files'] = files
    source_bytes = (json.dumps(source, indent=2) + '\n').encode()
    (output / 'protocol.json').write_bytes(source_bytes)
    if protocol_path:
        protocol_path.parent.mkdir(parents=True, exist_ok=True)
        protocol_path.write_bytes(source_bytes)
    (output / 'cases.json').write_text(json.dumps(dict(protocol=PROTOCOL_ID, files=files, cases=all_cases), indent=2) + '\n')
    fields = ['file', 'case_id', 'family', 'midi_channel', 'note', 'velocity', 'patch_ms',
              'program_ms', 'note_on_ms', 'note_off_ms', 'gate_ms', 'tail_ms', 'ar', 'd1r',
              'd1l', 'd2r', 'rr', 'srr', 'tl', 'rks', 'reverb_required', 'sustain_cc64', 'sysex_sha256']
    (output / 'cases.csv').write_bytes(csv_bytes(all_cases, fields))
    event_rows = [dict(file=file['name'], **row) for file in files
                  for row in read_smf((output / file['name']).read_bytes())]
    (output / 'events.csv').write_bytes(csv_bytes(event_rows, ['file', 'tick', 'seconds', 'kind', 'status', 'meta_type', 'data_hex']))
    takes = [dict(midi_file=f['name'], recorded_wav=None, sha256=None, actual_reverb=None,
                  actual_sustain=None, actual_chorus=None, actual_vibrato=None,
                  initial_sample_of_midi_t0=None, notes=None) for f in files]
    template = dict(filled_by_operator=False, instrument='Yamaha PSS-780', serial=None, modifications=None,
        supply=None, tuning=None, master_volume=None, midi_mode=99, receive_channel=1,
        interface=None, line_inputs=None, input_gain=None, daw=None, audio_format='48kHz24bitPCM',
        processing_confirmed_absent=None, resampling_confirmed_absent=None,
        voice_bank_backup_path=None, midi_loopback_path=None, physical_effect_photo_path=None, takes=takes)
    (output / 'capture_metadata_template.json').write_text(json.dumps(template, indent=2) + '\n')
    table = '\n'.join(f"| {f['name']} | {f['seconds']:.2f}s | {f['cases']} | {f['reverb_required']} | {'ON' if f['sustain_cc64'] else 'OFF'} |" for f in files)
    readme = f'''# Optional PSS-780 hardware capture kit\n\n{WARNING}\n\nThese files contain Yamaha voice SysEx. If you deliberately route and play one on a PSS-780, it repeatedly replaces DIGITAL SYNTHESIZER user bank5 (raw bank4), then selects program104 on MIDI channel1. Back up the user voice banks and current setup first. Bank5 remains a temporary calibration voice afterwards; restore the backup when finished.\n\nGeneration opens no MIDI port and performs no playback or hardware operation. Do not auto-route an imported file.\n\n| MIDI file | Duration | Cases | Physical Reverb | MIDI Sustain |\n|---|---:|---:|---|---|\n{table}\n\nUse MIDI MODE99 and receive channel1. Program104 means bank5 (some DAWs display programs starting at1). Ensure your player preserves embedded SysEx and does not remap program numbers. Each case waits1second after its voice write before C4/MIDI60 velocity127; notes have explicit note-offs. No clock, transport, All Notes Off, or undocumented Reverb message is emitted.\n\n1. Record the actual instrument/setup and back up its user banks.\n2. With Reverb/Chorus/Vibrato off, deliberately use the gain-check file to set unclipped recording gain, then leave all gains and master volume fixed.\n3. Record the dry calibration file from AUX L/R to stereo48kHz24bitPCM with no AGC, normalization, compression, limiter, gate, denoise, EQ, external effects, resampling, time stretch or pitch correction.\n4. Record the four matched release files separately with the physical Reverb LED matching their names. Sustain is controlled by documented CC64 after each program change, because the Mode99 front panel cannot be relied on to toggle it. Chorus stays off; Vibrato is disabled in patch/CC1. Do not change effects during a file.\n5. Fill capture_metadata_template.json, preserving actual settings rather than assumed settings. Capture MIDI loopback alongside audio if available; file gate times are intended times, not measured hardware arrival times.\n\nThe source patch is a fresh pure carrier; no factory preset dump is copied. cases.csv/cases.json describe all rates, raw patches, exact millisecond gates and silences. events.csv is decoded from the emitted MIDI. Repeated TL values reveal gain-history changes; the hardware TL law itself remains to be measured. Attack0 and the D1R0/D1L0 versus1 pair are deliberate silent/endpoint controls. Low release rates have longer tail windows. No envelope constants or cutoff are claimed as hardware truth. Each tail silence is a finite observation window: if audio remains at the next patch write, mark the tail censored rather than completed. Generate a separate longer kit with --tail-scale 2 (or higher) for a follow-up; preserve the original recordings and manifest.\n\nManufacturer reference: {MANUAL_URL}, printed pp35/41/46. See protocol.json for source hash and limitations. validation.json independently reads the generated SMF/SysEx and checks bank, checksum, gates, sweeps and matching effect patches; it establishes no hardware result.\n\nRegenerate: python3 Tools/generate_hardware_capture.py --output {output}\nValidate without writing: python3 Tools/generate_hardware_capture.py --output {output} --validate-only\n'''
    (output / 'README.md').write_text(readme)
    result = validate_directory(output)
    (output / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--protocol-json', type=Path, help='Optional copy of authored protocol metadata')
    parser.add_argument('--tail-scale', type=float, default=1.0, help='Multiply all tail observation windows (1..10), preserving gates')
    parser.add_argument('--validate-only', action='store_true', help='Read existing kit; do not write files')
    args = parser.parse_args()
    require(1 <= args.tail_scale <= 10, '--tail-scale must be1..10')
    require(not (args.validate_only and args.protocol_json), '--validate-only cannot write protocol copy')
    result = validate_directory(args.output) if args.validate_only else generate(args.output, args.protocol_json, args.tail_scale)
    print(json.dumps(dict(status=result['status'], files=len(result['files']), cases=result['total_cases'],
                         output=str(args.output), hardware_playback=False), indent=2))


if __name__ == '__main__':
    try:
        main()
    except (InvalidCapture, OSError, json.JSONDecodeError) as exc:
        print(f'Capture kit error: {exc}', file=sys.stderr)
        raise SystemExit(1)
