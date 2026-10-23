import unreal
from pathlib import Path

OUT_DIR = Path("g:/film-304-toon-spine/Saved/Renders/FilmOffice")
OUT_DIR.mkdir(parents=True, exist_ok=True)

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "SESSION_CAM_Cast":
        a.set_actor_location(unreal.Vector(898.7, -685.6, 184.6), False, False)
        a.set_actor_rotation(unreal.Rotator(pitch=2.2, yaw=140.8, roll=0.0), False)
        comp = a.get_cine_camera_component()
        comp.focus_settings.focus_method = unreal.CameraFocusMethod.MANUAL
        comp.focus_settings.manual_focus_distance = 1154.0
        comp.current_aperture = 2.8
        print("Restored SESSION_CAM_Cast to exact original hero framing: (898.7, -685.6, 184.6), Yaw=140.8")
        
        filename = str(OUT_DIR / "hero_cast_with_horizon.png")
        unreal.AutomationLibrary.take_high_res_screenshot(
            res_x=1920, res_y=1080,
            filename=filename,
            camera=a,
            mask_enabled=False, capture_hdr=False,
            force_game_view=True
        )
        print("Captured hero_cast_with_horizon.png")
