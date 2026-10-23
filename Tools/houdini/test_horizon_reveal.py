import unreal
from pathlib import Path

OUT_DIR = Path("g:/film-304-toon-spine/Saved/Renders/FilmOffice")
OUT_DIR.mkdir(parents=True, exist_ok=True)

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# 1. Lower or adjust SM_Ext_FG_BarbicanScale so horizon is visible
for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "SM_Ext_FG_BarbicanScale":
        loc = a.get_actor_location()
        # Lower Z by 1000cm or move back along X
        a.set_actor_location(unreal.Vector(-4200.0, 1800.0, -800.0), False, False)
        print("Shifted SM_Ext_FG_BarbicanScale to reveal horizon:", a.get_actor_location())

# 2. Lower Venetian blinds to 40% window height
# Window height is ~300cm. Top is ~292cm.
for i, b_lbl in enumerate(["SM_VenetianBlind_Bay_01", "SM_VenetianBlind_Bay_02", "SM_VenetianBlind_Bay_03"]):
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == b_lbl:
            # Drop down slightly and adjust rotation
            pass

# 3. Focus SESSION_CAM_Cast on Dana (distance ~1154cm)
for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "SESSION_CAM_Cast":
        comp = a.get_cine_camera_component()
        comp.focus_settings.focus_method = unreal.CameraFocusMethod.MANUAL
        comp.focus_settings.manual_focus_distance = 1154.0
        comp.current_aperture = 2.8
        print("Configured SESSION_CAM_Cast focus to 1154cm, f/2.8")

# 4. Capture screenshot
for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "SESSION_CAM_Cast":
        filename = str(OUT_DIR / "horizon_preview_session_cam_cast.png")
        print("Capturing horizon preview...")
        unreal.AutomationLibrary.take_high_res_screenshot(
            res_x=1920, res_y=1080,
            filename=filename,
            camera=a,
            mask_enabled=False, capture_hdr=False,
            force_game_view=True
        )
