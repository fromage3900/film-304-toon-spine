import unreal
from pathlib import Path

OUT_DIR = Path("g:/film-304-toon-spine/Saved/Renders/FilmOffice")
OUT_DIR.mkdir(parents=True, exist_ok=True)

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

glass_mat = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Glass")
print("Loaded MI_Toon_Glass:", glass_mat)

for a in EAS.get_all_level_actors():
    if "glass_windowbay" in a.get_actor_label().lower():
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc and glass_mat:
            smc.set_material(0, glass_mat)
            print(f"Assigned MI_Toon_Glass to {a.get_actor_label()}")

# Capture preview
for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "SESSION_CAM_Cast":
        filename = str(OUT_DIR / "transparent_glass_preview.png")
        print("Capturing transparent glass preview...")
        unreal.AutomationLibrary.take_high_res_screenshot(
            res_x=1920, res_y=1080,
            filename=filename,
            camera=a,
            mask_enabled=False, capture_hdr=False,
            force_game_view=True
        )
