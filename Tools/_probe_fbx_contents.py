"""Report what an exported cast FBX actually contains, using Blender as an
independent reader of the file (Blender is not otherwise part of this pipeline).

Used to tell apart two very different failure modes that look identical from the
UE side - "the exporter only wrote one mesh" versus "the UE importer only read
one mesh" - by checking the file with a third party before touching UE again.

    blender --background --factory-startup --python Tools/_probe_fbx_contents.py -- <fbx>
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    import bpy

    argv = sys.argv
    fbx_path = argv[argv.index("--") + 1]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=fbx_path, use_anim=False)

    armatures = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    materials = [m.name for m in bpy.data.materials]

    per_mesh = []
    for obj in meshes:
        slots = sorted({slot.material.name for slot in obj.material_slots
                        if slot.material is not None})
        per_mesh.append({
            "name": obj.name,
            "parent": obj.parent.name if obj.parent else None,
            "vertices": len(obj.data.vertices),
            "polygons": len(obj.data.polygons),
            "materials": slots,
            "vertex_groups": len(obj.vertex_groups),
            "armature_modifier": any(m.type == "ARMATURE" for m in obj.modifiers),
        })

    report = {
        "fbx": fbx_path,
        "bytes": Path(fbx_path).stat().st_size,
        "armature_count": len(armatures),
        "armatures": [{"name": a.name, "bones": len(a.data.bones)} for a in armatures],
        "mesh_count": len(meshes),
        "materials": materials,
        "meshes": per_mesh,
    }

    out = ROOT / "Saved/Audit/CastMayaExport_20261016" / (
        "fbx_contents_%s.json" % Path(fbx_path).stem)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("FBX_JSON" + json.dumps({
        "fbx": Path(fbx_path).name,
        "armatures": report["armatures"],
        "mesh_count": len(meshes),
        "materials": materials,
        "written": str(out),
    }))


if __name__ == "__main__":
    main()