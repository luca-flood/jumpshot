# Deploy JumpShot to GitHub Pages

This folder is a complete static site. No build step is required.

## Fast Path

1. Create a GitHub repository.
2. Copy the contents of `outputs/jumpshot/` to the repository root.
3. Commit and push to `main`.
4. In GitHub, open `Settings > Pages`.
5. Set `Build and deployment` to `GitHub Actions`.
6. Run the included `Deploy JumpShot to GitHub Pages` workflow, or push to `main`.

The workflow uploads the repository root as the Pages artifact.

## Local Verification

From this workspace:

```sh
cd outputs/jumpshot
python3 -m http.server 4176
```

Then open:

```text
http://127.0.0.1:4176/
```

Expected runtime state:

- `jumpshotPrimaryVisual=generated-scan`
- `jumpshotScan=ready`
- `jumpshotScanClips=7`
- `jumpshotPlayerPhase=idle` at rest
- `jumpshotPlayerPhase=followThrough` during a released shot

## Production Asset Gate

Before publishing:

```sh
python3 tools/preflight_pages.py .
```

This verifies required Pages files, metadata, service worker caching, fallback page, runtime profile wiring, production animation markers, JSON files, payload size, and the rigged GLB contract.

Before publishing a new player GLB directly:

```sh
python3 tools/asset-pipeline/validate_player_glb.py \
  assets/players/hunyuan-lebron/player_rigged.glb \
  --strict --pretty
```

The current generated LeBron mesh passes with `animationReady: true`.

## Current Artifact

The current Pages-ready package is available at:

```text
dist/jumpshot-pages/
dist/jumpshot-pages.zip
```

This workspace is not currently a git repository and does not have a GitHub remote configured. The installed GitHub connector can see `RussDT/hoople-highlight-lab` and `anthonyeft/AAYL`, but no JumpShot repository. Publish live by creating or choosing a target repo, then copying `dist/jumpshot-pages/` to the repo root and enabling the included Pages workflow.
