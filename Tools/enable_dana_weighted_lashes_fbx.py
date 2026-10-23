"""Create a non-destructive FBX preview with intended weighted lashes visible."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
import os
import sys
sys.path.insert(0, os.path.join(os.environ.get("BLENDER_DIR", r"C:\Program Files\Blender Foundation\Blender 4.5"), "4.5", "scripts", "addons_core"))
from io_scene_fbx import data_types, encode_bin, parse_fbx

TARGETS = {"EyelashUpperLower_L", "EyelashUpperLower_R", "FaceDeformationSystem"}
METHODS = {
    data_types.BOOL: "add_bool", data_types.CHAR: "add_char",
    data_types.INT8: "add_int8", data_types.INT16: "add_int16",
    data_types.INT32: "add_int32", data_types.INT64: "add_int64",
    data_types.FLOAT32: "add_float32", data_types.FLOAT64: "add_float64",
    data_types.BYTES: "add_bytes", data_types.STRING: "add_string",
    data_types.INT32_ARRAY: "add_int32_array", data_types.INT64_ARRAY: "add_int64_array",
    data_types.FLOAT32_ARRAY: "add_float32_array", data_types.FLOAT64_ARRAY: "add_float64_array",
    data_types.BOOL_ARRAY: "add_bool_array", data_types.BYTE_ARRAY: "add_byte_array",
}

def child(node, key):
    return next((x for x in node.elems if x.id == key), None)

def text(v):
    return v.decode("utf-8", "replace").split("\x00")[0] if isinstance(v, bytes) else str(v)

def write_node(node):
    out = encode_bin.FBXElem(node.id)
    for typ, value in zip(node.props_type, node.props):
        method = METHODS.get(typ)
        if not method:
            raise RuntimeError("Unsupported FBX property type " + repr(typ))
        if typ == data_types.BOOL: value = bool(value)
        elif typ in (data_types.FLOAT32, data_types.FLOAT64): value = float(value)
        getattr(out, method)(value)
    out.elems = [write_node(x) for x in node.elems]
    return out

def visibility(model):
    block = child(model, b"Properties70")
    if not block: return None
    for p in block.elems:
        if p.id == b"P" and p.props and text(p.props[0]) == "Visibility":
            return p
    return None

def main(source, target):
    source, target = Path(source), Path(target)
    if not source.is_file(): raise RuntimeError("Source FBX missing: " + str(source))
    if target.exists(): raise RuntimeError("Refusing to overwrite preview: " + str(target))
    root, version = parse_fbx.parse(str(source))
    objects = child(root, b"Objects").elems
    models = {text(o.props[1]).split(":")[-1]: o for o in objects
              if o.id == b"Model" and o.props}
    found = {}
    for name in TARGETS:
        model = models.get(name)
        if model is None: raise RuntimeError("Missing lash model: " + name)
        prop = visibility(model)
        if prop is None: raise RuntimeError("Missing Visibility property: " + name)
        old = float(prop.props[4])
        prop.props[4] = 1.0
        # Blender's FBX importer skips properties marked user-defined ('U')
        # and therefore keeps these models hidden. Use the normal FBX default
        # flag on this preview-only visibility property.
        prop.props[3] = b""
        found[name] = {"before": old, "after": float(prop.props[4])}
    target.parent.mkdir(parents=True, exist_ok=True)
    encode_bin.write(str(target), write_node(root), version)
    checked, read_version = parse_fbx.parse(str(target))
    checked_objects = child(checked, b"Objects").elems
    checked_models = {text(o.props[1]).split(":")[-1]: o for o in checked_objects
                      if o.id == b"Model" and o.props}
    for name in TARGETS:
        prop = visibility(checked_models[name])
        if prop is None or float(prop.props[4]) != 1.0 or b"U" in prop.props[3]:
            raise RuntimeError("Visibility readback failed: " + name)
    # Require invariant counts and skin deformation objects to match exactly.
    src_objects = child(root, b"Objects").elems
    dst_objects = checked_objects
    count = lambda arr, kind: sum(o.id == kind for o in arr)
    for kind in (b"Geometry", b"Deformer", b"Model"):
        if count(src_objects, kind) != count(dst_objects, kind):
            raise RuntimeError("FBX object count changed: " + text(kind))
    report = {"result": "pass", "source": str(source), "output": str(target),
              "fbx_version": version, "readback_version": read_version,
              "visible_lashes": found,
              "object_counts": {text(kind): count(dst_objects, kind)
                                for kind in (b"Geometry", b"Deformer", b"Model")},
              "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "output_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
              "scope": "Visibility flags on intended weighted lashes and their hidden facial deformation parent; source file untouched."}
    audit = target.with_suffix(".json")
    audit.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    if len(sys.argv) == 3:
        source, target = sys.argv[1], sys.argv[2]
    else:
        import os
        source = os.environ.get("DANA_LASH_SOURCE")
        target = os.environ.get("DANA_LASH_TARGET")
        if not source or not target:
            raise SystemExit("set DANA_LASH_SOURCE and DANA_LASH_TARGET")
    main(source, target)
