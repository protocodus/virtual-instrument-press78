#!/usr/bin/env python3
"""One-time assumed-hardware auditions; protocol is design-frozen.json.

Generate narrowly patched native translation units in a NEW ignored directory.
Keep shipping Source/DSP untouched; never read original captured audio or fit
parameters. Each A/B pair differs in one mechanism, then receives constant RMS
matching. These metrics measure software behavior, not hardware fidelity.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np
from scipy.io import wavfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RATE = 48000
FRAMES = 14 * RATE


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    with Path(path).open("x") as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write("\n")


def checked_replace(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError("Native insertion point changed; explicit review required")
    return text.replace(old, new)


def compile_models(out):
    native = (ROOT / "Source/DSP/Press78Engine.cpp").read_text()
    includes = "".join('#include "' + str(HERE / h) + '"\n' for h in
                       ("EnvelopeHypothesis.h", "OutputHypothesis.h"))
    hook = "    const double em = modEnvelope.next(released), ec = carrierEnvelope.next(released);"
    modified = checked_replace(native, hook,
        "    const bool knee = press78::research::AssumedEnvelope::engaged(carrierEnvelope, released, true);\n"
        "    const double em = press78::research::AssumedEnvelope::next(modEnvelope, patch.modulator, note, released, knee);\n"
        "    const double ec = press78::research::AssumedEnvelope::next(carrierEnvelope, patch.carrier, note, released, knee);")
    sources = {"baseline": native, "envelope": modified,
        "envelope_off": checked_replace(modified, "carrierEnvelope, released, true);", "carrierEnvelope, released, false);"),
        "output": checked_replace(native,
            "    const double circuit = analog_.process(mono);",
            "    mono = press78::research::OutputHypothesis::process(mono);\n"
            "    const double circuit = analog_.process(mono);")}
    result = {}
    for name, source in sources.items():
        cpp = out / (name + ".cpp")
        cpp.write_text(includes + source + '\n#include "' + str(HERE / "Renderer.cpp") + '"\n')
        binary = out / name
        command = ["clang++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-pedantic",
                   "-I", str(ROOT / "Source/DSP"), str(cpp), "-o", str(binary)]
        p = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        (out / (name + "-compile.log")).write_bytes(p.stdout)
        if p.returncode:
            raise RuntimeError("Compile failed: " + name + "; log retained")
        result[name] = {"executable": binary, "generated_source_sha256": sha(cpp), "command": command}
    return result


def render(binary, fixture, block=64):
    p = subprocess.run([str(binary), str(fixture), str(block)], stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, check=True)
    data = np.frombuffer(p.stdout, dtype="<f4").reshape((-1, 2)).copy()
    if data.shape != (FRAMES, 2) or not np.isfinite(data).all():
        raise RuntimeError("Invalid native audio")
    return data, json.loads(p.stderr)


def rms(data):
    return float(np.sqrt(np.mean(np.square(data.astype(np.float64)))))


def tail_metrics(data):
    # First known note-off at1.75s. Last complete 20ms window crossing threshold,
    # within first note's six-second support; raw audio, prior to RMS matching.
    mono = np.mean(data.astype(np.float64), axis=1)
    hold = mono[int(1.25*RATE):int(1.65*RATE)]
    reference = rms(hold)
    start = int(1.75*RATE)
    windows = mono[start:int(6.75*RATE)].reshape((-1, 960))
    levels = np.sqrt(np.mean(windows**2, axis=1))
    result = {"hold_reference_rms": reference, "window_seconds": .02}
    for db in (20, 40, 60):
        hits = np.flatnonzero(levels >= reference * 10**(-db/20))
        result["last_above_minus_%ddb_seconds" % db] = float((hits[-1]+1)*.02) if hits.size else 0.0
    return result


def export_pair(out, folder, a, b, explanation):
    destination = out / folder
    destination.mkdir()
    (destination / "raw").mkdir()
    levels = [rms(a), rms(b)]
    if min(levels) <= 0:
        raise RuntimeError("Silent audition")
    target = min(levels)
    trims = [target / x for x in levels]
    peak = max(float(np.max(np.abs(x.astype(np.float64) * gain))) for x, gain in zip((a,b), trims))
    common = min(1.0, .95 / peak)
    receipts = {}
    for letter, raw, trim in zip("AB", (a,b), trims):
        data = (raw.astype(np.float64) * trim * common).astype(np.float32)
        path = destination / (letter + ".wav")
        wavfile.write(path, RATE, data)
        raw_path = destination / "raw" / (letter + ".wav")
        wavfile.write(raw_path, RATE, raw)
        receipts[letter] = {"raw_rms": rms(raw), "raw_sha256_float32": hashlib.sha256(raw.tobytes()).hexdigest(),
            "rms_trim_db": 20*math.log10(trim), "common_safety_gain": common,
            "matched_rms": rms(data), "matched_peak": float(np.max(np.abs(data))), "wav_sha256": sha(path),
            "raw_wav_sha256": sha(raw_path)}
    key = ("A: unchanged shipping native implementation under the frozen audition controls.\n\n"
           "B: " + explanation + "\n\n"
           "Whole-file stereo RMS matched to the quieter member, then one common peak safety gain.\n"
           "These are assumed scenarios; no listener verdict or improved hardware accuracy is claimed.\n\n"
           + json.dumps(receipts, indent=2) + "\n")
    (destination / "key.md").write_text(key)
    return receipts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    build = ROOT / "build/assumed-hardware-20261019"
    if not out.is_relative_to(build) or out == build:
        raise RuntimeError("Output must be a new descendant of ignored build/assumed-hardware-20261019")
    out.mkdir(parents=True, exist_ok=False)
    production = {str(p.relative_to(ROOT)): sha(p) for p in sorted((ROOT / "Source/DSP").glob("*")) if p.is_file()}
    result = {"schema": "press78.assumed-hardware-result.v1", "status": "in_progress",
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "design_sha256": sha(HERE / "design-frozen.json"), "production_sources": production,
        "implementation_sha256": {p.name:sha(p) for p in sorted(HERE.iterdir()) if p.is_file()},
        "sample_rate": RATE, "frames": FRAMES, "hardware_fidelity_score": None,
        "fidelity_reason": "No new calibrated hardware reference; chosen assumptions are not identified target values."}
    write_json(out / "inputs.json", result)
    models = compile_models(out)
    result["models"] = {name:{k:str(v) if isinstance(v,Path) else v for k,v in meta.items()}
                        for name,meta in models.items()}
    p = subprocess.run([str(models["baseline"]["executable"]), "contracts"], capture_output=True, check=False, text=True)
    (out / "contracts.stdout").write_text(p.stdout)
    (out / "contracts.stderr").write_text(p.stderr)
    p.check_returncode()
    result["contracts"] = json.loads(p.stdout)
    result["silence"] = {}
    for name in ("baseline", "envelope", "output"):
        audio, _ = render(models[name]["executable"], 101)
        if np.count_nonzero(audio):
            raise RuntimeError(name + " adds signal to silence")
        result["silence"][name] = "exactly zero"
    result["envelope"] = {}
    for program in (65,93,97):
        a, am = render(models["baseline"]["executable"], program)
        b, bm = render(models["envelope"]["executable"], program)
        hold_end = int(1.75*RATE)+32
        if not np.array_equal(a[:hold_end],b[:hold_end]):
            raise RuntimeError("Envelope candidate changes held sound")
        if np.array_equal(a,b) or bm["max_active_voices"]>1:
            raise RuntimeError("Missing release change or sparse voice pressure")
        pair = export_pair(out, "set-"+str(program), a,b,
            "Sibling-inspired carrier-triggered release knee at assumed18 dB; each native RR is capped to its native RR4 rate after the knee. No other change.")
        result["envelope"][str(program)] = {"native_a":am,"native_b":bm,"held_portion_exact":True,
            "A":tail_metrics(a),"B":tail_metrics(b),"listening":pair}
        if program==93:
            off,_=render(models["envelope_off"]["executable"],program)
            if not np.array_equal(a,off):
                raise RuntimeError("Reverb-OFF native audio parity failed")
            result["contracts"]["reverb_off_complete_audio_exact"] = True
            for name, expected in (("baseline",a),("envelope",b)):
                alternate,_=render(models[name]["executable"],program,257)
                if not np.array_equal(expected,alternate):
                    raise RuntimeError("Native envelope block partition differs")
                result["contracts"][name+"_block_partition_exact"] = True
    a, am = render(models["baseline"]["executable"],100)
    b, bm = render(models["output"]["executable"],100)
    if np.array_equal(a,b):
        raise RuntimeError("Output candidate inaudible by exact comparison")
    alternate,_ = render(models["output"]["executable"],100,257)
    if not np.array_equal(b,alternate):
        raise RuntimeError("Native output block partition differs")
    repeat,_ = render(models["output"]["executable"],100)
    if not np.array_equal(b,repeat):
        raise RuntimeError("Output reset determinism differs")
    result["contracts"]["output_block_partition_exact"] = True
    result["contracts"]["output_reset_determinism_exact"] = True
    pair = export_pair(out,"set-output",a,b,
        "Assumed shared asymmetric soft headroom before the existing analog output filter; normalized H=1 and bias=.14. No added noise, DAC bit-depth claim, supply sag or release change.")
    result["output"] = {"native_a":am,"native_b":bm,"listening":pair,
        "raw_difference_to_A_rms_db":20*math.log10(rms(b-a)/rms(a))}
    after = {str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/"Source/DSP").glob("*")) if p.is_file()}
    if after != production:
        raise RuntimeError("Production source was altered")
    result["production_unchanged"] = True
    result["status"] = "passed"
    write_json(out / "result.json", result)
    print(json.dumps({"status":result["status"],"output":str(out),"production_unchanged":True,"sets":4}))


if __name__ == "__main__":
    main()
