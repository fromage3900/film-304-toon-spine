import unreal
from pathlib import Path

OUT_DIR = Path("g:/film-304-toon-spine/Saved/Renders/FilmOffice")
OUT_DIR.mkdir(parents=True, exist_ok=True)

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "Film_BackWall":
        root = a.get_editor_property("root_component")
        if root:
            root.set_visibility(False, True)
        print("Explicitly hid Film_BackWall root component!")

for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "SESSION_CAM_Cast":
        filename = str(OUT_DIR / "true_transparent_horizon_hero.png")
        unreal.AutomationLibrary.take_high_res_screenshot(
            res_x=1920, res_y=1080,
            filename=filename,
            camera=a,
            mask_enabled=False, capture_hdr=False,
            force_game_view=True
        )
        print("Captured true_transparent_horizon_hero.png")
