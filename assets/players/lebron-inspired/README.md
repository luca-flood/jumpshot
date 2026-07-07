# LeBron-Inspired Asset Slot

Place the optimized runtime GLB files for this profile here.

Expected runtime files:

- `player.glb`: default MVP player asset
- `player_lod0.glb`: close camera LOD, target 35k-55k triangles
- `player_lod1.glb`: gameplay LOD, target 12k-25k triangles
- `player_lod2.glb`: far/background LOD, target under 8k triangles

Expected mesh/object naming:

- `Body`
- `Head`
- `Hair`
- `Jersey`
- `Shorts`
- `Socks`
- `Shoes`
- `Accessories`
- `JerseyNumberAnchor`
- `JerseyNameAnchor`
- `BallReleaseAnchor`

The game will keep using the placeholder player until `player.glb` exists.
