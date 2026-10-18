#!/usr/bin/env python3
"""Copy canonical Source/DSP files to a Rack device's DSP directory.

Usage: python3 Tools/sync_rack_dsp.py /path/to/Examples/Press78 [--check]

The deterministic manifest records byte lengths and SHA-256 hashes, without
machine paths or timestamps. --check is read-only and exits nonzero on drift.
Unrelated Rack files are preserved; this does not generate or modify wrappers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Source" / "DSP"
MANIFEST = "press78-source-manifest.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def snapshot() -> dict[str, bytes]:
    result = {}
    for path in sorted(SOURCE.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Canonical DSP source must not be a symlink: {path}")
        if path.is_file():
            result[path.relative_to(SOURCE).as_posix()] = path.read_bytes()
    if not result:
        raise ValueError(f"No canonical DSP files found in {SOURCE}")
    return result


def manifest_bytes(files: dict[str, bytes]) -> bytes:
    manifest = {
        "schema_version": 1,
        "source": "virtual-instrument-press78/Source/DSP",
        "destination": "DSP",
        "hash_algorithm": "sha256",
        "files": [
            {"path": name, "bytes": len(data), "sha256": sha256(data)}
            for name, data in sorted(files.items())
        ],
    }
    return (json.dumps(manifest, indent=2) + "\n").encode("utf-8")


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def differences(target: Path, files: dict[str, bytes]) -> list[str]:
    problems = []
    for name, expected in files.items():
        path = target / name
        if not path.is_file():
            problems.append(f"Missing: DSP/{name}")
        elif path.is_symlink():
            problems.append(f"Symlink is not a copied source: DSP/{name}")
        elif path.read_bytes() != expected:
            problems.append(f"Content differs: DSP/{name}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("device", type=Path, help="Rack device root, containing its DSP directory")
    parser.add_argument("--check", action="store_true", help="Check copies and manifest without writing")
    args = parser.parse_args()
    device = args.device.expanduser().resolve()
    target = device / "DSP"
    if not device.is_dir():
        parser.error(f"Rack device directory does not exist: {device}")
    if target.is_symlink() or target.resolve() == SOURCE.resolve():
        parser.error("Destination must be a separate, non-symlink DSP directory")
    try:
        files = snapshot()
        expected_manifest = manifest_bytes(files)
        manifest = target / MANIFEST
        if not args.check:
            # Check all destinations before writing any file. No deletions occur.
            for name in files:
                path = target / name
                if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != device and device in p.parents):
                    raise ValueError(f"Refusing symlink destination: {path}")
            for name, data in files.items():
                path = target / name
                if not path.is_file() or path.read_bytes() != data:
                    atomic_write(path, data)
            if snapshot() != files:
                raise ValueError("Canonical sources changed during copy; rerun to create a consistent manifest")
            atomic_write(manifest, expected_manifest)
        problems = differences(target, files)
        if not manifest.is_file():
            problems.append(f"Missing: DSP/{MANIFEST}")
        elif manifest.is_symlink() or manifest.read_bytes() != expected_manifest:
            problems.append(f"Manifest differs: DSP/{MANIFEST}")
        if problems:
            print("\n".join(problems))
            return 1
        print(f"{'Verified' if args.check else 'Synced and verified'} {len(files)} DSP files; SHA-256 manifest DSP/{MANIFEST}")
        return 0
    except (OSError, ValueError) as error:
        parser.exit(1, f"DSP sync failed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
