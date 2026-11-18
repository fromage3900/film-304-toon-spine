import os, shutil
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== SETTING FLAT CEILING WITH ZERO PITCH ===")
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl == "SM_Houdini_Ceiling_HVAC_Grid":
        a.set_actor_location(unreal.Vector(0.0, 0.0, 0.0), False, False)
        # Explicit keyword arguments: PITCH MUST BE 0.0! ROLL MUST BE 0.0! YAW IS -25.0!
        r = unreal.Rotator(pitch=0.0, yaw=-25.0, roll=0.0)
        a.set_actor_rotation(r, False)
        print(f"Set SM_Houdini_Ceiling_HVAC_Grid to flat: rot={a.get_actor_rotation()}")
        
    elif lbl in ["HOUDINI_SM_Houdini_Office_Ceiling_Metal", "HOUDINI_SM_Houdini_Office_Ceiling_Tiles"]:
        eas.destroy_actor(a)
        print(f"Removed duplicate {lbl}")

unreal.EditorLevelLibrary.save_current_level()

WORLD = unreal.EditorLevelLibrary.get_editor_world()
OUT_DIR = "G:/film-304-toon-spine/Saved/Renders/FilmOffice"
ARTIFACT_DIR = "C:/Users/froma/.gemini/antigravity-ide/brain/10d93b13-68af-4057-ae2d-343574ed43dd"

cam_actor = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SESSION_CAM_Cast":
        cam_actor = a
        break

if cam_actor:
    loc = cam_actor.get_actor_location()
    rot = cam_actor.get_actor_rotation()
    cc = cam_actor.get_component_by_class(unreal.CineCameraComponent)
    fov = cc.field_of_view if cc else 50.0
    
    rt = unreal.RenderingLibrary.create_render_target2d(WORLD, 1920, 1080, format=unreal.TextureRenderTargetFormat.RTF_RGBA8)
    cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, loc, rot)
    comp = cap.get_component_by_class(unreal.SceneCaptureComponent2D)
    comp.texture_target = rt
    comp.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
    comp.fov_angle = fov
    comp.capture_scene()
    
    out_name = "test_flat_ceiling_fix.png"
    unreal.RenderingLibrary.export_render_target(WORLD, rt, OUT_DIR, out_name)
    unreal.EditorLevelLibrary.destroy_actor(cap)
    shutil.copy2(f"{OUT_DIR}/{out_name}", f"{ARTIFACT_DIR}/{out_name}")
    print("Rendered test_flat_ceiling_fix.png")
