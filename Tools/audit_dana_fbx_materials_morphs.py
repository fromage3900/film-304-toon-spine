"""Raw FBX audit: materials, mesh->material bindings, blendshape channels, counts.

Extends Tools/audit_dana_eye_fbx.py (same Blender io_scene_fbx.parse_fbx approach,
no import into any DCC) to dump for EVERY mesh: material bindings, polygon and
triangle counts, and for the whole file: material list, bone (LimbNode) count,
BlendShape deformer/channel names, and morph Shape geometry names.

Run:  blender.exe --background --python audit_dana_fbx_materials_morphs.py -- <in.fbx> <out.json>
"""
import json
import sys
from pathlib import Path
from io_scene_fbx import parse_fbx


def child(node, key):
    return next((n for n in node.elems if n.id == key), None)


def children(node, key):
    return [n for n in node.elems if n.id == key]


def text(value):
    return value.decode("utf-8", "replace").split("\x00")[0] if isinstance(value, bytes) else str(value)


def prop_map(node):
    block = child(node, b"Properties70")
    result = {}
    if block:
        for p in block.elems:
            if p.id == b"P" and p.props:
                key = text(p.props[0])
                if key in {"Lcl Translation", "Lcl Rotation", "Lcl Scaling"}:
                    result[key] = [text(v) for v in p.props[4:]]
    return result


def get_props_array(node):
    return [p for p in node.props] if node.props else []


source = Path(sys.argv[sys.argv.index("--") + 1])
dest = Path(sys.argv[sys.argv.index("--") + 2])
root, version = parse_fbx.parse(str(source))
objects = child(root, b"Objects").elems
connections = child(root, b"Connections").elems

byid = {}
for o in objects:
    if o.props:
        try:
            byid[int(o.props[0])] = o
        except (ValueError, TypeError):
            pass

# OO parent map: child -> parent
parents = {}
for c in connections:
    if len(c.props) >= 3 and c.props[0] == b"OO":
        parents[int(c.props[1])] = int(c.props[2])

# OP connection map for deformer/geometry wiring: (child, parent) -> prop
op_links = []
for c in connections:
    if len(c.props) >= 4 and c.props[0] == b"OP":
        op_links.append((int(c.props[1]), int(c.props[2]), text(c.props[3])))

materials = [text(m.props[1]) for m in objects if m.id == b"Material" and m.props]
bones = [m for m in objects if m.id == b"Model" and m.props and text(m.props[-1]) in ("LimbNode", "Null")]

# BlendShape deformers and channels (channels connect OO to the BlendShape deformer)
blendshapes = {}
for d in objects:
    if d.id == b"Deformer" and d.props and text(d.props[-1]) == "BlendShape":
        channels = []
        for cid, pid in parents.items():
            if pid == int(d.props[0]):
                ch = byid.get(cid)
                if ch is not None and ch.id == b"Deformer" and text(ch.props[-1]) == "BlendShapeChannel":
                    channels.append(text(ch.props[1]))
        blendshapes[text(d.props[1])] = sorted(channels)

# Shape (morph target) geometries
shapes = [text(g.props[1]) for g in objects if g.id == b"Geometry" and g.props and text(g.props[-1]) == "Shape"]

# Mesh geometries: name, triangles, materials bound
geo_meshes = []
for g in objects:
    if g.id != b"Geometry" or not g.props or text(g.props[-1]) != "Mesh":
        continue
    verts = child(g, b"Vertices")
    faces = child(g, b"PolygonVertexIndex")
    # parse_fbx returns arrays: Vertices is a double array with 3 entries per vertex
    try:
        nv = len(verts.props[0]) // 3 if verts else 0
    except Exception:
        nv = 0
    tris = 0
    polys = 0
    if faces:
        raw_idx = faces.props[0]
        run = 0
        for v in raw_idx:  # element iteration; negative element closes the polygon
            if v < 0:
                polys += 1
                tris += max(run - 2, 0)  # a polygon of k edges -> k-2 triangles
                run = 0
            else:
                run += 1
    mats = []
    for cid, pid, prop in op_links:
        if pid == int(g.props[0]):
            m = byid.get(cid)
            if m is not None and m.id == b"Material":
                mats.append(text(m.props[1]))
    model_name = ""
    for mid, gid in parents.items():
        if gid == int(g.props[0]) and mid in byid:
            model_name = text(byid[mid].props[1])
    geo_meshes.append({"geometry": text(g.props[1]), "model": model_name, "vertices": nv,
                       "polygons": polys, "triangles": tris, "materials": sorted(set(mats))})

out = {"source": str(source), "fbx_version": version,
       "materials": sorted(materials),
       "material_count": len(materials),
       "bone_models": len(bones),
       "bone_names_sample": sorted(text(m.props[1]) for m in bones)[:5],
       "blendshapes": blendshapes,
       "morph_shape_geometries": sorted(shapes),
       "meshes": sorted(geo_meshes, key=lambda m: m["geometry"])}
dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps({"source": str(source), "materials": out["materials"], "material_count": out["material_count"],
                  "bone_models": out["bone_models"], "blendshapes": out["blendshapes"],
                  "morph_shape_geometries": out["morph_shape_geometries"],
                  "meshes": [{"geometry": m["geometry"], "vertices": m["vertices"], "polygons": m["polygons"],
                              "triangles": m["triangles"], "materials": m["materials"]} for m in out["meshes"]]}, indent=1))
