#!/usr/bin/env python3
"""Generate a lightweight LeBron-inspired runtime GLB for JumpShot.

This is a handcrafted placeholder asset for validating the GLB runtime path.
It is not a real-player scan and should be replaced by the offline Blender
pipeline once generated source meshes are available.
"""

from __future__ import annotations

import base64
import json
import math
import struct
from pathlib import Path

import numpy as np


OUT = Path(__file__).resolve().parents[2] / "assets/players/lebron-inspired/player.glb"

COLORS = {
    "skin": [0.47, 0.30, 0.19, 1.0],
    "hair": [0.035, 0.032, 0.03, 1.0],
    "jersey": [0.24, 0.10, 0.42, 1.0],
    "gold": [1.0, 0.73, 0.12, 1.0],
    "white": [0.93, 0.91, 0.84, 1.0],
    "black": [0.02, 0.025, 0.03, 1.0],
}


def normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v if n == 0 else v / n


def transform(vertices: np.ndarray, scale=(1, 1, 1), translate=(0, 0, 0)) -> np.ndarray:
    return vertices * np.array(scale, dtype=np.float32) + np.array(translate, dtype=np.float32)


def uv_sphere(rx: float, ry: float, rz: float, rows=14, cols=24):
    verts = []
    normals = []
    idx = []
    for r in range(rows + 1):
        phi = math.pi * r / rows
        for c in range(cols):
            theta = math.tau * c / cols
            x = math.sin(phi) * math.cos(theta)
            y = math.cos(phi)
            z = math.sin(phi) * math.sin(theta)
            verts.append([x * rx, y * ry, z * rz])
            normals.append(normalize(np.array([x / rx, y / ry, z / rz], dtype=np.float32)))
    for r in range(rows):
        for c in range(cols):
            a = r * cols + c
            b = r * cols + (c + 1) % cols
            d = (r + 1) * cols + c
            e = (r + 1) * cols + (c + 1) % cols
            idx.extend([a, d, b, b, d, e])
    return np.array(verts, dtype=np.float32), np.array(normals, dtype=np.float32), np.array(idx, dtype=np.uint32)


def cylinder(radius: float, height: float, segments=18, axis="y"):
    verts = []
    normals = []
    idx = []
    for y in [-height / 2, height / 2]:
        for s in range(segments):
            a = math.tau * s / segments
            x = math.cos(a) * radius
            z = math.sin(a) * radius
            verts.append([x, y, z])
            normals.append([math.cos(a), 0, math.sin(a)])
    for s in range(segments):
        a = s
        b = (s + 1) % segments
        c = segments + s
        d = segments + (s + 1) % segments
        idx.extend([a, c, b, b, c, d])
    # caps
    bottom_center = len(verts)
    verts.append([0, -height / 2, 0])
    normals.append([0, -1, 0])
    top_center = len(verts)
    verts.append([0, height / 2, 0])
    normals.append([0, 1, 0])
    for s in range(segments):
        b = (s + 1) % segments
        idx.extend([bottom_center, b, s])
        idx.extend([top_center, segments + s, segments + b])
    verts = np.array(verts, dtype=np.float32)
    normals = np.array(normals, dtype=np.float32)
    if axis == "x":
        verts = verts[:, [1, 0, 2]]
        normals = normals[:, [1, 0, 2]]
    elif axis == "z":
        verts = verts[:, [0, 2, 1]]
        normals = normals[:, [0, 2, 1]]
    return verts, normals, np.array(idx, dtype=np.uint32)


def box(w: float, h: float, d: float):
    x, y, z = w / 2, h / 2, d / 2
    faces = [
        ([[-x, -y, z], [x, -y, z], [x, y, z], [-x, y, z]], [0, 0, 1]),
        ([[x, -y, -z], [-x, -y, -z], [-x, y, -z], [x, y, -z]], [0, 0, -1]),
        ([[-x, y, z], [x, y, z], [x, y, -z], [-x, y, -z]], [0, 1, 0]),
        ([[-x, -y, -z], [x, -y, -z], [x, -y, z], [-x, -y, z]], [0, -1, 0]),
        ([[x, -y, z], [x, -y, -z], [x, y, -z], [x, y, z]], [1, 0, 0]),
        ([[-x, -y, -z], [-x, -y, z], [-x, y, z], [-x, y, -z]], [-1, 0, 0]),
    ]
    verts, normals, idx = [], [], []
    for corners, normal in faces:
        start = len(verts)
        verts.extend(corners)
        normals.extend([normal] * 4)
        idx.extend([start, start + 1, start + 2, start, start + 2, start + 3])
    return np.array(verts, dtype=np.float32), np.array(normals, dtype=np.float32), np.array(idx, dtype=np.uint32)


def add_mesh(meshes, name, geom, material, scale=(1, 1, 1), translate=(0, 0, 0)):
    verts, normals, idx = geom
    meshes.append(
        {
            "name": name,
            "positions": transform(verts, scale, (0, 0, 0)),
            "normals": normals.astype(np.float32),
            "indices": idx.astype(np.uint32),
            "material": material,
            "translation": translate,
        }
    )


def build_meshes():
    meshes = []
    add_mesh(meshes, "Body", uv_sphere(0.42, 0.78, 0.25), "skin", translate=(0, 1.47, 0))
    add_mesh(meshes, "Head", uv_sphere(0.24, 0.31, 0.23), "skin", translate=(0, 2.47, -0.02))
    add_mesh(meshes, "Hair", uv_sphere(0.255, 0.105, 0.235), "hair", translate=(0, 2.68, -0.02))
    add_mesh(meshes, "HeadbandFront", box(0.46, 0.055, 0.035), "black", translate=(0, 2.59, -0.245))
    add_mesh(meshes, "HeadbandBack", box(0.42, 0.055, 0.035), "black", translate=(0, 2.59, 0.205))
    add_mesh(meshes, "HeadbandLeft", box(0.035, 0.055, 0.39), "black", translate=(-0.245, 2.59, -0.02))
    add_mesh(meshes, "HeadbandRight", box(0.035, 0.055, 0.39), "black", translate=(0.245, 2.59, -0.02))
    add_mesh(meshes, "Beard", box(0.32, 0.12, 0.08), "hair", translate=(0, 2.33, -0.22))
    add_mesh(meshes, "Jersey", uv_sphere(0.48, 0.52, 0.23), "jersey", scale=(1.08, 0.96, 1.0), translate=(0, 1.58, 0))
    add_mesh(meshes, "JerseyBackPanel", box(0.68, 0.68, 0.025), "jersey", translate=(0, 1.57, -0.245))
    add_mesh(meshes, "JerseyCollarBack", box(0.42, 0.055, 0.035), "gold", translate=(0, 2.05, -0.23))
    add_mesh(meshes, "JerseyTrimLeft", box(0.04, 0.72, 0.035), "gold", translate=(-0.45, 1.54, -0.225))
    add_mesh(meshes, "JerseyTrimRight", box(0.04, 0.72, 0.035), "gold", translate=(0.45, 1.54, -0.225))
    add_mesh(meshes, "Shorts", box(0.82, 0.38, 0.44), "jersey", translate=(0, 0.91, 0.02))
    add_mesh(meshes, "ShortsTrim", box(0.82, 0.04, 0.44), "gold", translate=(0, 0.70, 0.02))
    add_mesh(meshes, "LeftShoulder", uv_sphere(0.18, 0.16, 0.15), "skin", translate=(-0.58, 1.99, -0.02))
    add_mesh(meshes, "RightShoulder", uv_sphere(0.18, 0.16, 0.15), "skin", translate=(0.58, 1.99, -0.02))
    add_mesh(meshes, "LeftArm", cylinder(0.112, 0.94), "skin", scale=(1, 1, 1), translate=(-0.69, 1.48, -0.02))
    add_mesh(meshes, "RightArm", cylinder(0.112, 0.94), "skin", translate=(0.69, 1.48, -0.02))
    add_mesh(meshes, "LeftWristband", cylinder(0.118, 0.11), "black", translate=(-0.62, 1.02, -0.02))
    add_mesh(meshes, "RightWristband", cylinder(0.118, 0.11), "gold", translate=(0.62, 1.02, -0.02))
    add_mesh(meshes, "LeftLeg", cylinder(0.14, 0.88), "skin", translate=(-0.25, 0.43, 0.02))
    add_mesh(meshes, "RightLeg", cylinder(0.14, 0.88), "skin", translate=(0.25, 0.43, 0.02))
    add_mesh(meshes, "LeftKneePad", cylinder(0.145, 0.12), "black", translate=(-0.24, 0.54, -0.01))
    add_mesh(meshes, "RightKneePad", cylinder(0.145, 0.12), "black", translate=(0.24, 0.54, -0.01))
    add_mesh(meshes, "SocksLeft", cylinder(0.135, 0.28), "white", translate=(-0.24, 0.20, 0.02))
    add_mesh(meshes, "SocksRight", cylinder(0.135, 0.28), "white", translate=(0.24, 0.20, 0.02))
    add_mesh(meshes, "ShoesLeft", box(0.37, 0.16, 0.62), "white", translate=(-0.25, 0.08, -0.13))
    add_mesh(meshes, "ShoesRight", box(0.37, 0.16, 0.62), "white", translate=(0.25, 0.08, -0.13))
    add_mesh(meshes, "ShoeGoldLeft", box(0.25, 0.035, 0.50), "gold", translate=(-0.25, 0.17, -0.14))
    add_mesh(meshes, "ShoeGoldRight", box(0.25, 0.035, 0.50), "gold", translate=(0.25, 0.17, -0.14))
    return meshes


def create_texture_png() -> str:
    # Tiny neutral texture embedded so the GLB carries at least one image source.
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAEklEQVR4nGP8z8Dwn4GBgYGJAQATbwICoh/x3AAAAABJRU5ErkJggg=="
    )
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")


def write_glb(meshes):
    buffers = bytearray()
    buffer_views = []
    accessors = []
    gltf_meshes = []
    nodes = []

    def align():
        while len(buffers) % 4:
            buffers.append(0)

    def add_accessor(data: bytes, component_type: int, count: int, acc_type: str, minmax=None):
        align()
        offset = len(buffers)
        buffers.extend(data)
        buffer_views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(data)})
        accessor = {
            "bufferView": len(buffer_views) - 1,
            "componentType": component_type,
            "count": count,
            "type": acc_type,
        }
        if minmax:
            accessor["min"] = minmax[0]
            accessor["max"] = minmax[1]
        accessors.append(accessor)
        return len(accessors) - 1

    mat_index = {
        key: i
        for i, key in enumerate(["skin", "hair", "jersey", "gold", "white", "black"])
    }
    materials = [
        {
            "name": f"{key}_material",
            "pbrMetallicRoughness": {
                "baseColorFactor": COLORS[key],
                "roughnessFactor": 0.54 if key in {"skin", "white"} else 0.68,
                "metallicFactor": 0.0,
            },
        }
        for key in mat_index
    ]

    for part in meshes:
        pos = part["positions"].astype(np.float32)
        nor = part["normals"].astype(np.float32)
        idx = part["indices"].astype(np.uint32)
        pos_acc = add_accessor(
            pos.tobytes(),
            5126,
            len(pos),
            "VEC3",
            ([float(v) for v in pos.min(axis=0)], [float(v) for v in pos.max(axis=0)]),
        )
        nor_acc = add_accessor(nor.tobytes(), 5126, len(nor), "VEC3")
        idx_acc = add_accessor(idx.tobytes(), 5125, len(idx), "SCALAR")
        gltf_meshes.append(
            {
                "name": part["name"],
                "primitives": [
                    {
                        "attributes": {"POSITION": pos_acc, "NORMAL": nor_acc},
                        "indices": idx_acc,
                        "material": mat_index[part["material"]],
                    }
                ],
            }
        )
        nodes.append(
            {
                "name": part["name"],
                "mesh": len(gltf_meshes) - 1,
                "translation": [float(v) for v in part["translation"]],
            }
        )

    nodes.append({"name": "BallReleaseAnchor", "translation": [0.18, 2.48, -0.48]})
    nodes.append({"name": "JerseyNumberAnchor"})
    nodes.append({"name": "JerseyNameAnchor"})

    scene_nodes = list(range(len(nodes)))
    gltf = {
        "asset": {"version": "2.0", "generator": "JumpShot procedural GLB generator"},
        "scene": 0,
        "scenes": [{"nodes": scene_nodes}],
        "nodes": nodes,
        "meshes": gltf_meshes,
        "materials": materials,
        "buffers": [{"byteLength": len(buffers)}],
        "bufferViews": buffer_views,
        "accessors": accessors,
        "images": [{"name": "tiny_reference_texture", "uri": create_texture_png()}],
    }

    json_chunk = json.dumps(gltf, separators=(",", ":")).encode("utf8")
    while len(json_chunk) % 4:
        json_chunk += b" "
    align()
    bin_chunk = bytes(buffers)
    while len(bin_chunk) % 4:
        bin_chunk += b"\0"

    total_len = 12 + 8 + len(json_chunk) + 8 + len(bin_chunk)
    out = bytearray()
    out.extend(struct.pack("<4sII", b"glTF", 2, total_len))
    out.extend(struct.pack("<I4s", len(json_chunk), b"JSON"))
    out.extend(json_chunk)
    out.extend(struct.pack("<I4s", len(bin_chunk), b"BIN\0"))
    out.extend(bin_chunk)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(out)


def main():
    write_glb(build_meshes())
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
