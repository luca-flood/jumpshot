"""Blender export helper for JumpShot runtime GLB assets.

Run from Blender:
blender source.blend --background --python blender_export_runtime.py -- <output.glb>
"""

from __future__ import annotations

import sys

import bpy


PART_NAMES = {
    "Body",
    "Head",
    "Hair",
    "Jersey",
    "Shorts",
    "Socks",
    "Shoes",
    "Accessories",
}


def arg_after_double_dash(default: str) -> str:
    if "--" not in sys.argv:
        return default
    args = sys.argv[sys.argv.index("--") + 1 :]
    return args[0] if args else default


def prepare_scene() -> None:
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.data.name = obj.name
            obj.select_set(obj.name in PART_NAMES or obj.find_armature() is not None)
            for poly in obj.data.polygons:
                poly.use_smooth = True
        elif obj.type == "ARMATURE":
            obj.select_set(True)
        else:
            obj.select_set(obj.name.endswith("Anchor"))


def main() -> None:
    output = arg_after_double_dash("//player.glb")
    prepare_scene()
    bpy.ops.export_scene.gltf(
        filepath=output,
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_animations=True,
        export_frame_range=False,
        export_skins=True,
        export_morph=True,
        export_materials="EXPORT",
    )


if __name__ == "__main__":
    main()
