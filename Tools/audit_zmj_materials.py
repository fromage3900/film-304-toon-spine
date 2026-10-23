import unreal
import json
from pathlib import Path
REPO = Path(unreal.Paths.project_dir())

zmj_meshes = [
    "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_Counter_ZMJ_FilmStage_20261016",
    "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_CounterTop_ZMJ_FilmStage_20261016",
    "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_EspressoMachine_ZMJ_FilmStage_20261016",
    "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_Fridge_ZMJ_FilmStage_20261016",
    "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_Cabinet_ZMJ_FilmStage_20261016",
    "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_BreakRoomShelf_ZMJ_FilmStage_20261016",
    "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_CoffeeBag_ZMJ_FilmStage_20261016",
    "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_CoffeeMugLarge_ZMJ_FilmStage_20261016",
    "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_PastryCover_ZMJ_FilmStage_20261016",
    "/Game/Staging/OneDriveRigs_20261016/Environment/SM_O_Pastry_ZMJ_FilmStage_20261016",
    "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_BreakroomTable_AC_FilmStage_20261016",
    "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_Chair_KS_FilmStage_20261016",
    "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_OfficeDesk_AC_FilmStage_20261016",
    "/Game/Staging/OneDriveRigs_20261016/Environment/SM_P_DeskDrawers_SG_FilmStage_20261016"
]

res = {}
for path in zmj_meshes:
    mesh = unreal.load_asset(path)
    if not mesh:
        res[path] = "NOT_FOUND"
        continue
    slots = []
    for sm in mesh.get_editor_property("static_materials"):
        slot_name = str(sm.material_slot_name)
        mat = sm.material_interface.get_path_name() if sm.material_interface else None
        slots.append({"slot": slot_name, "material": mat})
    bounds = mesh.get_bounds()
    res[mesh.get_name()] = {
        "path": path,
        "extent_uu": [round(bounds.box_extent.x, 2), round(bounds.box_extent.y, 2), round(bounds.box_extent.z, 2)],
        "slots": slots
    }

out_file = REPO / "Saved" / "Audit" / "HoudiniBrutalist" / "zmj_materials_audit.json"
out_file.parent.mkdir(parents=True, exist_ok=True)
out_file.write_text(json.dumps(res, indent=2), encoding="utf-8")
unreal.log(f"[ZMJ_Audit] Wrote audit to {out_file}")
