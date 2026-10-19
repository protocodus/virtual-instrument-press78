#!/usr/bin/env python3
"""Collect only the prospectively declared bounded original-program cases.

Local hash-matched executable images remain ignored. This is constructed-state
65C02 execution, not physical boot, elapsed-time or audio emulation. No previous
observations can be overwritten. The adjacent design predates this source.
"""
from pathlib import Path
import gzip
import hashlib
import json
import sys
import traceback

HERE = Path(__file__).resolve().parent
DESIGN = json.loads((HERE / "design-frozen.json").read_text())
OLD = Path("/Users/vojta/Dev/virtual-instrument-press78")


def digest(path):
    raw = Path(path).read_bytes()
    return {"path": str(Path(path).resolve()), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def held(ram):
    return [n for n in range(36, 97) if ram[0x24bf + 10 - (n - 31) // 6] & (32 >> ((n - 31) % 6))]


def state(b, keyed):
    m = b.mem
    return {"ranks": m[0x207e:0x208a], "notes": m[0x2120:0x212c],
            "pending": m[0x2194:0x21a0], "keyed": keyed.copy(),
            "cached": m[0x24a6:0x24b2], "delay": m[0x248e:0x249a],
            "byte21": m[0x2476:0x2482], "byte15": m[0x246a:0x2476],
            "byte22": m[0x2482:0x248e], "held": held(m),
            "effects": m[0x2588], "program": m[0x2585]}


def main():
    output = Path(sys.argv[1])
    if output.exists():
        raise SystemExit("Refuse to overwrite original-program observations")
    for expected in DESIGN["inputs"]:
        assert digest(expected["path"]) == expected, expected["path"]
    sys.path.insert(0, str(OLD / "build/opu-release-command-path-20261019"))
    import verify_release as v
    output.mkdir(parents=True)
    cases = 0
    with gzip.open(output / "prospective-observations.jsonl.gz", "wt") as stream:
        def collect(model, panel, note, fx, controls, delay_edit=None):
            nonlocal cases
            profile = v.PROFILES[model]
            b, _, _, initial_io = v.setup(profile, 0, panel)
            b.mem[0x3f7c] = controls["volume"]
            b.mem[0x3f75] = controls["fine"] & 255
            b.mem[0x208e] = controls["bend_high"]
            b.mem[0x259b] = controls["span"] & 255
            if delay_edit is not None:
                b.mem[0x2659 + 21] = delay_edit
                v.p.execute(b, 0xc6ee if model == "PSS780" else 0xc5e9)
            v.setfx(b, profile, 0, fx)
            keyed = [0] * 12
            row = {"model": model, "panel": panel, "note": note, "fx": fx,
                   "controllers": controls, "delay_edit": delay_edit,
                   "working_patch": b.mem[0x2659:0x2679].copy(),
                   "initial_ram": b.mem[0x2000:0x26a0].copy(),
                   "initial_state": state(b, keyed), "events": []}

            def event(command, action):
                before = b.mem[0x2000:0x26a0].copy()
                trace = v.capture(b, action)
                for w in trace:
                    if w["address"] == 0x208 and (w["value"] & 7) < 6:
                        pair = w["value"] & 7
                        keyed[2 * pair] = int(bool(w["value"] & 24))
                        keyed[2 * pair + 1] = int(bool(w["value"] & 96))
                row["events"].append({"command": command, "io": trace,
                    "ram_changes": [[0x2000 + i, a, z] for i, (a, z) in
                                    enumerate(zip(before, b.mem[0x2000:0x26a0])) if a != z],
                    "state": state(b, keyed)})

            try:
                event(f"on {note} 127", lambda: v.event(b, profile, 0, note))
                event("key 1", lambda: v.p.execute(b, profile["service"]))
                if delay_edit is None:
                    event("vib 32", lambda: [v.p.execute(b, 0x43b7) for _ in range(32)])
                event(f"off {note}", lambda: v.event(b, profile, 0, note, False))
                count = 255 if delay_edit is not None else 32
                event(f"vib {count}", lambda: [v.p.execute(b, 0x43b7) for _ in range(count)])
                if delay_edit is None:
                    for value in [0, 1, 63, 64, 127]:
                        event(f"cc64 {value}", lambda value=value: v.serial(b, profile, [0xb0, 64, value]))
            except Exception as error:
                row["error"] = repr(error)
                row["traceback"] = traceback.format_exc()
                stream.write(json.dumps(row, separators=(",", ":")) + "\n")
                stream.flush()
                raise
            stream.write(json.dumps(row, separators=(",", ":")) + "\n")
            stream.flush()
            cases += 1

        matrix = DESIGN["validation"]["prospective_cpu_matrix"]
        for model in matrix["models"]:
            for panel in matrix["panel_programs"]:
                for i in range(40):
                    collect(model, panel, matrix["notes"][i % 3], i % 8, matrix["controllers"][i % 5])
                print(f"Collected {model} panel {panel}: {cases} cases", flush=True)
        control = matrix["controllers"][0]
        for model in ["PSS780", "PSS680"]:
            for delay in [0, 1, 2, 11, 63, 127]:
                for vibrato in [False, True]:
                    collect(model, 99, 60, int(vibrato), control, delay)
        assert cases == 344
    result = {"passed": True, "cases": cases, "prospective_composition_cases": 320,
              "prospective_delay_cases": 24, "design": digest(HERE / "design-frozen.json"),
              "collector": digest(Path(__file__)),
              "observations": digest(output / "prospective-observations.jsonl.gz"),
              "scope": "New bounded original-program command/state observations only; no hardware, boot, elapsed-time or audio claim."}
    (output / "collection-receipt.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
