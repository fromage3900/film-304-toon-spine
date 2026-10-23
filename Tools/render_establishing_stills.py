"""Renders high-res still captures from the 5 Film 304 Master Establishing Cameras."""
import json
import time
from pathlib import Path
import unreal

REPO = Path(unreal.Paths.project_dir())
OUT_DIR = REPO / "Saved" / "Renders" / "establishing_shots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MAP_PACKAGE = "/Game/Maps/Lookdev/UniversalFilm_20261016/L_Toon_Office_ProceduralVariants"
ELL = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ELL.load_level(MAP_PACKAGE)

SHOTS = [
    {"camera_label": "Cam_SH010_ExteriorVista", "stem": "EST_SH010_ExteriorVista"},
    {"camera_label": "Cam_SH020_CubicleBay", "stem": "EST_SH020_CanonicalCubicles"},
    {"camera_label": "Cam_SH090_BreakRoom", "stem": "EST_SH090_BreakRoomSanctuary"},
    {"camera_label": "Cam_SH080_MazeTracking", "stem": "EST_SH080_Labyrinth"},
    {"camera_label": "Cam_SH030_DeskOverShoulder", "stem": "EST_SH030_HeroDesk"},
    {"camera_label": "Cam_SH060_CalendarMacro", "stem": "EST_SH060_CalendarMacro"},
]

def find_camera(label):
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None

results = []
for s in SHOTS:
    cam = find_camera(s["camera_label"])
    if not cam:
        unreal.log(f"[RenderStills] WARNING: Camera {s['camera_label']} not found!")
        continue

    stem = s["stem"]
    target_path = str(OUT_DIR / stem)
    unreal.log(f"[RenderStills] Capturing {s['camera_label']} -> {target_path}.png")

    task = unreal.AutomationLibrary.take_high_res_screenshot(
        res_x=1280, res_y=720,
        filename=target_path,
        camera=cam,
        mask_enabled=False,
        capture_hdr=False,
        force_game_view=True
    )
    results.append({
        "camera": s["camera_label"],
        "stem": stem,
        "output": f"{target_path}.png"
    })

unreal.log(f"[RenderStills] Fired {len(results)} high-res still captures.")
