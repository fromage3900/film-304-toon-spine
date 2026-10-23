"""Consolidate an exported cast FBX into one mesh per armature, for UE.

The legacy UE FBX importer creates exactly ONE SkeletalMesh per armature and
silently drops the rest, so a multi-mesh FBX never arrives as the single
skeletal mesh a character needs. Proven on 2026-10-16: Sam's 18-mesh export
imported as one mesh carrying 6 of its 12 materials; David's 16-mesh export
imported as one mesh named after one of its parts.

Blender's FBX exporter, by contrast, writes one armature object with one mesh
carrying every material as a slot - exactly the shape UE wants. So the
consolidation happens here, between the Maya export and the UE import:

    Maya (per-material meshes) -> this script -> UE (one skeletal mesh)

Meshes are grouped by the armature that deforms them and joined within their
group, so a character with a body system and a face system yields one mesh per
system instead of a pile of loose parts. Nothing is dropped: a mesh with no
armature modifier is reported as rigid and left in its own group.

    blender --background --factory-startup \
      --python Tools/consolidate_fbx_for_ue.py -- <in.fbx> <out.fbx>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "Saved/Audit/CastMayaExport_20261016"


def armature_of(obj):
    for mod in obj.modifiers:
        if mod.type == "ARMATURE" and mod.object is not None:
            return mod.object
    return None


def group_key(obj, armatures):
    """Stable join order: the first armature by name, so re-running is idempotent."""
    arm = armature_of(obj)
    if arm is None:
        return "__rigid__"
    if arm.name not in armatures:
        armatures[arm.name] = arm
    return arm.name


def main() -> None:
    import bpy

    argv = sys.argv
    in_path, out_path = argv[argv.index("--") + 1], argv[argv.index("--") + 2]

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=in_path, use_anim=False)

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    armatures = {}
    groups = {}
    for obj in meshes:
        groups.setdefault(group_key(obj, armatures), []).append(obj)

    joined = []
    for key in sorted(groups):
        members = groups[key]
        bpy.ops.object.select_all(action="DESELECT")
        for obj in members:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = members[0]
        if len(members) > 1:
            bpy.ops.object.join()
        target = bpy.context.view_layer.objects.active
        target.name = key if key != "__rigid__" else "RigidParts"
        joined.append({
            "group": key,
            "result_object": target.name,
            "merged_meshes": len(members),
            "slots": sorted({s.material.name for s in target.material_slots
                             if s.material is not None}),
            "polygons": len(target.data.polygons),
            "armature": (armature_of(target).name if armature_of(target) else None),
        })

    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.data.objects:
        if obj.type in {"MESH", "ARMATURE"}:
            obj.select_set(True)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=out_path,
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
        "schema": "humber-fbx-consolidation.v1",
        "input": in_path,
        "output": out_path,
        "input_mesh_count": len(meshes),
        "input_armatures": sorted(armatures),
        "groups": joined,
        "note": ("one UE SkeletalMesh is produced per armature; a character with "
                 "a body and a face system will import as two SkeletalMeshes"),
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / ("consolidation_%s.json" % Path(out_path).stem)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("CONSOLIDATION_JSON" + json.dumps(report))


if __name__ == "__main__":
    main()