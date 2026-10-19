#!/usr/bin/env python3
"""Pure constructed guard tests; never run the benchmark or read retained PCM."""
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("gated_runner", HERE / "run.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
checks = 0


def check(value):
    global checks
    checks += 1
    if not value:
        raise AssertionError("Constructed runner guard failed")


def rejected(function):
    try:
        function()
    except (ValueError, RuntimeError, FileExistsError):
        check(True)
    else:
        check(False)


def main():
    design = runner.read(runner.DESIGN)
    # Pure budget arithmetic; no allocation of large files or evidence cleanup.
    original_size, original_disk = runner.bytes_below, runner.shutil.disk_usage
    incoming = design["storage"]["scratch_maximum"]
    try:
        runner.bytes_below = lambda path: design["storage"]["maximum_new_bytes"] + 1
        runner.shutil.disk_usage = lambda path: SimpleNamespace(free=10 ** 10)
        rejected(lambda: runner.budget(design))
        runner.bytes_below = lambda path: 0
        runner.shutil.disk_usage = lambda path: SimpleNamespace(free=incoming + 64 * 1024 * 1024 - 1)
        rejected(lambda: runner.budget(design, incoming))
        runner.shutil.disk_usage = lambda path: SimpleNamespace(free=incoming + 64 * 1024 * 1024)
        check(runner.budget(design, incoming)["incoming_bytes"] == incoming)
        runner.bytes_below = lambda path: design["storage"]["maximum_new_bytes"] - incoming + 1
        rejected(lambda: runner.budget(design, incoming))
    finally:
        runner.bytes_below, runner.shutil.disk_usage = original_size, original_disk
    with tempfile.TemporaryDirectory(prefix="constructed-runner-guards-", dir=runner.BUILD) as temporary:
        directory = Path(temporary)
        approval = directory / "not-an-execution-approval.json"
        for value in ({}, {"approved": False}, {"schema": "press78.command-recording-root-execution-review.v1", "approved": True, "design_sha256": "0" * 64}):
            approval.write_text(json.dumps(value))
            rejected(lambda: runner.check_review(approval))
        value = {"schema": "press78.command-recording-root-execution-review.v1", "approved": True, "design_sha256": runner.sha(runner.DESIGN), "implementation_sha256": runner.implementation()}
        approval.write_text(json.dumps(value))
        rejected(lambda: runner.check_review(approval))
        pure = directory / "constructed-precheck.json"
        pure.write_text(json.dumps({"passed": True, "audio_processed": True}))
        value["prechecks"] = runner.record(pure)
        approval.write_text(json.dumps(value))
        rejected(lambda: runner.check_review(approval))
        pure.write_text(json.dumps({"passed": True, "audio_processed": False}))
        rejected(lambda: runner.check_review(approval))  # old expected hash
        oversized = directory / "oversized.json"
        rejected(lambda: runner.write_new(oversized, {"constructed": "x" * (8 * 1024 * 1024)}))
        check(not oversized.exists())
        oversized_cell = directory / "oversized-scores.json"
        rejected(lambda: runner.write_new(oversized_cell, {"constructed": "x" * (1024 * 1024)}))
        check(not oversized_cell.exists())
        sentinel = directory / "existing.json"
        sentinel.write_text("user/evidence sentinel\n")
        rejected(lambda: runner.write_new(sentinel, {}))
        check(sentinel.read_text() == "user/evidence sentinel\n")
    print(json.dumps({"passed": True, "checks": checks, "audio_processed": False,
                      "retained_fixture_replay": False, "constructed_inputs_only": True}))


if __name__ == "__main__":
    main()
