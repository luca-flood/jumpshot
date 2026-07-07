# JumpShot Asset and Character-Control Research

## Asset Sources

### Kenney Sports Pack

- URL: https://kenney.nl/assets/sports-pack
- License: Creative Commons CC0.
- Use for: quick UI, 2D sports icons, temporary basketball-themed sprites, score-card polish.
- Notes: The pack is 2D/top-down, so it is not a replacement for runtime 3D players, but it is clean, permissive, and useful for menus/results screens.

### Kenney General Asset Library

- URL: https://kenney.nl/assets
- License note: Kenney states asset-page game assets are public domain/CC0 and attribution is not required.
- Use for: placeholder props, UI, icons, and lightweight arcade-style extras.

### Poly Haven

- URL: https://polyhaven.com
- License: CC0 for HDRIs, textures, and 3D models.
- Use for: arena HDRI lighting, hardwood-like PBR textures, concrete/plastic/metal materials, background props.
- Notes: Better for environmental realism than basketball-specific meshes.

### OpenGameArt

- URL: https://opengameart.org
- License: varies per asset, including CC0, CC BY, GPL, LGPL, and others.
- Use for: one-off free assets if license is checked asset-by-asset.
- Notes: Useful search pool, but licenses are mixed, so avoid bulk import without review.

## Character Control and Dribbling Stack

### Rapier JavaScript Character Controller

- URL: https://rapier.rs/docs/user_guides/javascript/character_controller/
- Use for: robust collision-aware player movement.
- Fit for JumpShot: strong candidate if movement becomes more physical. Rapier's controller computes corrected movement from desired translation, handles obstacles/slopes/stairs, and can use kinematic bodies.
- Caveat: dribbling itself should remain custom gameplay animation, not physics-driven ball chaos.

### react-three-rapier

- URL: https://github.com/pmndrs/react-three-rapier
- License: MIT.
- Use for: Rapier in a React Three Fiber version of JumpShot.
- Fit for JumpShot: good if the app migrates to R3F. Less useful for the current static vanilla Three.js file unless we move architecture.

### Ecctrl

- URL: https://github.com/pmndrs/ecctrl
- License: MIT.
- Use for: R3F + Rapier physics-driven character controllers, animation states, touch controls, camera tooling, curve tuning.
- Fit for JumpShot: best off-the-shelf character-control candidate if we adopt R3F. It already exposes runtime animation state and curve-tuned behavior, which maps well to dribble/walk/sprint/gather transitions.
- Caveat: it is R3F-first, so adopting it means a framework migration.

### three-stdlib

- URL: https://github.com/pmndrs/three-stdlib
- License: MIT.
- Use for: standalone Three.js helpers/loaders/controls without copying examples code.
- Fit for JumpShot: useful immediately for vanilla Three.js utilities. It is not a dribbling system, but it helps keep loader/control imports cleaner.

## Recommendation

Keep dribbling as a deterministic animation system tied to player speed, hand side, and shot phase. Use physics only for character collision and optional ball/rim/net polish.

Best near-term path:

1. Keep vanilla Three.js for the prototype.
2. Add Rapier directly only when court collision or contact movement matters.
3. Make dribble a authored state machine: `idle_dribble`, `walk_dribble`, `sprint_dribble`, `gather`, `pickup`, `release`, `follow_through`.
4. If the project grows into a full app, consider migrating to React Three Fiber and using Ecctrl + react-three-rapier for movement/camera/input.

## Current JumpShot Implementation Decision

- Shot result is timing-first: only the green window can score.
- Non-green releases are forced misses even if the simulated ball crosses the hoop plane.
- The visible miss trajectory is driven by `meterError`, so early/late releases visibly alter short/long and left/right flight instead of using a cosmetic-only meter.
- Rapier is used directly in the vanilla Three.js build for ball, floor, rim, backboard, and bounce contact. Character dribbling remains deterministic so the ball stays readable and responsive.
- Game modes are static-host friendly for GitHub Pages: Practice, deterministic Daily spots, and a 15-second threes sprint store best local results in `localStorage`.
