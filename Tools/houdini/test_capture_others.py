import unreal
from pathlib import Path

OUT_DIR = Path("g:/film-304-toon-spine/Saved/Renders/FilmOffice")
OUT_DIR.mkdir(parents=True, exist_ok=True)

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for cname in ["Film_Cam_OfficeWide", "Film_Cam_David_DeskSleep", "CineCam_Hero_WindowEstablishing"]:
    cam = None
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == cname:
            cam = a
            break
    if cam:
        filename = str(OUT_DIR / f"test_{cname.lower()}.png")
        print(f"Capturing from {cname} to {filename}...")
        unreal.AutomationLibrary.take_high_res_screenshot(
            res_x=1920, res_y=1080,
            filename=filename,
            camera=cam,
            mask_enabled=False, capture_hdr=False,
            force_game_view=True
        )
