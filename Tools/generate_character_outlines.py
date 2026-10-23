"""Generate inverted-hull outline meshes for a character FBX via geometry nodes.

Usage:
  blender --background --factory-startup --python Tools/generate_character_outlines.py -- \
      <input.fbx> <output.fbx>

Duplicates each mesh, applies MEL_InvertedHullOutline (thickness 0.012), and
exports the outline meshes (plus their armatures) to <output.fbx>.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "Saved" / "Audit" / "InvertedHullOutlines"


def main():
    argv = sys.argv
    if "--" not in argv:
        raise SystemExit("expected -- <input.fbx> <output.fbx>")
    args = argv[argv.index("--") + 1:]
    if len(args) < 2:
        raise SystemExit("expected <input.fbx> <output.fbx>")
    in_path, out_path = args[0], args[1]

    # rebuild GN group directly
    sys.path.insert(0, str(ROOT/"Tools"))
    sys.path.insert(0, str(ROOT/'Tools'))
    import build_inverted_hull_outline_gn
    build_inverted_hull_outline_gn.build()
    ng = bpy.data.node_groups["MEL_InvertedHullOutline"]

    bpy.ops.import_scene.fbx(filepath=in_path, use_anim=False)

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    armatures = [o for o in bpy.data.objects if o.type == "ARMATURE"]

    outline_objects = []
    for obj in meshes:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.duplicate()
        dup = bpy.context.active_object
        dup.name = obj.name + "_Outline"
        mod = dup.modifiers.new(name="InvertedHull", type="NODES")
        mod.node_group = ng
        try:
            mod.properties.inputs.Socket_1.value = 0.012
        except Exception:
            pass
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name, keep_shapekeys=False)
        except Exception:
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception:
                pass
        outline_objects.append(dup)

    bpy.ops.object.select_all(action="DESELECT")
    for o in armatures + outline_objects:
        o.select_set(True)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=str(out),
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        apply_unit_scale=True,
        global_scale=1.0,
        bake_space_transform=False,
        add_leaf_bones=False,
        primary_bone_axis="Y",
        secondary_bone_axis="X",
        use_mesh_modifiers=False,
        mesh_smooth_type="FACE",
        path_mode="COPY",
    )

    report = {
        "schema": "humber-inverted-hull-outline.v1",
        "input": in_path,
        "output": out_path,
        "source_mesh_count": len(meshes),
        "outline_mesh_count": len(outline_objects),
        "armature_count": len(armatures),
        "thickness": 0.012,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / (Path(out).stem + "_report.json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("OUTLINE_JSON" + json.dumps(report))


if __name__ == "__main__":
    main()




