#!/usr/bin/env python3
"""Frozen no-CC64 regression check for the optional original release pedal.

Uses retained local research inputs. Exact complete-WAV identity proves that
the existing four-map recording scores and A/Bs are unchanged; it does not
measure pedal behavior on hardware. Core/controller tests cover that separately.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def record(path):
    path = Path(path).resolve()
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def verify(item):
    assert sha(item["path"]) == item["sha256"], item["path"]


def freeze(out):
    assert not out.exists(), "Use a fresh directory; keep earlier experiments"
    source = ROOT / "build/key-level-b13-20261019/design-frozen-v2.json"
    prior = read(source)
    verify({"path": prior["baseline"]["prior_b12_result"],
            "sha256": prior["baseline"]["prior_result_sha256"]})
    fixture = Path(prior["baseline"]["prior_b12_result"]).parent / "snapshots/HardwareSequencePressure.cpp"
    out.mkdir(parents=True)
    design = {"schema": "press78.sustain-no-CC64-regression.v1",
              "source_design": record(source), "runner": record(Path(__file__)),
              "fixture": record(fixture), "baseline": prior["baseline"],
              "render": prior["render"], "maps": prior["maps"],
              "windows": prior["windows"], "bank": prior["bank"],
              "laws": {"Legacy": 0, "Original": 1},
              "required_gate": "All eight complete WAVs exactly equal their b12 Original baseline",
              "no_timing_parameter_or_window_fit": True,
              "maximum_retained_new_WAV_bytes": 650000000,
              "scope": "No CC64 events. Tests recording-regression compatibility, not hardware pedal fidelity."}
    for m in design["maps"]:
        verify(m["events"])
        verify(m["expected_legacy_audio"])
    verify(design["bank"])
    write(out / "design-frozen.json", design)
    print(json.dumps(record(out / "design-frozen.json"), indent=2))


def run(out, source):
    assert not (out / "candidate-bound.json").exists(), "Never overwrite an attempted run"
    design = read(out / "design-frozen.json")
    verify(design["runner"])
    verify(design["fixture"])
    verify(design["bank"])
    shutil.copytree(source, out / "candidate-source")
    source = out / "candidate-source"
    fixture = Path(design["fixture"]["path"]).read_text()
    assert fixture.count("if(argc!=7)") == 1
    assert fixture.count("press78::Controls c;c.masterGain=1.;") == 1
    fixture = fixture.replace("if(argc!=7)", "if(argc!=8)").replace(
        "press78::Controls c;c.masterGain=1.;",
        "press78::Controls c;c.pitchModel=1;c.sustainMode=std::stoi(argv[7]);c.midiPitchBend=-1;c.masterGain=1.;")
    runner = out / "SustainSequence.cpp"
    runner.write_text(fixture)
    binding = {"design": record(out / "design-frozen.json"),
               "source": {p.name: sha(p) for p in source.iterdir() if p.is_file()},
               "fixture": record(runner), "status": "Bound before compilation or audio"}
    write(out / "candidate-bound.json", binding)
    exe = out / "sustain_sequence"
    command = ["c++", "-std=c++17", "-O2", "-I", str(source), str(runner),
               str(source / "Press78Engine.cpp"), "-o", str(exe)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    renders = []
    for m in design["maps"]:
        verify(m["events"])
        verify(m["expected_legacy_audio"])
        folder = out / m["id"]
        folder.mkdir()
        for name, mode in design["laws"].items():
            audio, pressure = folder / (name + ".wav"), folder / (name + "-pressure.csv")
            cmd = [str(exe), m["events"]["path"], str(audio), str(design["render"]["frames"]),
                   "48000", "recorded", str(pressure), str(mode)]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            detail = json.loads(result.stdout)
            assert detail["events"] == 3622 and detail["latency_samples"] == 32
            identity = sha(audio) == m["expected_legacy_audio"]["sha256"]
            renders.append({"map": m["id"], "mode": name, "command": cmd,
                            "detail": detail, "audio": record(audio), "pressure": record(pressure),
                            "complete_WAV_equal_b12": identity,
                            "duplicate_deleted_after_exact_identity": identity})
            if identity:
                audio.unlink()
            assert sum(p.stat().st_size for p in out.rglob("*.wav")) <= design["maximum_retained_new_WAV_bytes"]
            write(out / "render-progress.json", renders)
            print(m["id"], name, identity, flush=True)
    assert binding["source"] == {p.name: sha(p) for p in source.iterdir() if p.is_file()}
    result = {"schema": design["schema"], "design": binding["design"],
              "candidate_binding": record(out / "candidate-bound.json"),
              "compile_command": command, "executable": record(exe), "renders": renders,
              "passed": len(renders) == 8 and all(r["complete_WAV_equal_b12"] for r in renders),
              "scope": design["scope"], "no_automatic_adoption": True}
    write(out / "result.json", result)
    print(json.dumps({"passed": result["passed"], "result": record(out / "result.json")}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "run"))
    parser.add_argument("--output", type=Path, default=ROOT / "build/sustain-b13-20261019/no-CC64")
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    if args.action == "freeze":
        freeze(args.output.resolve())
    else:
        if args.source is None:
            parser.error("run requires --source")
        run(args.output.resolve(), args.source.resolve())


if __name__ == "__main__":
    main()
