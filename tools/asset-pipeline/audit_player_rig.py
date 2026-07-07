#!/usr/bin/env python3
"""Audit JumpShot GLB skinning quality beyond the basic runtime contract."""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path


JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942

FLOAT = 5126
UNSIGNED_SHORT = 5123
UNSIGNED_BYTE = 5121

COMPONENT_SIZE = {
    FLOAT: 4,
    UNSIGNED_SHORT: 2,
    UNSIGNED_BYTE: 1,
}

TYPE_COMPONENTS = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT4": 16,
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_glb(path: Path) -> tuple[dict, bytes]:
    data = path.read_bytes()
    if len(data) < 20:
        fail("file is too small to be a GLB")
    magic, version, declared_length = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67:
        fail("not a GLB file")
    if version != 2:
        fail(f"expected GLB v2, got {version}")
    if declared_length != len(data):
        fail(f"declared length {declared_length} does not match file size {len(data)}")

    gltf = None
    binary = b""
    offset = 12
    while offset + 8 <= len(data):
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset : offset + chunk_length]
        offset += chunk_length
        if chunk_type == JSON_CHUNK:
            gltf = json.loads(chunk.decode("utf-8"))
        elif chunk_type == BIN_CHUNK:
            binary = bytes(chunk)
    if gltf is None:
        fail("missing JSON chunk")
    return gltf, binary


def accessor_payload(gltf: dict, binary: bytes, accessor_index: int) -> tuple[dict, bytes]:
    accessor = gltf["accessors"][accessor_index]
    view = gltf["bufferViews"][accessor["bufferView"]]
    component_size = COMPONENT_SIZE[accessor["componentType"]]
    components = TYPE_COMPONENTS[accessor["type"]]
    byte_stride = view.get("byteStride", component_size * components)
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    count = accessor["count"]
    if byte_stride == component_size * components:
        length = count * byte_stride
        return accessor, binary[start : start + length]

    packed = bytearray()
    for index in range(count):
        row_start = start + index * byte_stride
        packed.extend(binary[row_start : row_start + component_size * components])
    return accessor, bytes(packed)


def unpack_vec4(accessor: dict, payload: bytes) -> list[tuple[float, float, float, float]]:
    count = accessor["count"]
    component_type = accessor["componentType"]
    if accessor["type"] != "VEC4":
        fail(f"expected VEC4 accessor, got {accessor['type']}")
    if component_type == FLOAT:
        return list(struct.iter_unpack("<4f", payload[: count * 16]))
    if component_type == UNSIGNED_SHORT:
        return [tuple(float(value) for value in row) for row in struct.iter_unpack("<4H", payload[: count * 8])]
    if component_type == UNSIGNED_BYTE:
        return [tuple(float(value) for value in row) for row in struct.iter_unpack("<4B", payload[: count * 4])]
    fail(f"unsupported VEC4 component type {component_type}")


def primary_primitive(gltf: dict) -> tuple[int, dict]:
    for mesh_index, mesh in enumerate(gltf.get("meshes", [])):
        for primitive in mesh.get("primitives", []):
            attrs = primitive.get("attributes", {})
            if {"POSITION", "JOINTS_0", "WEIGHTS_0"} <= set(attrs):
                return mesh_index, primitive
    fail("could not find primitive with POSITION, JOINTS_0, and WEIGHTS_0")


def audit(path: Path) -> tuple[dict, int]:
    gltf, binary = load_glb(path)
    mesh_index, primitive = primary_primitive(gltf)
    attrs = primitive["attributes"]
    position_count = gltf["accessors"][attrs["POSITION"]]["count"]

    joints_accessor, joints_payload = accessor_payload(gltf, binary, attrs["JOINTS_0"])
    weights_accessor, weights_payload = accessor_payload(gltf, binary, attrs["WEIGHTS_0"])
    joints = unpack_vec4(joints_accessor, joints_payload)
    weights = unpack_vec4(weights_accessor, weights_payload)
    if len(joints) != position_count or len(weights) != position_count:
        fail("POSITION, JOINTS_0, and WEIGHTS_0 accessor counts do not match")

    skin_nodes = [node for node in gltf.get("nodes", []) if node.get("mesh") == mesh_index and "skin" in node]
    if not skin_nodes:
        fail(f"mesh {mesh_index} is not attached to a skin")
    skin = gltf["skins"][skin_nodes[0]["skin"]]
    joint_nodes = skin.get("joints", [])
    joint_names = [gltf["nodes"][index].get("name", f"joint_{i}") for i, index in enumerate(joint_nodes)]

    joint_vertex_counts: Counter[str] = Counter()
    joint_weight_totals: defaultdict[str, float] = defaultdict(float)
    influence_histogram: Counter[int] = Counter()
    bad_weight_sum = 0
    out_of_range_joint = 0
    max_weight_error = 0.0
    blended_vertices = 0

    for joint_row, weight_row in zip(joints, weights):
        weight_sum = sum(weight_row)
        error = abs(weight_sum - 1.0)
        max_weight_error = max(max_weight_error, error)
        if error > 0.015:
            bad_weight_sum += 1
        active = 0
        for joint_value, weight_value in zip(joint_row, weight_row):
            if weight_value <= 0.001:
                continue
            joint_index = int(joint_value)
            active += 1
            if joint_index < 0 or joint_index >= len(joint_names):
                out_of_range_joint += 1
                continue
            joint_name = joint_names[joint_index]
            joint_vertex_counts[joint_name] += 1
            joint_weight_totals[joint_name] += weight_value
        influence_histogram[active] += 1
        if active >= 2:
            blended_vertices += 1

    animation_names = [animation.get("name", "") for animation in gltf.get("animations", [])]
    required_animation_names = {
        "idle",
        "dribble_idle",
        "gather",
        "jump",
        "release",
        "follow_through",
        "land",
    }
    missing_required_animations = sorted(required_animation_names - set(animation_names))
    quality_flags = []
    if bad_weight_sum:
        quality_flags.append(f"{bad_weight_sum} vertices have weight sums outside tolerance")
    if out_of_range_joint:
        quality_flags.append(f"{out_of_range_joint} active influences point outside the skin joint list")
    if blended_vertices / max(1, position_count) < 0.35:
        quality_flags.append("too few vertices have blended influences for a deforming humanoid")
    if missing_required_animations:
        quality_flags.append(f"missing required animations: {', '.join(missing_required_animations)}")

    report = {
        "path": str(path),
        "bytes": path.stat().st_size,
        "meshIndex": mesh_index,
        "vertexCount": position_count,
        "skin": {
            "jointCount": len(joint_names),
            "jointNames": joint_names,
            "hasInverseBindMatrices": "inverseBindMatrices" in skin,
        },
        "weights": {
            "maxInfluences": max(influence_histogram.keys()) if influence_histogram else 0,
            "influenceHistogram": {str(key): influence_histogram[key] for key in sorted(influence_histogram)},
            "blendedVertexRatio": round(blended_vertices / max(1, position_count), 4),
            "badWeightSumVertices": bad_weight_sum,
            "maxWeightSumError": round(max_weight_error, 6),
            "outOfRangeJointInfluences": out_of_range_joint,
            "jointVertexCounts": dict(sorted(joint_vertex_counts.items())),
            "jointWeightTotals": {name: round(value, 3) for name, value in sorted(joint_weight_totals.items())},
        },
        "animations": {
            "names": animation_names,
            "missingRequired": missing_required_animations,
            "hasLebronCombinedClip": "jumpshot_lebron" in animation_names,
        },
        "extras": gltf.get("extras", {}),
        "qualityFlags": quality_flags,
        "rigAuditReady": not quality_flags,
    }
    return report, 0 if not quality_flags else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("glb", type=Path)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
      report, exit_code = audit(args.glb)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"path": str(args.glb), "error": str(exc), "rigAuditReady": False}), file=sys.stderr)
        return 1

    text = json.dumps(report, indent=2 if args.pretty else None)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return exit_code if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
