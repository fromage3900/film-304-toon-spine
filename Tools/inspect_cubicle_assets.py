import unreal
import json

meshes = [
    "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_Canonical",
    "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_MazeShift",
    "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_OpenPlan",
    "/Game/Environment/Brutalist/04_INTERIOR_CUBICLES/SM_CUBICLE_Swarm",
    "/Game/Meshes/Office/Props/Desk",
    "/Game/Meshes/Office/Props/DeskDrawers",
    "/Game/Meshes/Office/Props/P_Chair_KS",
    "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_OfficeDesk_AC_FilmStage_20261016",
    "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_DeskDrawers_SG_FilmStage_20261016",
    "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Chair_KS_FilmStage_20261016"
]

info = {}
for m_path in meshes:
    asset = unreal.load_asset(m_path)
    if not asset:
        info[m_path] = "NOT_FOUND"
        continue
    bounds = asset.get_bounds()
    box_extent = bounds.box_extent
    mats = [str(mat.material_slot_name) for mat in asset.get_editor_property("static_materials")]
    info[asset.get_name()] = {
        "path": m_path,
        "extent_uu": [round(box_extent.x, 2), round(box_extent.y, 2), round(box_extent.z, 2)],
        "materials": mats
    }

unreal.log("[CubicleAudit] " + json.dumps(info, indent=2))
print(json.dumps(info, indent=2))
