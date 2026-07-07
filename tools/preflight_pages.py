#!/usr/bin/env python3
"""Preflight a JumpShot static site folder before GitHub Pages deployment."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REQUIRED_FILES = [
    "index.html",
    "styles.css",
    "manifest.webmanifest",
    "icon.svg",
    "sw.js",
    "404.html",
    ".nojekyll",
    "src/main.js",
    "src/main.animation-2.js",
    "src/shooters/lebron-inspired.json",
    "src/assets/basketball-assets.json",
    "assets/players/hunyuan-lebron/player_rigged.glb",
    ".github/workflows/deploy-pages.yml",
]


def fail(message: str) -> None:
    raise RuntimeError(message)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def run(command: list[str], cwd: Path) -> None:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        fail(f"command failed: {' '.join(command)}\n{detail}")


def check_required_files(root: Path) -> None:
    missing = [item for item in REQUIRED_FILES if not (root / item).exists()]
    if missing:
        fail(f"missing required files: {', '.join(missing)}")


def check_html(root: Path) -> None:
    html = read_text(root / "index.html")
    required = [
        "JumpShot | LeBron Release Challenge",
        'name="description"',
        'property="og:title"',
        'rel="manifest"',
        'rel="icon"',
        "./src/main.animation-2.js",
        "manifest.webmanifest",
    ]
    missing = [needle for needle in required if needle not in html]
    if missing:
        fail(f"index.html missing expected deploy/share markers: {', '.join(missing)}")


def check_profile(root: Path) -> None:
    profile = json.loads(read_text(root / "src/shooters/lebron-inspired.json"))
    visual = profile.get("visual", {})
    if visual.get("primary") != "generated-scan":
        fail("ShooterProfile visual.primary must be generated-scan")
    if visual.get("scanGlb") != "./assets/players/hunyuan-lebron/player_rigged.glb":
        fail("ShooterProfile must point at player_rigged.glb")
    if visual.get("scanPrimaryOpacity") != 1:
        fail("generated scan must be fully opaque in production")


def check_runtime_source(root: Path) -> None:
    source = read_text(root / "src/main.js")
    required = [
        "playerRig.scanMixer = new THREE.AnimationMixer(scan)",
        "document.documentElement.dataset.jumpshotPlayerPhase = phase",
        "setPlayerPhase(\"jump\")",
        "setPlayerPhase(\"followThrough\")",
        "if (generatedScanIsPrimary)",
        "return;",
        "navigator.serviceWorker.register(\"./sw.js\")",
    ]
    missing = [needle for needle in required if needle not in source]
    if missing:
        fail(f"src/main.js missing production runtime markers: {', '.join(missing)}")


def check_json(root: Path) -> None:
    for path in [
        root / "manifest.webmanifest",
        root / "src/shooters/lebron-inspired.json",
        root / "src/assets/basketball-assets.json",
    ]:
        json.loads(read_text(path))


def check_service_worker(root: Path) -> None:
    source = read_text(root / "sw.js")
    required = [
        "jumpshot-v2",
        "./assets/players/hunyuan-lebron/player_rigged.glb",
        "./src/main.animation-2.js",
        "caches.open",
        "request.mode === \"navigate\"",
    ]
    missing = [needle for needle in required if needle not in source]
    if missing:
        fail(f"sw.js missing cache/offline markers: {', '.join(missing)}")


def check_rig_contract(root: Path) -> None:
    validator = root / "tools/asset-pipeline/validate_player_glb.py"
    glb = root / "assets/players/hunyuan-lebron/player_rigged.glb"
    run([sys.executable, str(validator), str(glb), "--strict"], root)


def check_payload(root: Path) -> None:
    glb = root / "assets/players/hunyuan-lebron/player_rigged.glb"
    size_mb = glb.stat().st_size / (1024 * 1024)
    if size_mb > 12:
        fail(f"player_rigged.glb is {size_mb:.1f} MB; expected <= 12 MB for Pages MVP")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Static site root to preflight")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        check_required_files(root)
        check_html(root)
        check_json(root)
        check_service_worker(root)
        check_profile(root)
        check_runtime_source(root)
        check_rig_contract(root)
        check_payload(root)
    except Exception as exc:  # noqa: BLE001 - CLI should print all preflight failures plainly.
        print(json.dumps({"ok": False, "root": str(root), "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, "root": str(root)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
