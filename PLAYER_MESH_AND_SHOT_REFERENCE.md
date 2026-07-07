# Player Mesh and Shot Reference

Date: 2026-07-06

## Local Source Inventory

Image references:

- `/Users/lucaflood/Downloads/nba_images_players/lebron/`
- `/Users/lucaflood/Downloads/nba_images_players/shai/`
- `/Users/lucaflood/Downloads/nba_images_players/pg/`

Hunyuan3D generated meshes:

- `/Users/lucaflood/Hunyuan3D-2.1/generated_meshes/lebron/lebron1.glb` - 9.92 MB, raw bounds `1.97w x 2.00h x 0.28d`
- `/Users/lucaflood/Hunyuan3D-2.1/generated_meshes/lebron/lebron2.glb` - 9.47 MB, raw bounds `1.91w x 1.99h x 1.02d`
- `/Users/lucaflood/Hunyuan3D-2.1/generated_meshes/lebron/lebron4.glb` - 22.67 MB, raw bounds `1.66w x 1.99h x 1.57d`
- `/Users/lucaflood/Hunyuan3D-2.1/generated_meshes/lebron/lebron5.glb` - 9.98 MB, raw bounds `1.35w x 1.99h x 0.32d`
- `/Users/lucaflood/Hunyuan3D-2.1/generated_meshes/lebron/lebron6.glb` - 5.69 MB, raw bounds `1.10w x 2.00h x 0.48d`
- `/Users/lucaflood/Hunyuan3D-2.1/generated_meshes/shai/shai1.glb` - 21.07 MB, raw bounds `2.00w x 1.99h x 1.33d`

## Mesh Decision

Selected mesh: `lebron6.glb`

Reasons:

- Lowest payload among the plausible generated outputs.
- Best silhouette in the browser preview when scaled against the JumpShot ball and rim.
- Shai1 and most other LeBron generations render as large blocky/depth-heavy slabs in the preview, which makes them poor runtime candidates without cleanup.
- LeBron6 is still a raw source mesh: single mesh, no useful skeleton, no animation clips, and a hands-on-hips pose. It should not be treated as final game-ready character art.

Runtime integration:

- Copied to `assets/players/hunyuan-lebron/player.glb`.
- Loaded as the primary visible player in `generated-scan` mode.
- Normalized to `2.1m` player height so it matches the `0.24m` ball radius and `3.05m` rim height in JumpShot scale.
- The generated mesh is opaque, centered on the playable character, shadow-casting, and decorated with runtime `JAMES`/`23` uniform decals.
- The old procedural/block player is hidden in this mode. The lightweight modular rig can still load invisibly as a gameplay/phase driver until a true skinned LeBron GLB exists.
- The placeholder remains hidden during generated-scan loading/failure, so the app reports a mesh-load problem instead of showing the block/procedural human.
- The scan root participates in slow-motion dip, rise, high-release lean, fade drift, release stretch, idle breathing, and landing settle.
- Browser/runtime proof from the previous scan pass: `scan=ready`, normalized height `2.1m`, 120 FPS, p95 frame about `9.0-9.6 ms`.
- Current local-browser verification of the primary-scan patch was blocked by preview connectivity (`127.0.0.1:4174` timed out from the app browser), but `node --check` and JSON validation pass.
- Rig audit artifact: `reference/hunyuan-lebron-rig-audit.json`. The current LeBron6 scan has 1 mesh node, 0 skins, 0 skinned mesh nodes, 0 animation clips, and no runtime anchors.
- Rigged audit artifact: `reference/hunyuan-lebron-rigged-audit.json`. The generated rig bridge output has 1 skin, 17 joints, inverse bind matrices, 1 skinned mesh node, all runtime anchors, and all 7 required animation clips.

Generated JumpShot reference artifacts:

- `reference/hunyuan-mesh-candidate-bounds.json`
- `reference/lebron-shot-slowmo-2_15x.mp4`
- `reference/lebron-shot-slowmo-contact.jpg`

## LeBron Shot Reference Characterization

Local reference clips/contact sheets found:

- `/Users/lucaflood/basketball_ai/hoople-highlight-lab/out/highlights/generalized-fresh-mixed-20260702/autocrop-clips/01-rank-01-lebron-james-shot-22500362-664.basketball-v1.square.contact_sheet.jpg`
- `/Users/lucaflood/basketball_ai/hoople-highlight-lab/out/highlights/generalized-fresh-mixed-20260702/autocrop-clips/01-rank-01-lebron-james-shot-22500362-664.basketball-v1.square.mp4`
- `/Users/lucaflood/basketball_ai/data/output/highlights/production-unique-10-20260620/final/01-lebron-james-22401055-634.square.mp4`
- `/Users/lucaflood/basketball_ai/data/output/highlights/production-unique-10-20260620/final/02-lebron-james-42200154-681.square.mp4`

General motion notes used for the runtime animation:

- LeBron often shoots from a strong, upright base rather than a tiny guard-style compact release.
- Gather has a visible load/dip, then a high set point with shoulders squared late.
- Pull-up and fade variants create separation by moving the center of mass backward or upward while the guide hand drops away.
- Follow-through should read as high, strong, and slightly held, with a visible wrist snap.
- Fade/deep variants should exaggerate backward drift and left-leg kick more than a normal set shot.

Runtime animation decisions:

- `slowMotionScale: 2.15`, inside the requested 1.5x-3x range.
- Camera inspection zoom now eases in during active shots: lower camera height, closer z-distance, narrower FOV, and higher look target to focus on the release.
- Added shot classification: `Set`, `Pull-Up`, `Drift`, `Fade`, `Deep`.
- Shot type affects camera push, root fade, leg kick, feedback text, and scan motion.
- Modular limbs keep the shot readable while the Hunyuan scan validates the selected generated mesh in-game.

Updated primary-scan runtime decisions:

- `visual.primary: "generated-scan"` makes LeBron6 the rendered character instead of a side-by-side research layer.
- `scanPrimaryOpacity: 1` keeps the mesh fully visible through gather, release, and follow-through.
- The scan carries whole-body motion until the offline rig is ready. This is a deliberate bridge, not the final character-animation solution.

Required Blender pass for production-ready animation:

1. Clean the LeBron6 generated mesh: remove generation artifacts, separate body/clothing/shoes if feasible, and reduce the mesh into game-friendly topology.
2. Retopologize and unwrap the character so the jersey/shorts can use reusable team materials and dynamic decals instead of baked one-off texture identity.
3. Rig to a standard humanoid skeleton compatible with Mixamo/custom clips.
4. Skin weights for shoulders, elbows, wrists, fingers, hips, knees, ankles, and neck/head.
5. Author or retarget named animation clips: `idle`, `dribble_idle`, `gather`, `jump`, `release`, `follow_through`, and `land`.
6. Export compressed GLB and update the ShooterProfile release-frame metadata so the shot meter, ball release, camera push, green flash, and swish feedback line up with the exact release pose.
7. Run `tools/asset-pipeline/validate_player_glb.py --strict` and ship only when `animationReady` is `true`.

Autorig bridge now available:

No-Blender runtime rig bridge:

```sh
python3 outputs/jumpshot/tools/asset-pipeline/rig_hunyuan_scan_glb.py \
  outputs/jumpshot/assets/players/hunyuan-lebron/player.glb \
  outputs/jumpshot/assets/players/hunyuan-lebron/player_rigged.glb
```

This is the current runtime target. It preserves the generated LeBron mesh and injects a humanoid skeleton, weighted skin, anchors, and named jumpshot clips directly into the GLB.

Blender bridge:

```sh
blender --background \
  --python outputs/jumpshot/tools/asset-pipeline/blender_autorig_lebron_scan.py \
  -- outputs/jumpshot/assets/players/hunyuan-lebron/player.glb \
     outputs/jumpshot/assets/players/hunyuan-lebron/player_rigged.glb
```

This script creates a first-pass humanoid armature, automatic weights, anchors, and named classic-jumpshot clips for the generated LeBron scan. It is not a substitute for final artist cleanup, but it is the concrete path from current raw scan to a skinned GLB the Three.js `AnimationMixer` can drive.
