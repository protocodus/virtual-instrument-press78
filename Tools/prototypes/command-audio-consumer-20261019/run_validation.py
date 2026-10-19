#!/usr/bin/env python3
"""Reproduce synthetic command/audio integration checks; never writes WAVs.

Frozen scope: design-frozen.json. This does not validate YM3420 audio laws, run
original firmware, load recordings, or change production/default/host state.
Every output directory must be new, preserving failures and earlier receipts.
"""
import argparse
import hashlib
import json
from pathlib import Path
import os
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def binding(path):
    data = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--verify-inputs-only", action="store_true",
                        help="Check frozen hashes and write bindings without compiling/running DSP.")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    design = json.loads((HERE / "design-frozen.json").read_text())
    inputs = [HERE / "design-frozen.json", HERE / "CommandAudioConsumer.h",
              HERE / "consumer_test.cpp", Path(__file__).resolve()]
    original_root = Path(design["inputs"][0]["path"]).parents[2]
    inputs += [ROOT / Path(row["path"]).relative_to(original_root) for row in design["inputs"]]
    # Include the actual unchanged transitive chorus profile as well.
    inputs += [ROOT / "Source/DSP/RecordedChorusProfile.h"]
    rows = [binding(path) for path in dict.fromkeys(inputs)]
    (output / "source-bound-before-execution.json").write_text(
        json.dumps({"chronology": "Before compilation/execution; no WAV output requested.",
                    "sources": rows}, indent=2) + "\n")
    receipt = {"classification": "Synthetic integration only; not audible silicon validation.",
               "runs": [], "status": "running", "frozen_inputs_checked": []}
    try:
        for expected in design["inputs"]:
            path = ROOT / Path(expected["path"]).relative_to(original_root)
            actual = binding(path)
            if actual["bytes"] != expected["bytes"] or actual["sha256"] != expected["sha256"]:
                raise RuntimeError("Frozen input mismatch before compilation: " + actual["path"])
            receipt["frozen_inputs_checked"].append(actual)
        if args.verify_inputs_only:
            receipt["status"] = "inputs-verified-only; no compilation, DSP execution or WAV output"
            return
        for name, flags in (("opt", ["-O2"]),
                            ("san", ["-O1", "-g", "-fsanitize=address,undefined",
                                     "-fno-omit-frame-pointer"])):
            binary = output / ("test-" + name)
            command = ["clang++", "-std=c++17", *flags, "-Wall", "-Wextra",
                       "-Werror", "-pedantic", str(HERE / "consumer_test.cpp"),
                       "-o", str(binary)]
            with (output / ("compile-" + name + ".log")).open("wb") as stream:
                subprocess.run(command, cwd=ROOT, stdout=stream,
                               stderr=subprocess.STDOUT, check=True)
            env = dict(os.environ)
            if name == "san":
                env["ASAN_OPTIONS"] = "detect_leaks=0"
            with (output / ("test-" + name + ".json")).open("wb") as out, \
                    (output / ("test-" + name + ".stderr")).open("wb") as err:
                subprocess.run([str(binary)], cwd=ROOT, env=env, stdout=out,
                               stderr=err, check=True)
            receipt["runs"].append({"name": name, "command": command,
                                    "result": json.loads((output / ("test-" + name + ".json")).read_text())})
        if receipt["runs"][0]["result"] != receipt["runs"][1]["result"]:
            raise RuntimeError("Optimized and sanitized results differ; retained both.")
        receipt["status"] = "pass"
    except BaseException as error:
        receipt["status"] = "failure"
        receipt["error"] = repr(error)
        raise
    finally:
        receipt["artifacts"] = [binding(path) if path.is_relative_to(ROOT)
                                else {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                                for path in output.iterdir() if path.is_file()]
        (output / "validation.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": "pass", "output": str(output)}))


if __name__ == "__main__":
    main()
