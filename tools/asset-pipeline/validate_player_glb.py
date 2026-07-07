#!/usr/bin/env python3
"""Validate JumpShot player GLBs against the runtime animation contract.

This intentionally uses only the Python standard library so it can run in a
bare asset-pipeline checkout before Blender/glTF tooling is installed.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path


REQUIRED_CLIPS = {
    "idle",
    "dribble_idle",
    "gather",
    "jump",
    "release",
    "follow_through",
    "land",
}

REQUIRED_ANCHORS = {
    "BallReleaseAnchor",
    "JerseyNumberAnchor",
    "JerseyNameAnchor",
}

REQUIRED_JOINT_NAMES = {
    "Hips",
    "Spine",
    "Chest",
    "Head",
    "LeftUpperArm",
    "LeftForeArm",
    "LeftHand",
    "RightUpperArm",
    "RightForeArm",
    "RightHand",
    "LeftUpperLeg",
    "LeftLowerLeg",
    "LeftFoot",
    "RightUpperLeg",
    "RightLowerLeg",
    "RightFoot",
}

REQUIRED_ROOT_MOTION_CLIPS = {
    "gather",
    "jump",
    "release",
    "follow_through",
    "land",
}


def load_glb_json(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < 20:
        raise ValueError("file is too small to be a GLB")
    magic, version, declared_length = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67:
        raise ValueError("not a binary GLB file")
    if version != 2:
        raise ValueError(f"unsupported GLB version {version}; expected 2")
    if declared_length != len(data):
        raise ValueError(f"declared length {declared_length} does not match file size {len(data)}")

    offset = 12
    while offset + 8 <= len(data):
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset : offset + chunk_length]
        offset += chunk_length
        if chunk_type == 0x4E4F534A:
            return json.loads(chunk.decode("utf-8"))
    raise ValueError("missing JSON chunk")


def collect_node_names(gltf: dict) -> set[str]:
    return {node.get("name", "") for node in gltf.get("nodes", []) if node.get("name")}


def collect_animation_names(gltf: dict) -> set[str]:
    return {clip.get("name", "") for clip in gltf.get("animations", []) if clip.get("name")}


def animation_stats(gltf: dict) -> dict:
    node_names = {index: node.get("name", "") for index, node in enumerate(gltf.get("nodes", []))}
    channel_counts = {}
    root_motion_clips = set()
    for clip in gltf.get("animations", []):
        name = clip.get("name", "")
        channels = clip.get("channels", [])
        channel_counts[name] = len(channels)
        for channel in channels:
            target = channel.get("target", {})
            node_name = node_names.get(target.get("node"))
            if node_name == "JumpShotSkeletonRoot" and target.get("path") == "translation":
                root_motion_clips.add(name)
    return {
        "animationChannels": channel_counts,
        "rootMotionClips": sorted(root_motion_clips),
        "missingRootMotionClips": sorted(REQUIRED_ROOT_MOTION_CLIPS - root_motion_clips),
    }


def mesh_stats(gltf: dict) -> dict:
    primitive_count = 0
    skinned_mesh_nodes = 0
    mesh_nodes = 0
    joint_count = 0
    skins_with_inverse_bind_matrices = 0
    for node in gltf.get("nodes", []):
        if "mesh" in node:
            mesh_nodes += 1
        if "skin" in node:
            skinned_mesh_nodes += 1
    for skin in gltf.get("skins", []):
        joint_count += len(skin.get("joints", []))
        if "inverseBindMatrices" in skin:
            skins_with_inverse_bind_matrices += 1
    for mesh in gltf.get("meshes", []):
        primitive_count += len(mesh.get("primitives", []))
    return {
        "meshNodes": mesh_nodes,
        "primitives": primitive_count,
        "skins": len(gltf.get("skins", [])),
        "joints": joint_count,
        "skinsWithInverseBindMatrices": skins_with_inverse_bind_matrices,
        "skinnedMeshNodes": skinned_mesh_nodes,
        "nodes": len(gltf.get("nodes", [])),
        "materials": len(gltf.get("materials", [])),
        "animations": len(gltf.get("animations", [])),
    }


def validate(path: Path, strict: bool) -> tuple[dict, int]:
    gltf = load_glb_json(path)
    nodes = collect_node_names(gltf)
    clips = collect_animation_names(gltf)
    stats = mesh_stats(gltf)
    anim_stats = animation_stats(gltf)

    missing_anchors = sorted(REQUIRED_ANCHORS - nodes)
    missing_joints = sorted(REQUIRED_JOINT_NAMES - nodes)
    missing_clips = sorted(REQUIRED_CLIPS - clips)
    empty_clips = sorted(name for name, count in anim_stats["animationChannels"].items() if name in REQUIRED_CLIPS and count == 0)
    has_skin = (
        stats["skins"] > 0
        and stats["skinnedMeshNodes"] > 0
        and stats["joints"] >= 12
        and stats["skinsWithInverseBindMatrices"] > 0
    )
    has_all_clips = not missing_clips
    has_all_anchors = not missing_anchors
    has_required_joints = not missing_joints
    has_animated_clips = not empty_clips
    has_root_motion = not anim_stats["missingRootMotionClips"]
    animation_ready = has_skin and has_all_clips and has_all_anchors and has_required_joints and has_animated_clips and has_root_motion

    report = {
        "path": str(path),
        "bytes": path.stat().st_size,
        "stats": stats,
        "animationStats": anim_stats,
        "clipNames": sorted(clips),
        "requiredClips": sorted(REQUIRED_CLIPS),
        "missingClips": missing_clips,
        "emptyClips": empty_clips,
        "requiredAnchors": sorted(REQUIRED_ANCHORS),
        "missingAnchors": missing_anchors,
        "requiredJoints": sorted(REQUIRED_JOINT_NAMES),
        "missingJoints": missing_joints,
        "hasSkin": has_skin,
        "hasRequiredJoints": has_required_joints,
        "hasAnimatedClips": has_animated_clips,
        "hasRootMotion": has_root_motion,
        "animationReady": animation_ready,
    }

    exit_code = 0
    if strict and not animation_ready:
        exit_code = 2
    return report, exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("glb", type=Path, help="Path to a .glb player asset")
    parser.add_argument("--strict", action="store_true", help="Fail unless the GLB is animation-ready")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    try:
        report, exit_code = validate(args.glb, args.strict)
    except Exception as exc:  # noqa: BLE001 - CLI should report any parser failure plainly.
        print(json.dumps({"path": str(args.glb), "error": str(exc), "animationReady": False}), file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2 if args.pretty else None))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
