"""Auto-rig a generated LeBron scan into JumpShot's runtime character contract.

Run from Blender:
blender --background --python blender_autorig_lebron_scan.py -- \
  assets/players/hunyuan-lebron/player.glb \
  assets/players/hunyuan-lebron/player_rigged.glb

This script is intentionally conservative. It creates a first-pass humanoid
armature, anchors, and named jumpshot clips so the generated mesh can enter the
runtime as a skinned GLB. A human artist should still clean topology, skin
weights, fingers, clothing splits, likeness details, and final animation polish.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


CLIP_RANGES = {
    "idle": (1, 60),
    "dribble_idle": (70, 130),
    "gather": (140, 158),
    "jump": (159, 176),
    "release": (177, 184),
    "follow_through": (185, 218),
    "land": (219, 244),
}

BONE_LAYOUT = {
    "Hips": ((0.0, 1.02, 0.0), (0.0, 1.28, 0.0)),
    "Spine": ((0.0, 1.28, 0.0), (0.0, 1.72, 0.0)),
    "Chest": ((0.0, 1.72, 0.0), (0.0, 2.03, 0.0)),
    "Neck": ((0.0, 2.03, 0.0), (0.0, 2.22, 0.0)),
    "Head": ((0.0, 2.22, 0.0), (0.0, 2.58, 0.0)),
    "LeftUpperArm": ((-0.34, 1.96, 0.0), (-0.72, 1.65, 0.0)),
    "LeftForeArm": ((-0.72, 1.65, 0.0), (-0.62, 1.18, -0.06)),
    "LeftHand": ((-0.62, 1.18, -0.06), (-0.54, 1.02, -0.12)),
    "RightUpperArm": ((0.34, 1.96, 0.0), (0.72, 1.65, 0.0)),
    "RightForeArm": ((0.72, 1.65, 0.0), (0.62, 1.18, -0.06)),
    "RightHand": ((0.62, 1.18, -0.06), (0.54, 1.02, -0.12)),
    "LeftUpperLeg": ((-0.22, 1.02, 0.0), (-0.28, 0.55, 0.02)),
    "LeftLowerLeg": ((-0.28, 0.55, 0.02), (-0.26, 0.12, -0.02)),
    "LeftFoot": ((-0.26, 0.12, -0.02), (-0.26, 0.06, -0.36)),
    "RightUpperLeg": ((0.22, 1.02, 0.0), (0.28, 0.55, 0.02)),
    "RightLowerLeg": ((0.28, 0.55, 0.02), (0.26, 0.12, -0.02)),
    "RightFoot": ((0.26, 0.12, -0.02), (0.26, 0.06, -0.36)),
}

PARENTS = {
    "Spine": "Hips",
    "Chest": "Spine",
    "Neck": "Chest",
    "Head": "Neck",
    "LeftUpperArm": "Chest",
    "LeftForeArm": "LeftUpperArm",
    "LeftHand": "LeftForeArm",
    "RightUpperArm": "Chest",
    "RightForeArm": "RightUpperArm",
    "RightHand": "RightForeArm",
    "LeftUpperLeg": "Hips",
    "LeftLowerLeg": "LeftUpperLeg",
    "LeftFoot": "LeftLowerLeg",
    "RightUpperLeg": "Hips",
    "RightLowerLeg": "RightUpperLeg",
    "RightFoot": "RightLowerLeg",
}


def args_after_double_dash() -> tuple[Path, Path]:
    if "--" not in sys.argv:
        raise SystemExit("usage: blender --background --python blender_autorig_lebron_scan.py -- input.glb output.glb")
    args = sys.argv[sys.argv.index("--") + 1 :]
    if len(args) != 2:
        raise SystemExit("expected input.glb and output.glb")
    return Path(args[0]).resolve(), Path(args[1]).resolve()


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_scan(path: Path) -> list[bpy.types.Object]:
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"no mesh objects found in {path}")
    for obj in meshes:
        obj.name = obj.name or "GeneratedLeBronMesh"
        obj.data.name = obj.name
        for poly in obj.data.polygons:
            poly.use_smooth = True
    return meshes


def normalize_meshes(meshes: list[bpy.types.Object], target_height: float = 2.1) -> None:
    min_corner = Vector((math.inf, math.inf, math.inf))
    max_corner = Vector((-math.inf, -math.inf, -math.inf))
    for obj in meshes:
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            min_corner.x = min(min_corner.x, world.x)
            min_corner.y = min(min_corner.y, world.y)
            min_corner.z = min(min_corner.z, world.z)
            max_corner.x = max(max_corner.x, world.x)
            max_corner.y = max(max_corner.y, world.y)
            max_corner.z = max(max_corner.z, world.z)
    height = max(max_corner.y - min_corner.y, 0.001)
    scale = target_height / height
    center = (min_corner + max_corner) * 0.5
    for obj in meshes:
        obj.location.x -= center.x
        obj.location.z -= center.z
        obj.location.y -= min_corner.y
        obj.scale *= scale
    bpy.context.view_layer.update()


def create_armature() -> bpy.types.Object:
    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    armature = bpy.context.object
    armature.name = "JumpShotHumanoid"
    armature.data.name = "JumpShotHumanoidArmature"

    first = armature.data.edit_bones[0]
    first.name = "Hips"
    first.head = BONE_LAYOUT["Hips"][0]
    first.tail = BONE_LAYOUT["Hips"][1]

    for name, (head, tail) in BONE_LAYOUT.items():
        if name == "Hips":
            continue
        bone = armature.data.edit_bones.new(name)
        bone.head = head
        bone.tail = tail
        parent = PARENTS.get(name)
        if parent:
            bone.parent = armature.data.edit_bones[parent]
            bone.use_connect = False

    bpy.ops.object.mode_set(mode="OBJECT")
    return armature


def parent_with_automatic_weights(meshes: list[bpy.types.Object], armature: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")


def add_anchor(name: str, location: tuple[float, float, float], parent: bpy.types.Object) -> bpy.types.Object:
    anchor = bpy.data.objects.new(name, None)
    anchor.empty_display_type = "PLAIN_AXES"
    anchor.empty_display_size = 0.08
    anchor.location = location
    anchor.parent = parent
    bpy.context.collection.objects.link(anchor)
    return anchor


def set_pose(armature: bpy.types.Object, frame: int, values: dict[str, tuple[float, float, float]], root_y: float = 0.0) -> None:
    bpy.context.scene.frame_set(frame)
    armature.location.y = root_y
    armature.keyframe_insert(data_path="location", frame=frame)
    for bone_name, euler in values.items():
        bone = armature.pose.bones.get(bone_name)
        if not bone:
            continue
        bone.rotation_mode = "XYZ"
        bone.rotation_euler = tuple(math.radians(v) for v in euler)
        bone.keyframe_insert(data_path="rotation_euler", frame=frame)


def create_lebron_jumpshot_actions(armature: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="POSE")

    poses = {
        1: {},
        30: {"Chest": (1, 0, -1), "LeftUpperArm": (-4, 0, -8), "RightUpperArm": (-4, 0, 8)},
        70: {"LeftUpperArm": (-10, 0, -12), "RightUpperArm": (8, 0, 16), "LeftUpperLeg": (8, 0, 0), "RightUpperLeg": (-8, 0, 0)},
        100: {"LeftUpperArm": (8, 0, -8), "RightUpperArm": (-12, 0, 10), "LeftUpperLeg": (-8, 0, 0), "RightUpperLeg": (8, 0, 0)},
        140: {"Hips": (-8, 0, 0), "Spine": (-6, 0, 0), "Chest": (-5, 0, -3), "LeftUpperLeg": (18, 0, -2), "RightUpperLeg": (18, 0, 2), "LeftLowerLeg": (-20, 0, 0), "RightLowerLeg": (-20, 0, 0), "LeftUpperArm": (-18, 0, -24), "RightUpperArm": (-22, 0, 22)},
        158: {"Hips": (-4, 0, 0), "Spine": (4, 0, 0), "Chest": (8, 0, -4), "LeftUpperArm": (-58, 4, -26), "LeftForeArm": (-54, 0, 8), "RightUpperArm": (-68, -2, 18), "RightForeArm": (-62, 0, -10), "LeftUpperLeg": (6, 0, -2), "RightUpperLeg": (6, 0, 2)},
        176: {"Hips": (2, 0, 0), "Spine": (8, 0, -2), "Chest": (14, 0, -6), "LeftUpperArm": (-96, 5, -18), "LeftForeArm": (-72, 0, 18), "LeftHand": (-18, 0, 0), "RightUpperArm": (-112, -3, 12), "RightForeArm": (-82, 0, -18), "RightHand": (-22, 0, -20), "LeftUpperLeg": (-4, 0, -8), "RightUpperLeg": (2, 0, 6)},
        184: {"Hips": (3, 0, 0), "Spine": (10, 0, -2), "Chest": (16, 0, -8), "LeftUpperArm": (-98, 4, -42), "LeftForeArm": (-30, 0, 22), "RightUpperArm": (-124, -4, 8), "RightForeArm": (-88, 0, -26), "RightHand": (-34, 0, -38), "LeftUpperLeg": (-8, 0, -12), "RightUpperLeg": (4, 0, 8)},
        218: {"Hips": (1, 0, 0), "Spine": (7, 0, -1), "Chest": (12, 0, -5), "LeftUpperArm": (-70, 2, -48), "LeftForeArm": (-18, 0, 14), "RightUpperArm": (-118, -2, 8), "RightForeArm": (-70, 0, -24), "RightHand": (-28, 0, -34), "LeftUpperLeg": (-12, 0, -10), "RightUpperLeg": (2, 0, 4)},
        244: {"Hips": (-2, 0, 0), "Spine": (0, 0, 0), "Chest": (1, 0, -1), "LeftUpperArm": (-8, 0, -10), "RightUpperArm": (-8, 0, 10), "LeftUpperLeg": (2, 0, 0), "RightUpperLeg": (2, 0, 0)},
    }

    for frame, pose in poses.items():
        lift = 0.0
        if 159 <= frame <= 218:
            lift = math.sin((frame - 159) / (218 - 159) * math.pi) * 0.22
        set_pose(armature, frame, pose, root_y=lift)

    master_action = armature.animation_data.action
    if master_action is None:
        raise RuntimeError("failed to create source jumpshot action")

    for action_name, (start, end) in CLIP_RANGES.items():
        action = master_action.copy()
        action.name = action_name
        action.use_frame_range = True
        action.frame_start = start
        action.frame_end = end

    bpy.ops.object.mode_set(mode="OBJECT")


def create_materials(meshes: list[bpy.types.Object]) -> None:
    material = bpy.data.materials.new("GeneratedLeBronRuntime")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.32, 0.18, 0.12, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.58
        bsdf.inputs["Metallic"].default_value = 0.0
    for mesh in meshes:
        if not mesh.data.materials:
            mesh.data.materials.append(material)


def export_runtime_glb(output: Path) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.context.scene.objects:
        if obj.type in {"MESH", "ARMATURE"} or obj.name.endswith("Anchor"):
            obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=str(output),
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


def main() -> None:
    source, output = args_after_double_dash()
    clear_scene()
    meshes = import_scan(source)
    normalize_meshes(meshes)
    create_materials(meshes)
    armature = create_armature()
    parent_with_automatic_weights(meshes, armature)
    add_anchor("BallReleaseAnchor", (0.18, 2.52, -0.58), armature)
    add_anchor("JerseyNumberAnchor", (0.0, 1.48, 0.34), armature)
    add_anchor("JerseyNameAnchor", (0.0, 1.78, 0.34), armature)
    create_lebron_jumpshot_actions(armature)
    output.parent.mkdir(parents=True, exist_ok=True)
    export_runtime_glb(output)


if __name__ == "__main__":
    main()
