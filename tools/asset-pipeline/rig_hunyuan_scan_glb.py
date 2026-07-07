#!/usr/bin/env python3
"""Create a first-pass skinned JumpShot GLB from an unrigged Hunyuan scan.

This is a no-Blender bridge for the current LeBron mesh. It preserves the raw
mesh data, appends JOINTS_0/WEIGHTS_0 attributes, creates a humanoid skeleton,
adds runtime anchors, and writes named jumpshot animation clips.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
from pathlib import Path


JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942

FLOAT = 5126
UNSIGNED_INT = 5125
UNSIGNED_SHORT = 5123

JOINTS = [
    ("Hips", None, (0.0, -0.02, 0.0)),
    ("Spine", "Hips", (0.0, 0.24, 0.0)),
    ("Chest", "Spine", (0.0, 0.34, 0.0)),
    ("Neck", "Chest", (0.0, 0.18, 0.0)),
    ("Head", "Neck", (0.0, 0.22, 0.0)),
    ("LeftUpperArm", "Chest", (-0.22, -0.02, 0.0)),
    ("LeftForeArm", "LeftUpperArm", (-0.24, -0.26, -0.02)),
    ("LeftHand", "LeftForeArm", (0.06, -0.25, -0.04)),
    ("RightUpperArm", "Chest", (0.22, -0.02, 0.0)),
    ("RightForeArm", "RightUpperArm", (0.24, -0.26, -0.02)),
    ("RightHand", "RightForeArm", (-0.06, -0.25, -0.04)),
    ("LeftUpperLeg", "Hips", (-0.16, -0.14, 0.0)),
    ("LeftLowerLeg", "LeftUpperLeg", (-0.02, -0.46, 0.0)),
    ("LeftFoot", "LeftLowerLeg", (0.0, -0.36, -0.12)),
    ("RightUpperLeg", "Hips", (0.16, -0.14, 0.0)),
    ("RightLowerLeg", "RightUpperLeg", (0.02, -0.46, 0.0)),
    ("RightFoot", "RightLowerLeg", (0.0, -0.36, -0.12)),
]

LEBRON_READY = {
    "Hips": (-2, 0, 0),
    "Spine": (1, 0, 0),
    "Chest": (2, 0, -1),
    "LeftUpperArm": (-12, 2, -16),
    "LeftForeArm": (-12, 0, 10),
    "RightUpperArm": (-10, -2, 16),
    "RightForeArm": (-14, 0, -10),
    "LeftUpperLeg": (3, 0, -1),
    "RightUpperLeg": (-3, 0, 1),
}

LEBRON_DIP = {
    "Hips": (-10, 0, 0),
    "Spine": (-7, 0, 0),
    "Chest": (-5, 0, -4),
    "LeftUpperArm": (-30, 5, -24),
    "LeftForeArm": (-36, 0, 20),
    "LeftHand": (-10, 0, 8),
    "RightUpperArm": (-34, -5, 26),
    "RightForeArm": (-42, 0, -22),
    "RightHand": (-6, 0, -8),
    "LeftUpperLeg": (20, 0, -4),
    "RightUpperLeg": (19, 0, 3),
    "LeftLowerLeg": (-8, 0, 2),
    "RightLowerLeg": (-8, 0, -2),
}

LEBRON_LOAD = {
    "Hips": (-4, 0, 0),
    "Spine": (3, 0, -2),
    "Chest": (9, 0, -7),
    "LeftUpperArm": (-70, 8, -30),
    "LeftForeArm": (-58, 2, 26),
    "LeftHand": (-8, 0, 14),
    "RightUpperArm": (-78, -5, 18),
    "RightForeArm": (-66, 0, -18),
    "RightHand": (-10, 0, -12),
    "LeftUpperLeg": (8, 0, -3),
    "RightUpperLeg": (7, 0, 3),
}

LEBRON_SET = {
    "Hips": (2, 0, 0),
    "Spine": (7, 0, -3),
    "Chest": (14, 1, -9),
    "LeftUpperArm": (-104, 8, -34),
    "LeftForeArm": (-78, 2, 32),
    "LeftHand": (-12, 2, 18),
    "RightUpperArm": (-118, -5, 12),
    "RightForeArm": (-88, 0, -20),
    "RightHand": (-14, 0, -18),
    "LeftUpperLeg": (-4, 0, -4),
    "RightUpperLeg": (-2, 0, 4),
    "LeftLowerLeg": (5, 0, 0),
    "RightLowerLeg": (4, 0, 0),
}

LEBRON_RELEASE = {
    "Hips": (4, 0, 0),
    "Spine": (9, 0, -4),
    "Chest": (17, 2, -12),
    "LeftUpperArm": (-88, 16, -54),
    "LeftForeArm": (-48, 4, 38),
    "LeftHand": (6, 12, 26),
    "RightUpperArm": (-132, -6, 8),
    "RightForeArm": (-92, 0, -30),
    "RightHand": (-42, 0, -44),
    "LeftUpperLeg": (-9, 0, -8),
    "RightUpperLeg": (-5, 0, 5),
    "LeftLowerLeg": (10, 0, 2),
    "RightLowerLeg": (7, 0, -1),
}

LEBRON_FOLLOW = {
    "Hips": (1, 0, 0),
    "Spine": (5, 0, -2),
    "Chest": (12, 1, -8),
    "LeftUpperArm": (-54, 12, -58),
    "LeftForeArm": (-28, 2, 32),
    "LeftHand": (4, 8, 20),
    "RightUpperArm": (-122, -3, 6),
    "RightForeArm": (-70, 0, -25),
    "RightHand": (-32, 0, -38),
    "LeftUpperLeg": (-14, 0, -11),
    "RightUpperLeg": (-8, 0, 4),
    "LeftLowerLeg": (16, 0, 2),
    "RightLowerLeg": (9, 0, -1),
}

LEBRON_LAND = {
    "Hips": (-5, 0, 0),
    "Spine": (-1, 0, 0),
    "Chest": (2, 0, -2),
    "LeftUpperArm": (-28, 5, -24),
    "LeftForeArm": (-20, 0, 12),
    "RightUpperArm": (-42, -2, 12),
    "RightForeArm": (-20, 0, -12),
    "LeftUpperLeg": (12, 0, -3),
    "RightUpperLeg": (11, 0, 3),
    "LeftLowerLeg": (-5, 0, 1),
    "RightLowerLeg": (-5, 0, -1),
}

CLIPS = {
    "idle": [(0.0, LEBRON_READY), (1.0, {"Chest": (3, 0, -1), "Spine": (2, 0, 0)}), (2.0, LEBRON_READY)],
    "dribble_idle": [
        (0.0, {**LEBRON_READY, "LeftUpperArm": (-8, 0, -16), "RightUpperArm": (12, 0, 18), "LeftUpperLeg": (5, 0, 0), "RightUpperLeg": (-5, 0, 0)}),
        (0.5, {**LEBRON_READY, "LeftUpperArm": (10, 0, -12), "RightUpperArm": (-14, 0, 14), "LeftUpperLeg": (-5, 0, 0), "RightUpperLeg": (5, 0, 0)}),
        (1.0, {**LEBRON_READY, "LeftUpperArm": (-8, 0, -16), "RightUpperArm": (12, 0, 18), "LeftUpperLeg": (5, 0, 0), "RightUpperLeg": (-5, 0, 0)}),
    ],
    "gather": [
        (0.0, LEBRON_READY),
        (0.12, LEBRON_DIP),
        (0.22, LEBRON_LOAD),
    ],
    "load": [
        (0.0, LEBRON_DIP),
        (0.18, LEBRON_LOAD),
        (0.26, LEBRON_SET),
    ],
    "jump": [
        (0.0, LEBRON_LOAD),
        (0.2, LEBRON_SET),
    ],
    "release": [
        (0.0, LEBRON_SET),
        (0.055, LEBRON_RELEASE),
        (0.12, LEBRON_FOLLOW),
    ],
    "follow_through": [
        (0.0, LEBRON_RELEASE),
        (0.24, LEBRON_FOLLOW),
        (0.58, {**LEBRON_FOLLOW, "Chest": (8, 0, -5), "RightForeArm": (-58, 0, -20), "LeftUpperArm": (-44, 8, -42)}),
    ],
    "land": [
        (0.0, LEBRON_FOLLOW),
        (0.18, LEBRON_LAND),
        (0.32, LEBRON_READY),
    ],
    "recover": [
        (0.0, LEBRON_LAND),
        (0.22, LEBRON_READY),
    ],
    "jumpshot_lebron": [
        (0.0, LEBRON_READY),
        (0.16, LEBRON_DIP),
        (0.34, LEBRON_LOAD),
        (0.5, LEBRON_SET),
        (0.6, LEBRON_RELEASE),
        (0.76, LEBRON_FOLLOW),
        (0.98, LEBRON_LAND),
        (1.12, LEBRON_READY),
    ],
}

ROOT_TRANSLATIONS = {
    "gather": [(0.0, (0.0, 0.0, 0.0)), (0.12, (0.0, -0.045, 0.0)), (0.22, (0.0, -0.015, -0.01))],
    "load": [(0.0, (0.0, -0.04, 0.0)), (0.18, (0.0, -0.015, -0.02)), (0.26, (0.0, 0.04, -0.035))],
    "jump": [(0.0, (0.0, 0.0, -0.015)), (0.2, (0.0, 0.15, -0.055))],
    "release": [(0.0, (0.0, 0.15, -0.055)), (0.055, (0.0, 0.18, -0.075)), (0.12, (0.0, 0.17, -0.085))],
    "follow_through": [(0.0, (0.0, 0.17, -0.085)), (0.24, (0.0, 0.1, -0.11)), (0.58, (0.0, 0.04, -0.12))],
    "land": [(0.0, (0.0, 0.05, -0.08)), (0.18, (0.0, -0.02, -0.03)), (0.32, (0.0, 0.0, 0.0))],
    "recover": [(0.0, (0.0, -0.02, -0.03)), (0.22, (0.0, 0.0, 0.0))],
    "jumpshot_lebron": [
        (0.0, (0.0, 0.0, 0.0)),
        (0.16, (0.0, -0.045, 0.0)),
        (0.34, (0.0, -0.015, -0.02)),
        (0.5, (0.0, 0.12, -0.055)),
        (0.6, (0.0, 0.18, -0.08)),
        (0.76, (0.0, 0.1, -0.11)),
        (0.98, (0.0, -0.02, -0.03)),
        (1.12, (0.0, 0.0, 0.0)),
    ],
}

ANIMATION_METADATA = {
    "version": 1,
    "sourceReference": "youtube:nuKzWQMck-Q",
    "style": "lebron compact high-set jumpshot",
    "combinedClip": "jumpshot_lebron",
    "releaseFrame": 36,
    "releaseFps": 60,
    "releaseTimeSeconds": 0.6,
    "keyAttributes": [
        "compact dip",
        "high right-hand set point",
        "left guide hand peel",
        "slight shoulder turn",
        "right wrist gooseneck",
        "soft rearward fade",
        "left leg follow-through kick",
    ],
}


def align4(data: bytearray, pad: int = 0) -> None:
    while len(data) % 4:
        data.append(pad)


def quat_from_euler(rx: float, ry: float, rz: float) -> tuple[float, float, float, float]:
    x, y, z = math.radians(rx) / 2, math.radians(ry) / 2, math.radians(rz) / 2
    cx, sx = math.cos(x), math.sin(x)
    cy, sy = math.cos(y), math.sin(y)
    cz, sz = math.cos(z), math.sin(z)
    return (
        sx * cy * cz - cx * sy * sz,
        cx * sy * cz + sx * cy * sz,
        cx * cy * sz - sx * sy * cz,
        cx * cy * cz + sx * sy * sz,
    )


def load_glb(path: Path) -> tuple[dict, bytearray]:
    data = path.read_bytes()
    magic, version, _ = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67 or version != 2:
        raise ValueError("expected GLB v2")
    gltf = None
    binary = bytearray()
    offset = 12
    while offset + 8 <= len(data):
        length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset : offset + length]
        offset += length
        if chunk_type == JSON_CHUNK:
            gltf = json.loads(chunk.decode("utf-8"))
        elif chunk_type == BIN_CHUNK:
            binary = bytearray(chunk)
    if gltf is None:
        raise ValueError("missing JSON chunk")
    return gltf, binary


def accessor_bytes(gltf: dict, binary: bytes, accessor_index: int) -> bytes:
    accessor = gltf["accessors"][accessor_index]
    view = gltf["bufferViews"][accessor["bufferView"]]
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    component_size = {FLOAT: 4, UNSIGNED_INT: 4, UNSIGNED_SHORT: 2}[accessor["componentType"]]
    components = {"SCALAR": 1, "VEC3": 3, "VEC4": 4, "MAT4": 16}[accessor["type"]]
    length = accessor["count"] * component_size * components
    return binary[start : start + length]


def read_positions(gltf: dict, binary: bytes) -> list[tuple[float, float, float]]:
    primitive = gltf["meshes"][0]["primitives"][0]
    pos_accessor = primitive["attributes"]["POSITION"]
    raw = accessor_bytes(gltf, binary, pos_accessor)
    count = gltf["accessors"][pos_accessor]["count"]
    return list(struct.iter_unpack("<fff", raw[: count * 12]))


JOINT_INDEX = {name: index for index, (name, _, _) in enumerate(JOINTS)}


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 1.0 if value >= edge1 else 0.0
    t = clamp((value - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def mesh_bounds(positions: list[tuple[float, float, float]]) -> dict[str, tuple[float, float, float]]:
    mins = tuple(min(vertex[i] for vertex in positions) for i in range(3))
    maxs = tuple(max(vertex[i] for vertex in positions) for i in range(3))
    size = tuple(maxs[i] - mins[i] for i in range(3))
    center = tuple((mins[i] + maxs[i]) * 0.5 for i in range(3))
    return {"min": mins, "max": maxs, "size": size, "center": center}


def normalize_vertex(x: float, y: float, z: float, bounds: dict[str, tuple[float, float, float]]) -> tuple[float, float, float, float]:
    min_x, min_y, min_z = bounds["min"]
    size_x, size_y, size_z = bounds["size"]
    center_x, _, center_z = bounds["center"]
    y01 = (y - min_y) / max(size_y, 0.001)
    x_side = (x - center_x) / max(size_x * 0.5, 0.001)
    z_side = (z - center_z) / max(size_z * 0.5, 0.001)
    return y01, x_side, abs(x_side), z_side


def add_weight(weights: dict[int, float], joint_name: str, amount: float) -> None:
    if amount <= 0:
        return
    joint = JOINT_INDEX[joint_name]
    weights[joint] = weights.get(joint, 0.0) + amount


def top4_normalized(weights: dict[int, float]) -> list[tuple[int, float]]:
    top = sorted(weights.items(), key=lambda item: item[1], reverse=True)[:4]
    total = sum(weight for _, weight in top)
    if total <= 0:
        return [(JOINT_INDEX["Hips"], 1.0), (0, 0.0), (0, 0.0), (0, 0.0)]
    normalized = [(joint, weight / total) for joint, weight in top]
    while len(normalized) < 4:
        normalized.append((0, 0.0))
    return normalized


def skin_weights_for_vertex(x: float, y: float, z: float, bounds: dict[str, tuple[float, float, float]]) -> list[tuple[int, float]]:
    y01, x_side, x_abs, z_side = normalize_vertex(x, y, z, bounds)
    left = x_side < 0
    side_prefix = "Left" if left else "Right"
    weights: dict[int, float] = {}

    if y01 >= 0.82:
        head_blend = smoothstep(0.82, 0.92, y01)
        add_weight(weights, "Head", 0.72 + 0.25 * head_blend)
        add_weight(weights, "Neck", 0.18 * (1.0 - head_blend))
        add_weight(weights, "Chest", 0.1 * (1.0 - head_blend))
        return top4_normalized(weights)

    is_arm = x_abs > 0.34 and 0.22 < y01 < 0.82
    if is_arm:
        lower_arm_bias = smoothstep(0.58, 0.78, x_abs) * (1.0 - smoothstep(0.68, 0.82, y01))
        hand_bias = smoothstep(0.78, 0.93, x_abs) * (1.0 - smoothstep(0.45, 0.66, y01))
        shoulder_blend = smoothstep(0.62, 0.78, y01)
        add_weight(weights, f"{side_prefix}UpperArm", 0.58 + 0.18 * shoulder_blend)
        add_weight(weights, f"{side_prefix}ForeArm", 0.28 + 0.35 * lower_arm_bias)
        add_weight(weights, f"{side_prefix}Hand", 0.08 + 0.48 * hand_bias)
        add_weight(weights, "Chest", 0.24 * (1.0 - lower_arm_bias) * shoulder_blend)
        return top4_normalized(weights)

    if y01 >= 0.46:
        chest = smoothstep(0.52, 0.75, y01)
        spine = 1.0 - abs(y01 - 0.58) / 0.24
        add_weight(weights, "Chest", 0.45 + 0.35 * chest)
        add_weight(weights, "Spine", 0.25 + 0.35 * clamp(spine))
        add_weight(weights, "Hips", 0.2 * (1.0 - chest))
        return top4_normalized(weights)

    if y01 >= 0.34:
        side_weight = smoothstep(0.08, 0.38, x_abs)
        add_weight(weights, "Hips", 0.62 * (1.0 - side_weight) + 0.22)
        add_weight(weights, f"{side_prefix}UpperLeg", 0.55 * side_weight + 0.18)
        add_weight(weights, "Spine", 0.18 * (1.0 - side_weight))
        return top4_normalized(weights)

    lower_leg = smoothstep(0.12, 0.28, 1.0 - y01)
    foot = smoothstep(0.68, 0.95, abs(z_side)) * (1.0 - smoothstep(0.11, 0.19, y01))
    add_weight(weights, f"{side_prefix}UpperLeg", 0.65 * (1.0 - lower_leg) + 0.1)
    add_weight(weights, f"{side_prefix}LowerLeg", 0.45 + 0.45 * lower_leg)
    add_weight(weights, f"{side_prefix}Foot", 0.55 * foot)
    add_weight(weights, "Hips", 0.12 * (1.0 - lower_leg))
    return top4_normalized(weights)


def append_accessor(gltf: dict, binary: bytearray, payload: bytes, component_type: int, count: int, kind: str, name: str | None = None, minmax: tuple[list[float], list[float]] | None = None) -> int:
    align4(binary)
    offset = len(binary)
    binary.extend(payload)
    view = {"buffer": 0, "byteOffset": offset, "byteLength": len(payload)}
    gltf.setdefault("bufferViews", []).append(view)
    accessor = {"bufferView": len(gltf["bufferViews"]) - 1, "componentType": component_type, "count": count, "type": kind}
    if name:
        accessor["name"] = name
    if minmax:
        accessor["min"], accessor["max"] = minmax
    gltf.setdefault("accessors", []).append(accessor)
    return len(gltf["accessors"]) - 1


def global_joint_positions() -> dict[str, tuple[float, float, float]]:
    positions: dict[str, tuple[float, float, float]] = {}
    local = {name: loc for name, _, loc in JOINTS}
    parent = {name: parent for name, parent, _ in JOINTS}
    for name, _, _ in JOINTS:
        x = y = z = 0.0
        cur: str | None = name
        chain = []
        while cur is not None:
            chain.append(cur)
            cur = parent[cur]
        for item in reversed(chain):
            lx, ly, lz = local[item]
            x += lx
            y += ly
            z += lz
        positions[name] = (x, y, z)
    return positions


def inverse_bind_payload() -> bytes:
    payload = bytearray()
    positions = global_joint_positions()
    for name, _, _ in JOINTS:
        x, y, z = positions[name]
        # glTF matrices are column-major. This is inverse translation.
        payload.extend(struct.pack("<16f", 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, -x, -y, -z, 1))
    return bytes(payload)


def add_skin_and_weights(gltf: dict, binary: bytearray) -> None:
    positions = read_positions(gltf, binary)
    bounds = mesh_bounds(positions)
    joints_payload = bytearray()
    weights_payload = bytearray()
    for x, y, z in positions:
        weights = skin_weights_for_vertex(x, y, z, bounds)
        joints_payload.extend(struct.pack("<4H", *(joint for joint, _ in weights)))
        weights_payload.extend(struct.pack("<4f", *(weight for _, weight in weights)))

    count = len(positions)
    joints_accessor = append_accessor(gltf, binary, bytes(joints_payload), UNSIGNED_SHORT, count, "VEC4", "JOINTS_0")
    weights_accessor = append_accessor(gltf, binary, bytes(weights_payload), FLOAT, count, "VEC4", "WEIGHTS_0")
    inverse_bind_accessor = append_accessor(gltf, binary, inverse_bind_payload(), FLOAT, len(JOINTS), "MAT4", "inverseBindMatrices")

    primitive = gltf["meshes"][0]["primitives"][0]
    primitive.setdefault("attributes", {})["JOINTS_0"] = joints_accessor
    primitive["attributes"]["WEIGHTS_0"] = weights_accessor

    nodes = gltf.setdefault("nodes", [])
    root_index = len(nodes)
    nodes.append({"name": "JumpShotSkeletonRoot", "translation": [0, 0, 0]})
    joint_indices = []
    name_to_index = {}
    for name, parent, translation in JOINTS:
        index = len(nodes)
        name_to_index[name] = index
        joint_indices.append(index)
        nodes.append({"name": name, "translation": list(translation)})
        parent_index = root_index if parent is None else name_to_index[parent]
        nodes[parent_index].setdefault("children", []).append(index)

    for name, translation in [
        ("BallReleaseAnchor", (0.18, 0.72, -0.58)),
        ("JerseyNumberAnchor", (0.0, 0.42, 0.34)),
        ("JerseyNameAnchor", (0.0, 0.68, 0.34)),
    ]:
        index = len(nodes)
        nodes.append({"name": name, "translation": list(translation)})
        nodes[root_index].setdefault("children", []).append(index)

    mesh_node = next((node for node in gltf.get("nodes", []) if node.get("mesh") == 0), None)
    if mesh_node is None:
        raise ValueError("could not find mesh node for mesh 0")
    skin_index = len(gltf.setdefault("skins", []))
    gltf["skins"].append({"name": "JumpShotHumanoidSkin", "joints": joint_indices, "skeleton": root_index, "inverseBindMatrices": inverse_bind_accessor})
    mesh_node["skin"] = skin_index
    gltf["scenes"][gltf.get("scene", 0)].setdefault("nodes", []).append(root_index)
    gltf.setdefault("extras", {})["jumpshotAutorig"] = {
        "version": 2,
        "method": "bounds-adaptive blended procedural weights",
        "jointCount": len(JOINTS),
        "maxInfluences": 4,
        "bounds": {
            "min": list(bounds["min"]),
            "max": list(bounds["max"]),
            "size": list(bounds["size"]),
        },
    }


def add_animations(gltf: dict, binary: bytearray) -> None:
    node_index_by_name = {node.get("name"): i for i, node in enumerate(gltf.get("nodes", []))}
    animations = gltf.setdefault("animations", [])
    for clip_name, keyframes in CLIPS.items():
        times = [frame[0] for frame in keyframes]
        input_accessor = append_accessor(
            gltf,
            binary,
            struct.pack(f"<{len(times)}f", *times),
            FLOAT,
            len(times),
            "SCALAR",
            f"{clip_name}_time",
            ([min(times)], [max(times)]),
        )
        samplers = []
        channels = []
        root_frames = ROOT_TRANSLATIONS.get(clip_name)
        if root_frames:
            root_times = [frame[0] for frame in root_frames]
            root_input_accessor = append_accessor(
                gltf,
                binary,
                struct.pack(f"<{len(root_times)}f", *root_times),
                FLOAT,
                len(root_times),
                "SCALAR",
                f"{clip_name}_root_time",
                ([min(root_times)], [max(root_times)]),
            )
            root_values = [component for _, value in root_frames for component in value]
            root_output_accessor = append_accessor(
                gltf,
                binary,
                struct.pack(f"<{len(root_values)}f", *root_values),
                FLOAT,
                len(root_frames),
                "VEC3",
                f"{clip_name}_root_translation",
            )
            sampler_index = len(samplers)
            samplers.append({"input": root_input_accessor, "output": root_output_accessor, "interpolation": "LINEAR"})
            channels.append({"sampler": sampler_index, "target": {"node": node_index_by_name["JumpShotSkeletonRoot"], "path": "translation"}})
        animated_bones = sorted({bone for _, pose in keyframes for bone in pose})
        for bone in animated_bones:
            values = []
            for _, pose in keyframes:
                values.extend(quat_from_euler(*pose.get(bone, (0.0, 0.0, 0.0))))
            output_accessor = append_accessor(
                gltf,
                binary,
                struct.pack(f"<{len(values)}f", *values),
                FLOAT,
                len(keyframes),
                "VEC4",
                f"{clip_name}_{bone}_rotation",
            )
            sampler_index = len(samplers)
            samplers.append({"input": input_accessor, "output": output_accessor, "interpolation": "LINEAR"})
            channels.append({"sampler": sampler_index, "target": {"node": node_index_by_name[bone], "path": "rotation"}})
        animations.append({"name": clip_name, "samplers": samplers, "channels": channels})


def write_glb(path: Path, gltf: dict, binary: bytearray) -> None:
    align4(binary)
    gltf.setdefault("buffers", [{"byteLength": 0}])[0]["byteLength"] = len(binary)
    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    while len(json_bytes) % 4:
        json_bytes += b" "
    total = 12 + 8 + len(json_bytes) + 8 + len(binary)
    out = bytearray()
    out.extend(struct.pack("<III", 0x46546C67, 2, total))
    out.extend(struct.pack("<II", len(json_bytes), JSON_CHUNK))
    out.extend(json_bytes)
    out.extend(struct.pack("<II", len(binary), BIN_CHUNK))
    out.extend(binary)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    gltf, binary = load_glb(args.source)
    add_skin_and_weights(gltf, binary)
    add_animations(gltf, binary)
    gltf.setdefault("extras", {})["jumpshotAnimation"] = ANIMATION_METADATA
    write_glb(args.output, gltf, binary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
