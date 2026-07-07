# JumpShot

JumpShot is a lightweight browser basketball game built with Three.js. The current build focuses on a shareable core loop: move around the court, hold to load a LeBron-style release, let go near the green window, and watch the shot resolve with a rigged generated player mesh.

## Play

Open `index.html` from a local static server.

```sh
python3 -m http.server 4173
```

Then visit `http://localhost:4173/`.

Controls:

- `WASD`: move
- `Shift`: sprint
- `Space` or mouse/touch hold: shoot

## GitHub Pages

This folder is static and includes a GitHub Pages workflow. To host it:

1. Put the contents of `outputs/jumpshot` at the root of a GitHub repository, or serve that folder as the Pages source.
2. In GitHub, open `Settings > Pages`.
3. Set `Build and deployment` to `GitHub Actions`.
4. Push to `main` or run the included `Deploy JumpShot to GitHub Pages` workflow.

No build step is required.

See `DEPLOY_GITHUB_PAGES.md` for the exact deployment and verification checklist.

Preflight before publishing:

```sh
python3 tools/preflight_pages.py .
```

## Current Scope

- Three.js half-court scene
- Rigged generated LeBron mesh loaded as the primary visible player
- Seven generated player animation clips: `idle`, `dribble_idle`, `gather`, `jump`, `release`, `follow_through`, `land`
- GitHub Pages-ready static app with metadata, manifest, service worker cache, and fallback page
- WASD movement and sprinting
- Simple dribble math while moving
- Hold/release shot meter
- Data-driven player shooting profile
- Basic make/miss, score, streak, and timing feedback
- Practice, Daily, and 15s Threes modes with local bests and share text
- Lightweight Rapier ball physics with tuned contact feedback
- Data-driven basketball asset manifest for court/ball/hoop/net tuning
- Seeded daily challenge objectives
- Selected Hunyuan LeBron mesh scaled against ball/rim proportions and validated as a skinned GLB runtime asset

## Progress Report

See `PROGRESS_BENCHMARK.md` for the latest benchmark snapshot, completed improvements, research notes, and next priorities.

See `PLAYER_MESH_AND_SHOT_REFERENCE.md` for the local Hunyuan mesh inventory, selected mesh decision, and LeBron shot characterization.

Reference artifacts from the current player pass live in `reference/`:

- `lebron-shot-slowmo-2_15x.mp4`
- `lebron-shot-slowmo-contact.jpg`
- `hunyuan-mesh-candidate-bounds.json`
- `hunyuan-lebron-rigged-audit.json`

## Asset Pipeline

The LeBron-inspired asset pipeline starts at `ASSET_PIPELINE.md`.

Runtime profile:

- `src/shooters/lebron-inspired.json`

Reference image folder:

- `assets/players/lebron-inspired/source/references/`

Validation:

```sh
cd outputs/jumpshot/tools/asset-pipeline
python3 prepare_references.py manifest.lebron-inspired.json
```

Generate the current rigged Hunyuan LeBron runtime GLB:

```sh
python3 outputs/jumpshot/tools/asset-pipeline/rig_hunyuan_scan_glb.py \
  outputs/jumpshot/assets/players/hunyuan-lebron/player.glb \
  outputs/jumpshot/assets/players/hunyuan-lebron/player_rigged.glb
```

Validate the runtime player contract:

```sh
python3 outputs/jumpshot/tools/asset-pipeline/validate_player_glb.py \
  outputs/jumpshot/assets/players/hunyuan-lebron/player_rigged.glb \
  --strict --pretty
```
