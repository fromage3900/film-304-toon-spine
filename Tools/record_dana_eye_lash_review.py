"""Record evidence-led eye/lash review of the current Humber Dana outputs.

This is a local audit helper. It reads existing rendered images and FBX audit
reports; it does not modify Unreal assets or source FBX files.
"""
import json
from pathlib import Path
from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parents[1]
EYES = ROOT / "Saved/Audit/dana_eye_look_fix.json"
ANATOMY = ROOT / "Saved/Audit/dana_fbx_anatomy.json"
RENDER = ROOT / "Saved/Audit/dana_refined_uds_render_results.json"
OUT = ROOT / "Saved/Audit/dana_eye_lash_review.json"
LASH_PREVIEW = ROOT / "Saved/Exports/DanaImportAudit/Dana_Film_WeightedLashesVisible_Preview.json"
UNREAL_IMPORT = ROOT / "Saved/Audit/dana_lash_visibility_unreal_import.json"
COMPARE = ROOT / "Saved/Audit/dana_lash_visibility_comparison.json"


def img(path):
    image = Image.open(path).convert("RGB")
    stat = ImageStat.Stat(image.resize((160, 90)))
    return {"path": str(path), "resolution": list(image.size),
            "bytes": path.stat().st_size,
            "mean_rgb": [round(c, 2) for c in stat.mean]}


def main():
    eye_report = json.loads(EYES.read_text(encoding="utf-8"))
    anatomy = json.loads(ANATOMY.read_text(encoding="utf-8"))
    lash_preview = json.loads(LASH_PREVIEW.read_text(encoding="utf-8"))
    unreal_import = json.loads(UNREAL_IMPORT.read_text(encoding="utf-8"))
    comparison = json.loads(COMPARE.read_text(encoding="utf-8"))
    fbx = anatomy[0]
    rows = {row["name"].split(":")[-1]: row for row in fbx["meshes"]}
    lashes = {}
    for name in ("EyelashUpperLower_L", "EyelashUpperLower_R",
                 "Eyelashes_squint_Lf", "Eyelashes_squint_Rt"):
        row = rows.get(name)
        if row:
            lashes[name] = {"vertices": row["vertices"],
                "triangles": row["triangles"],
                "source_material": row["parts"][0]["material"],
                "weighted_groups": row["weighted_groups"],
                "unweighted_vertices": row["unweighted_vertices"]}
    render_rows = json.loads(RENDER.read_text(encoding="utf-8"))
    renders = []
    for row in render_rows:
        path = Path(row["image"])
        if path.exists():
            record = img(path)
            record.update({"shot": row["shot"], "exit_code": row["exit_code"],
                           "fresh_image": row["fresh_image"]})
            renders.append(record)
    detail_path = ROOT / "Saved/Renders/dana_refined_uds/DANA_REFINED_UDS_DAY_DETAIL_v01.png"
    if detail_path.exists():
        renders.append(img(detail_path) | {"shot": "DANA_REFINED_UDS_DAY_DETAIL_v01",
                                           "role": "focused DanaFilm eye material detail"})
    out = {
        "result": "visibility_flag_fix_roundtripped_unreal_imported_render_pending",
        "eye_material_gate": eye_report["result"],
        "eye_material_readback": eye_report["material_readback"],
        "visual_review": {
            "day_detail": "Sclera, warm iris, and pupil separate clearly in the focused still.",
            "lash_readability": "Only a faint upper lash edge is visible; distinct lash silhouette remains weak.",
            "limitation": "Reviewed render is a static T-pose material preview, not deformation proof."
        },
        "lash_fbx": lashes,
        "source_fbx": fbx["file"],
        "renders": renders,
        "visibility_preview": {"fbx": lash_preview, "unreal_import": unreal_import,
            "comparison_level": comparison,
            "render": {"path": str(ROOT / "Saved/Renders/dana_lash_compare/DANA_LASH_VISIBILITY_COMPARE_v01.png"),
                "exit_code": 0, "mrq_completed": True,
                "camera_binding_resolved": True, "visual_result": "invalid_black_frame",
                "limitation": "Headless game render returned black despite a resolved camera cut; not valid visual proof."}},
        "conclusion": "Both intended weighted lash models were explicitly hidden in the source FBX (Visibility=0.0), which Blender's FBX importer maps to hidden. A sidecar enables only these two models; geometry, deformers, model counts, and source export are preserved. Unreal imported it as a distinct SkeletalMesh and Skeleton. The comparison render is black, so visible lash behavior remains unproven.",
        "pending": ["Resolve black MRQ output and obtain a valid close-up comparison.",
                    "Verify the corrected lash pair is visible in Unreal.",
                    "If visible, compare against canonical Dana and decide whether sparse geometry or material still needs work.",
                    "Do not promote the preview skeleton or replace the canonical Dana asset."],
        "scope_note": "No FBX, rig, camera, or project source assets modified by this audit."
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(OUT), "result": out["result"],
                      "renders": len(renders), "lash_meshes": len(lashes)}, indent=2))


if __name__ == "__main__":
    main()
