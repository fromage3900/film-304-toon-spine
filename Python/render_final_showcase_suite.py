import unreal
import claireon
from pathlib import Path
import json

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
OUT.mkdir(parents=True, exist_ok=True)

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# 1. Fix HeroDressing_Sam_Lamp material
lamp_mat = unreal.load_asset("/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Env_SM_P_Lamp_EF_FilmStage_20261016")
for a in eas.get_all_level_actors():
    if "Lamp" in a.get_actor_label() and "HeroDressing" in a.get_actor_label():
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc and lamp_mat:
            for i in range(smc.get_num_materials()):
                smc.set_material(i, lamp_mat)
            print(f"Bound lamp material to {a.get_actor_label()}")

# 2. Fully seal Bay 3 window opening
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_Ext_Bay3_CompanionTower":
        a.set_actor_location(unreal.Vector(-180.0, 3100.0, -300.0), False, False)
        a.set_actor_scale3d(unreal.Vector(4.8, 2.0, 1.8))
        a.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=25.0, roll=0.0), False)
        print("Extended SM_Ext_Bay3_CompanionTower to fully seal the window opening")
        break

# Helper to configure CineCamera
def setup_cine(label, loc, rot, focal_len, aperture, focus_dist):
    cam = None
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == label:
            cam = a
            break
    if not cam:
        cam = eas.spawn_actor_from_class(unreal.CineCameraActor, loc)
        cam.set_actor_label(label)
        cam.set_folder_path("Film304/Showcase_20261018")
    else:
        cam.set_actor_location(loc, False, False)
    cam.set_actor_rotation(rot, False)
    
    cine = cam.get_cine_camera_component()
    cine.current_focal_length = focal_len
    cine.current_aperture = aperture
    
    fb = cine.filmback
    fb.sensor_width = 36.0
    fb.sensor_height = 20.25
    cine.filmback = fb
    
    focus = cine.focus_settings
    focus.focus_method = unreal.CameraFocusMethod.MANUAL
    focus.manual_focus_distance = focus_dist
    cine.focus_settings = focus
    return cam

# Shot 1: The Narrative Master (Ensemble)
cam1_loc = unreal.Vector(250.0, -210.0, 108.0)
cam1_rot = unreal.Rotator(pitch=-0.2, yaw=130.5, roll=0.0)
cam1 = setup_cine("Film_Cam_Showcase_Ensemble_v02", cam1_loc, cam1_rot, 32.0, 2.8, 295.0)

# Shot 2: Dana Hero Close-Up Portrait (Tight chest-up, 3/4 angle)
# Dana's head is around (15.9, 35.2, 85.0)
dana_head = unreal.Vector(15.9, 35.2, 85.0)
cam2_loc = unreal.Vector(85.0, -35.0, 85.0)
cam2_rot = unreal.MathLibrary.find_look_at_rotation(cam2_loc, dana_head)
dist2 = (dana_head - cam2_loc).length()
cam2 = setup_cine("Film_Cam_Showcase_DanaPortrait_v02", cam2_loc, cam2_rot, 85.0, 2.4, dist2)

# Shot 3: Late-Night Crunch Rake (Low-Angle Desk Level)
# David is at (-142.4, -36.9, 50.0)
david_head = unreal.Vector(-142.4, -36.9, 52.0)
cam3_loc = unreal.Vector(-25.0, -170.0, 68.0)
cam3_rot = unreal.MathLibrary.find_look_at_rotation(cam3_loc, david_head)
dist3 = (david_head - cam3_loc).length()
cam3 = setup_cine("Film_Cam_Showcase_LowAngleRake_v02", cam3_loc, cam3_rot, 28.0, 3.2, dist3)

# Render all 3 shots
shots = [
    ("showcase_final_shot1_ensemble.png", cam1),
    ("showcase_final_shot2_dana_portrait.png", cam2),
    ("showcase_final_shot3_lowangle_rake.png", cam3),
]

render_receipts = {}
for fname, cam_actor in shots:
    cloc = cam_actor.get_actor_location()
    crot = cam_actor.get_actor_rotation()
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(cloc, crot)
    res = claireon.slate_screenshot(target="level_viewport", filename=fname, directory=str(OUT))
    render_receipts[cam_actor.get_actor_label()] = {
        "filename": fname,
        "location": [cloc.x, cloc.y, cloc.z],
        "rotation": [crot.pitch, crot.yaw, crot.roll],
        "result": res
    }
    print(f"Rendered {fname}:", res.get("summary"))

# Save level
saved = unreal.EditorLoadingAndSavingUtils.save_current_level()
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
print(f"Level saved cleanly: {saved}")

(OUT / "final_showcase_render_receipts.json").write_text(json.dumps(render_receipts, indent=2), encoding="utf-8")
print("All final showcase renders completed and level saved!")
