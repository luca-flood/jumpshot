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

CLIPS = {
    "idle": [(0.0, {}), (1.0, {"Chest": (1, 0, -1)}), (2.0, {})],
    "dribble_idle": [
        (0.0, {"LeftUpperArm": (-8, 0, -14), "RightUpperArm": (10, 0, 18), "LeftUpperLeg": (5, 0, 0), "RightUpperLeg": (-5, 0, 0)}),
        (0.5, {"LeftUpperArm": (10, 0, -10), "RightUpperArm": (-12, 0, 12), "LeftUpperLeg": (-5, 0, 0), "RightUpperLeg": (5, 0, 0)}),
        (1.0, {"LeftUpperArm": (-8, 0, -14), "RightUpperArm": (10, 0, 18), "LeftUpperLeg": (5, 0, 0), "RightUpperLeg": (-5, 0, 0)}),
    ],
    "gather": [
        (0.0, {}),
        (0.18, {"Hips": (-8, 0, 0), "Spine": (-6, 0, 0), "Chest": (-5, 0, -3), "LeftUpperLeg": (18, 0, -2), "RightUpperLeg": (18, 0, 2), "LeftUpperArm": (-18, 0, -24), "RightUpperArm": (-22, 0, 22)}),
        (0.3, {"Spine": (3, 0, 0), "Chest": (7, 0, -4), "LeftUpperArm": (-58, 4, -26), "RightUpperArm": (-68, -2, 18)}),
    ],
    "jump": [
        (0.0, {"Spine": (3, 0, 0), "Chest": (7, 0, -4), "LeftUpperArm": (-58, 4, -26), "RightUpperArm": (-68, -2, 18)}),
        (0.2, {"Hips": (2, 0, 0), "Spine": (8, 0, -2), "Chest": (14, 0, -6), "LeftUpperArm": (-96, 5, -18), "LeftForeArm": (-72, 0, 18), "RightUpperArm": (-112, -3, 12), "RightForeArm": (-82, 0, -18)}),
    ],
    "release": [
        (0.0, {"Chest": (14, 0, -6), "RightUpperArm": (-112, -3, 12), "RightForeArm": (-82, 0, -18)}),
        (0.12, {"Chest": (16, 0, -8), "LeftUpperArm": (-98, 4, -42), "RightUpperArm": (-124, -4, 8), "RightForeArm": (-88, 0, -26), "RightHand": (-34, 0, -38)}),
    ],
    "follow_through": [
        (0.0, {"Chest": (16, 0, -8), "LeftUpperArm": (-98, 4, -42), "RightUpperArm": (-124, -4, 8), "RightForeArm": (-88, 0, -26), "RightHand": (-34, 0, -38)}),
        (0.55, {"Chest": (12, 0, -5), "LeftUpperArm": (-70, 2, -48), "RightUpperArm": (-118, -2, 8), "RightForeArm": (-70, 0, -24), "RightHand": (-28, 0, -34), "LeftUpperLeg": (-12, 0, -10)}),
    ],
    "land": [
        (0.0, {"Chest": (12, 0, -5), "RightUpperArm": (-90, -2, 8)}),
        (0.25, {"Hips": (-2, 0, 0), "Chest": (1, 0, -1), "LeftUpperArm": (-8, 0, -10), "RightUpperArm": (-8, 0, 10)}),
    ],
}

ROOT_TRANSLATIONS = {
    "gather": [(0.0, (0.0, 0.0, 0.0)), (0.18, (0.0, -0.035, 0.0)), (0.3, (0.0, 0.0, -0.015))],
    "jump": [(0.0, (0.0, 0.0, -0.015)), (0.2, (0.0, 0.12, -0.05))],
    "release": [(0.0, (0.0, 0.12, -0.05)), (0.12, (0.0, 0.17, -0.08))],
    "follow_through": [(0.0, (0.0, 0.17, -0.08)), (0.55, (0.0, 0.05, -0.11))],
    "land": [(0.0, (0.0, 0.04, -0.07)), (0.25, (0.0, 0.0, 0.0))],
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


def joint_for_vertex(x: float, y: float, z: float) -> int:
    if y > 0.68:
        return 4
    if y > 0.32:
        if x < -0.22:
            return 5 if y > 0.52 else 6
        if x > 0.22:
            return 8 if y > 0.52 else 9
        return 2
    if y > -0.1:
        return 1
    if x < -0.06:
        return 11 if y > -0.55 else 12
    if x > 0.06:
        return 14 if y > -0.55 else 15
    return 0


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
    joints_payload = bytearray()
    weights_payload = bytearray()
    for x, y, z in positions:
        joint = joint_for_vertex(x, y, z)
        joints_payload.extend(struct.pack("<4H", joint, 0, 0, 0))
        weights_payload.extend(struct.pack("<4f", 1.0, 0.0, 0.0, 0.0))

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

    mesh_node = gltf["nodes"][1]
    skin_index = len(gltf.setdefault("skins", []))
    gltf["skins"].append({"name": "JumpShotHumanoidSkin", "joints": joint_indices, "skeleton": root_index, "inverseBindMatrices": inverse_bind_accessor})
    mesh_node["skin"] = skin_index
    gltf["scenes"][gltf.get("scene", 0)].setdefault("nodes", []).append(root_index)


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
    write_glb(args.output, gltf, binary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
