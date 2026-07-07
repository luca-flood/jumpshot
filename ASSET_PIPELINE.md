# JumpShot Asset Pipeline

This pipeline keeps generation offline and ships only optimized GLB assets to GitHub Pages.

## Runtime Visual Tiers

1. Placeholder: procedural low-poly player, used for gameplay work and fallback.
2. MVP rigged: stylized humanoid GLB with modular body, head/hair, jersey, shorts, socks, shoes, and accessories.
3. Higher-quality generated: refined Hunyuan3D/TRELLIS-derived assets after Blender cleanup, retopology, UVs, texture baking, LODs, and rigging.

## LeBron-Inspired Test

Put local reference images in:

`assets/players/lebron-inspired/source/references/`

Required filenames:

- `front_full_body.png`
- `side_full_body.png`
- `back_full_body.png`

Optional:

- `head_front.png`
- `shoe_detail.png`
- `jersey_detail.png`

Validate references:

```sh
cd outputs/jumpshot/tools/asset-pipeline
python3 prepare_references.py manifest.lebron-inspired.json
```

The current in-game test asset is a handcrafted lightweight GLB, generated locally to prove the runtime path before heavier Hunyuan3D/TRELLIS work:

```sh
python3 outputs/jumpshot/tools/asset-pipeline/generate_lebron_style_glb.py
```

Output:

`assets/players/lebron-inspired/player.glb`

## Generation Options

### Hunyuan3D

Use Hunyuan3D for raw shape and texture generation. The Hunyuan3D-2 repo documents an image-conditioned API that returns a mesh object, and the project includes Blender tooling for generation workflows.

Recommended first pass:

```py
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
    "tencent/Hunyuan3D-2mini"
)
mesh = pipeline(image="front_full_body.png")[0]
mesh.export("raw_player.glb")
```

Use the generated output as source material only.

### TRELLIS

Use TRELLIS as an alternate raw source mesh generator. Compare it against Hunyuan3D for silhouette, garment readability, and cleanup effort. Prefer the asset that is easiest to retopologize and rig, not the prettiest raw mesh.

## Blender Cleanup

1. Import the raw GLB/OBJ.
2. Delete artifacts and fused geometry.
3. Split into `Body`, `Head`, `Hair`, `Jersey`, `Shorts`, `Socks`, `Shoes`, `Accessories`.
4. Retopologize or decimate to the target triangle budget.
5. Unwrap UVs and bake base color, normal, and optional ORM maps.
6. Rig to a Mixamo-compatible humanoid skeleton.
7. Add empty anchors named `JerseyNumberAnchor`, `JerseyNameAnchor`, and `BallReleaseAnchor`.
8. Create clips: `idle`, `dribble_idle`, `gather`, `jump`, `release`, `follow_through`, `land`.
9. For a first-pass generated-mesh rig without Blender, run the no-dependency GLB rigging bridge:

```sh
python3 outputs/jumpshot/tools/asset-pipeline/rig_hunyuan_scan_glb.py \
  outputs/jumpshot/assets/players/hunyuan-lebron/player.glb \
  outputs/jumpshot/assets/players/hunyuan-lebron/player_rigged.glb
```

This preserves the Hunyuan scan mesh, appends skin weights, creates a 17-joint humanoid skeleton, adds the required runtime anchors, and writes the named LeBron-style jumpshot clips. The generated output is the current runtime target for the LeBron mesh path.

10. If Blender is available, run the LeBron scan autorig script for an artist-editable bridge:

```sh
blender --background \
  --python outputs/jumpshot/tools/asset-pipeline/blender_autorig_lebron_scan.py \
  -- outputs/jumpshot/assets/players/hunyuan-lebron/player.glb \
     outputs/jumpshot/assets/players/hunyuan-lebron/player_rigged.glb
```

The autorig script normalizes the raw generated mesh to JumpShot scale, creates a humanoid armature, adds the required runtime anchors, authors named LeBron-style jumpshot clips, binds the mesh with automatic weights, and exports a GLB. This is the bridge from raw scan to runtime-valid animation asset; it should still be artist-polished before final ship.

11. Export artist-cleaned GLB:

```sh
blender lebron-inspired-cleanup.blend --background \
  --python tools/asset-pipeline/blender_export_runtime.py \
  -- assets/players/lebron-inspired/player.glb
```

12. Optimize with glTF Transform or equivalent compression:

```sh
gltf-transform optimize assets/players/lebron-inspired/player.glb \
  assets/players/lebron-inspired/player.glb \
  --compress draco --texture-compress webp
```

13. Validate the runtime animation contract:

```sh
python3 outputs/jumpshot/tools/asset-pipeline/validate_player_glb.py \
  outputs/jumpshot/assets/players/hunyuan-lebron/player_rigged.glb \
  --strict --pretty
```

The strict validator must pass before a generated player is considered production animation-ready. It checks for:

- a skinned mesh and at least one skin-bound mesh node
- at least 12 joints, named humanoid joints, and inverse bind matrices
- anchors named `BallReleaseAnchor`, `JerseyNumberAnchor`, and `JerseyNameAnchor`
- clips named `idle`, `dribble_idle`, `gather`, `jump`, `release`, `follow_through`, and `land`
- non-empty animation channels and root translation motion for `gather`, `jump`, `release`, `follow_through`, and `land`

Current Hunyuan LeBron6 audit:

`reference/hunyuan-lebron-rig-audit.json`

The current raw scan fails this contract because it has one static mesh, no skin, no anchors, and no animation clips. That is expected for raw generation output; the Blender pass must turn it into a skinned runtime GLB.

Current rigged LeBron6 audit:

`reference/hunyuan-lebron-rigged-audit.json`

The no-Blender rig bridge output passes this contract with 1 skin, 17 joints, inverse bind matrices, 1 skinned mesh node, 3 runtime anchors, and all 7 named clips.

## Runtime Contract

The `ShooterProfile` controls both gameplay and visuals:

- `visual.glb`: runtime GLB path
- `bodyScale`: player scale
- `team`: dynamic material colors
- `jersey`: name/number/trim
- `releaseFrame` and `releaseFps`: sync point for meter, release animation, ball spawn, camera push, and feedback
- `animationClips`: named clips loaded by Three.js `AnimationMixer`

If the rigged GLB is missing or fails to load during early MVP tiers, the game can fall back to the placeholder visual tier. When `visual.primary` is `generated-scan`, the placeholder is intentionally hidden; the generated mesh either loads as the visible player or reports a mesh-load error instead of showing the block/procedural human.

## Basketball Environment Asset Manifest

Runtime court/ball/hoop/net tuning is declared in:

`src/assets/basketball-assets.json`

This manifest bridges the current lightweight procedural MVP and future compressed GLB assets. It stores:

- approved open-source asset/source candidates
- future `targetGlb` slots for court, basketball, hoop, backboard, and net assets
- material tuning for the generated hardwood court
- Rapier tuning for ball mass, friction, restitution, damping, rim bounce, backboard bounce, floor bounce, and net anchors
- benchmark targets for desktop/mobile FPS and initial payload size

The current game still renders generated assets so it remains GitHub Pages-friendly, but the physics and material values now come from this manifest instead of being hardcoded into the scene.
