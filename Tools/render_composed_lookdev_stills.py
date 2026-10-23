"""Renders high-res viewport preview stills for the new Houdini Engine & VFX Composed Cameras in L_Film_Office."""
from pathlib import Path
import unreal

REPO = Path(unreal.Paths.project_dir())
OUT_DIR = REPO / "Saved" / "Renders" / "houdini_lookdev"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SHOTS = [
    {"camera_label": "CineCam_Hero_CubicleEstablishing", "stem": "COMP_HOUDINI_CubicleEstablishing_24mm"},
    {"camera_label": "CineCam_Hero_CubicleTrench", "stem": "COMP_HOUDINI_CubicleTrench_35mm"},
    {"camera_label": "CineCam_Hero_BreakroomEstablishing", "stem": "COMP_HOUDINI_BreakroomSanctuary_35mm"},
    {"camera_label": "CineCam_Hero_CorridorWatercooler", "stem": "COMP_HOUDINI_CorridorWatercooler_50mm"},
    {"camera_label": "CineCam_Hero_WindowEstablishing", "stem": "COMP_HOUDINI_WindowEstablishing_BlindsVFX_28mm"}
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

unreal.log(f"[RenderStills] Successfully queued {len(results)} composed high-res still captures.")
