# JumpShot Progress and Benchmark

Date: 2026-07-06

## Benchmark Snapshot

- Browser runtime: local static server at `http://127.0.0.1:4173/outputs/jumpshot/`
- Render surface: one Three.js canvas
- Physics: Rapier loaded and marked `ready`
- Game loop benchmark: 120 FPS reported by the internal loop counter on this display
- p95 frame time: 9.7-9.8 ms after the latest asset/challenge pass
- Quick bad-release test: `0/1`, score `0`, feedback `Short`
- Daily mode test: deterministic daily key active, 8-shot counter visible, seeded goal visible (`Win the wings (15+ pts)` on 2026-07-06)
- 15s Threes test: mode activates and countdown advances
- Hunyuan scan test: selected LeBron6 mesh loads in-game as `scan=ready`, normalized to `2.1m`, and quick-release scoring still holds at 120 FPS
- Slow-motion reference artifacts: generated `reference/lebron-shot-slowmo-2_15x.mp4`, `reference/lebron-shot-slowmo-contact.jpg`, and `reference/hunyuan-mesh-candidate-bounds.json`
- Slow-motion zoom patch: syntax/static validation passes; final browser capture for this exact patch was blocked by the local browser security policy for `127.0.0.1:4173`
- Console: no app errors observed; Rapier emits a non-blocking init deprecation warning from the CDN module

## Deliverable 1: Realistic Assets and Lightweight Physics

Progress so far:

- Court, ball, hoop, backboard, rim, and net are runtime Three.js meshes with static/dynamic Rapier physics where it matters.
- Ball is a dynamic body with continuous collision detection and analytical launch velocity.
- Rim, backboard, floor, pole/neck, and net anchors are static colliders.
- Miss trajectory is now visibly driven by shot-meter error, and non-green shots are forced misses.

Three improvements completed this pass:

1. Added more readable half-court details: restricted arc, lane/hash markings, hoop stanchion, backboard padding, and richer ball seams.
2. Added lightweight net anchor colliders plus strand-level net animation instead of cloth simulation.
3. Added procedural contact audio and benchmark counters for swish, rim, glass, and floor events.

Latest follow-up improvements:

1. Added `src/assets/basketball-assets.json` as the runtime asset manifest for court/ball/hoop/backboard/net tuning and future compressed GLB slots.
2. Moved material and Rapier tuning for court, ball, rim, backboard, floor, and net anchors out of hardcoded scene values and into the manifest.
3. Documented the environment asset manifest in `ASSET_PIPELINE.md` so future GLB/baked texture replacement has a clear contract.

Hunyuan mesh follow-up:

1. Found the local `nba_images_players` references and Hunyuan outputs.
2. Benchmarked LeBron1/2/4/5/6 and Shai1 by payload, raw bounds, and browser preview.
3. Selected LeBron6 as the best current raw mesh and brought it into the game as a translucent scan layer scaled against the ball/rim.
4. Promoted LeBron6 to the primary rendered player in `generated-scan` mode: the procedural/block player is hidden, the generated mesh is opaque, centered on the playable character, shadow-casting, and decorated with runtime `JAMES`/`23` uniform decals.
5. Added whole-body scan shot motion for the raw mesh: gather dip, high-release lean, fade drift, release stretch, idle breathing, landing settle, and debug fields for `primaryVisual`, `placeholderVisible`, `rigRootVisible`, and `visualPhase`.
6. Added `tools/asset-pipeline/validate_player_glb.py`, a no-dependency GLB contract validator for skins, anchors, and named animation clips.
7. Audited the current Hunyuan LeBron6 asset in `reference/hunyuan-lebron-rig-audit.json`: it has 1 mesh node, 0 skins, 0 skinned mesh nodes, 0 animations, and is not animation-ready yet.
8. Added `tools/asset-pipeline/rig_hunyuan_scan_glb.py`, a no-Blender rigging bridge that preserves the generated scan mesh and injects JOINTS_0/WEIGHTS_0, a 17-joint humanoid skin, runtime anchors, and 7 named LeBron-style clips.
9. Generated `assets/players/hunyuan-lebron/player_rigged.glb` and validated it in `reference/hunyuan-lebron-rigged-audit.json`: `animationReady: true`, 1 skin, 17 joints, inverse bind matrices, 1 skinned mesh node, and all clips/anchors present.
10. Updated the ShooterProfile so the visible generated LeBron mesh loads `player_rigged.glb`, and updated the runtime scan loader to create an `AnimationMixer` for generated-scan clips.
11. Browser verification on `http://127.0.0.1:4175/`: `jumpshotPrimaryVisual=generated-scan`, `jumpshotScan=ready`, `jumpshotScanClips=7`, `jumpshotScanHeight=2.1`, `jumpshotPhysics=ready`, feedback `LeBron mesh ready`, and a key-triggered shot reached `jumpshotVisualPhase=release`.
12. Updated runtime phase sequencing so charge/release now drives the generated LeBron mesh through `gather`, `jump`, `release`, `follow_through`, and `land` instead of skipping directly from gather to release.
13. Regenerated `player_rigged.glb` with root translation channels for gather dip, jump lift, release rise, backward fade, follow-through settle, and landing. Strict validation still passes after the new channels.
14. Browser verification on `http://127.0.0.1:4176/`: initial runtime reported `jumpshotClip=idle`, `jumpshotPlayerPhase=idle`, `jumpshotScan=ready`, and `jumpshotScanClips=7`; a key-triggered shot reported `jumpshotClip=follow_through`, `jumpshotPlayerPhase=followThrough`, then returned to `idle` after the miss resolved.
15. Prepared the shareable GitHub Pages static site: metadata, web manifest, SVG icon, share text with page URL, `.nojekyll`, and `.github/workflows/deploy-pages.yml`.
16. Created a Pages-ready deploy package at `dist/jumpshot-pages/` and `dist/jumpshot-pages.zip`; packaged build verified with `jumpshotPrimaryVisual=generated-scan`, `jumpshotScan=ready`, `jumpshotScanClips=7`, `jumpshotPhysics=ready`, title/description/manifest present, and strict rigged-GLB validation passing.
17. Live publication is waiting on a target GitHub repository. This workspace is not a git repo and `gh` is not installed, so there is currently no authenticated local remote to push Pages to.
18. Added `tools/preflight_pages.py`, a single-command release gate for Pages packages. It checks required static files, share metadata, production profile wiring, runtime animation markers, JSON validity, payload size, and strict rigged-GLB validation. Both `outputs/jumpshot` and `dist/jumpshot-pages` pass.
19. Strengthened strict GLB validation: production-ready now also requires named humanoid joints, non-empty animation channels, and root translation motion for `gather`, `jump`, `release`, `follow_through`, and `land`. `player_rigged.glb` passes the stronger gate.

Research notes:

- Kenney assets are a useful CC0 placeholder/source pool for UI and light sports assets: https://kenney.nl/assets/sports-pack
- Poly Haven is a useful CC0 material/HDRI source for court/arena lighting and PBR polish: https://polyhaven.com/license
- Rapier's JavaScript character controller is the best near-term physics-control reference: https://rapier.rs/docs/user_guides/javascript/character_controller/

## Deliverable 2: Overtly Unique LeBron-Style Jumpshot

Progress so far:

- ShooterProfile now has signature animation parameters.
- The LeBron-style profile has a bigger gather dip, high set point, backward fade, left-leg kick, right-elbow tuck, guide-hand drop, and wrist snap.
- The same signature silhouette now affects both the loaded GLB player and fallback procedural player.

Three improvements completed this pass:

1. Added a `signature` block to the shooter profile so shot identity can be data-driven per player.
2. Kept the player airborne through release/follow-through instead of snapping immediately back to the floor.
3. Added stronger LeBron-style silhouette cues: backward fade, left-leg kick, shoulder turn, high set point, and wrist snap.

Latest follow-up improvements:

1. Added release-time shot classification: Set, Pull-Up, Drift, Fade, and Deep.
2. Shot classification now changes feedback text, camera push, fade amount, and leg-kick scale.
3. The animation path now uses both shooter signature data and situational shot type data, making the same shooter feel different by context.

Hunyuan/slow-motion follow-up:

1. Added `slowMotionScale: 2.15` to the LeBron profile, inside the requested 1.5x-3x range.
2. Slowed the release/follow-through limb animation and generated scan root motion so the shot can be inspected longer.
3. Characterized the local LeBron reference clips/contact sheet in `PLAYER_MESH_AND_SHOT_REFERENCE.md` and mapped the notes to gather dip, high set point, backward fade, guide-hand drop, wrist snap, and leg kick.
4. Added a shot-inspection camera zoom: closer camera, lower height, narrower FOV, and higher release-focused look target during active slow-motion shots.
5. Updated the generated LeBron scan to stay fully visible during the shot instead of fading out, so the visible character now carries the slow-motion jumper.

Current limitation:

- The original Hunyuan LeBron6 GLB is still a raw static scan, but the new `player_rigged.glb` bridge asset now passes the runtime animation contract. Remaining production polish is visual fidelity: hand-authored/retargeted skin weights, better limb separation, fingers, cloth cleanup, and final animation polish.
- The generated-scan runtime path now keeps the placeholder hidden even while the scan is loading or if it errors, so the Three.js block human should not reappear in the LeBron mesh mode.

Reference notes:

- Public basketball references identify the pull-up jumper as a core move used by LeBron James and describe fadeaway mechanics as a backward jump that creates separation.
- Jump-shot form references emphasize balance, elbow alignment, high arc, and follow-through.
- Exact clip acquisition still needs a licensed/offline reference pass; current implementation uses public mechanics references and does not ship copyrighted footage.

## Deliverable 3: Modes, Daily Features, and Static Backend Layer

Progress so far:

- Practice, Daily, and 15s Threes modes are available in the HUD.
- Daily spots are deterministic from the date key.
- Local best results are stored in `localStorage`, which fits GitHub Pages hosting.

Three improvements completed this pass:

1. Added a visible Best panel that formats score, makes/shots, and streak for the active mode.
2. Added local best persistence for Practice, Daily, and 15s Threes with streak-aware comparison.
3. Added a Share button that uses Web Share when available or clipboard copy as fallback.

Latest follow-up improvements:

1. Added a visible Goal panel next to Best/Share.
2. Added deterministic daily challenge generation from the date key, including labels and target scores.
3. Saved/shareable result payloads now include daily challenge metadata and goal-clear status.

## Next Three Improvements

1. Rig LeBron6 in Blender to a standard humanoid skeleton, retopologize/skin the mesh, and export a skinned GLB with named `idle`, `dribble_idle`, `gather`, `jump`, `release`, `follow_through`, and `land` clips.
2. Convert the current whole-body runtime jumper into proper animation clips with release-frame metadata, then bind ball release, camera push, green flash, and feedback to that frame.
3. Replace the procedural court/hoop/ball with compressed GLB assets and baked textures using the new manifest slots.
