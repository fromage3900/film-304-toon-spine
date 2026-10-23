"""Read Dana's source FBX eye geometry and eye-bone rest transforms without importing it."""
import json
import sys
from pathlib import Path
from io_scene_fbx import parse_fbx

def child(node, key):
    return next((n for n in node.elems if n.id == key), None)

def text(value):
    return value.decode("utf-8", "replace").split("\x00")[0] if isinstance(value, bytes) else str(value)

def prop_map(node):
    block = child(node, b"Properties70")
    result = {}
    if block:
        for p in block.elems:
            if p.id == b"P" and p.props:
                key = text(p.props[0])
                if key in {"Lcl Translation", "Lcl Rotation", "Lcl Scaling", "PreRotation", "PostRotation", "GeometricTranslation", "GeometricRotation", "GeometricScaling"}:
                    result[key] = [text(v) for v in p.props[4:]]
    return result

source = Path(sys.argv[sys.argv.index("--") + 1])
root, version = parse_fbx.parse(str(source))
objects = child(root, b"Objects").elems
connections = child(root, b"Connections").elems
models = [o for o in objects if o.id == b"Model" and o.props and o.props[-1] in (b"LimbNode", b"Mesh")]
byid = {int(o.props[0]): o for o in objects if o.props}
parents = {}
for c in connections:
    if len(c.props) >= 3 and c.props[0] == b"OO":
        parents[int(c.props[1])] = int(c.props[2])
wanted = ("Eye_L", "Eye_R", "Iris_L", "Iris_R", "Pupil_L", "Pupil_R")
bones = []
for m in models:
    n = text(m.props[1])
    if any(n.endswith(":" + w) for w in wanted):
        parent = byid.get(parents.get(int(m.props[0])))
        bones.append({"name": n, "kind": text(m.props[-1]), "parent": text(parent.props[1]) if parent else None, "properties": prop_map(m)})
geometries = []
for g in objects:
    if g.id != b"Geometry" or not g.props or g.props[-1] != b"Mesh":
        continue
    mn = next((text(byid[p].props[1]) for gid,p in parents.items() if gid == int(g.props[0]) and p in byid), "")
    if "Dana_Eye_" not in mn and "Dana_Cornea_" not in mn and "Dana_EyeInt_" not in mn:
        continue
    color = child(g, b"LayerElementColor")
    colors = None
    if color:
        values = child(color, b"Colors")
        colors = {"mapping": text(child(color,b"MappingInformationType").props[0]) if child(color,b"MappingInformationType") else None,
                  "reference": text(child(color,b"ReferenceInformationType").props[0]) if child(color,b"ReferenceInformationType") else None,
                  "count": len(values.props[0]) // 4 if values else 0,
                  "sample": [list(values.props[0][i:i+4]) for i in range(0,min(len(values.props[0]),24),4)] if values else []}
    geometries.append({"model":mn, "has_vertex_color": bool(color), "color_data":colors})
out = {"source":str(source),"fbx_version":version,"eye_bones":bones,"eye_geometry":geometries}
dest=Path("G:/film-304-toon-spine/Saved/Audit/dana_eye_fbx_transform.json")
dest.write_text(json.dumps(out,indent=2),encoding="utf-8")
print(json.dumps(out,indent=2))
