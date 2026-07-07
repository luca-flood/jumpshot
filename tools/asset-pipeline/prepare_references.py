#!/usr/bin/env python3
"""Validate local reference images for a JumpShot player asset run."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    manifest_path = Path(sys.argv[1] if len(sys.argv) > 1 else "manifest.lebron-inspired.json")
    manifest = json.loads(manifest_path.read_text())
    root = manifest_path.parent
    reference_dir = (root / manifest["references"]["dir"]).resolve()

    missing = []
    present = []
    for name in manifest["references"]["required"]:
      path = reference_dir / name
      if path.exists():
        present.append(path)
      else:
        missing.append(path)

    optional = [reference_dir / name for name in manifest["references"]["optional"]]
    print(f"Reference directory: {reference_dir}")
    print(f"Required present: {len(present)}/{len(manifest['references']['required'])}")
    for path in present:
        print(f"  ok: {path.name}")
    for path in optional:
        if path.exists():
            print(f"  optional ok: {path.name}")

    if missing:
        print("Missing required references:")
        for path in missing:
            print(f"  missing: {path.name}")
        return 2

    print("References are ready for offline Hunyuan3D/TRELLIS generation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
