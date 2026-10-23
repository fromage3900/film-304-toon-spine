import unreal
import json
from pathlib import Path

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
OUT.mkdir(parents=True, exist_ok=True)

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# 1. Seal window gap completely
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_Ext_Bay3_CompanionTower":
        a.set_actor_location(unreal.Vector(-260.0, 3100.0, -300.0), False, False)
        a.set_actor_scale3d(unreal.Vector(3.2, 2.0, 1.8))
        a.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=25.0, roll=0.0), False)
        print("Scaled and sealed SM_Ext_Bay3_CompanionTower")
        break

# Helper to spawn or get CineCamera
def setup_cine_cam(label, loc, rot, focal_len, aperture, focus_dist):
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
    fb.sensor_height = 20.25 # 16:9
    cine.filmback = fb
    
    focus = cine.focus_settings
    focus.focus_method = unreal.CameraFocusMethod.MANUAL
    focus.manual_focus_distance = focus_dist
    cine.focus_settings = focus
    
    return cam

# Shot 1: The Narrative Master
cam1_loc = unreal.Vector(257.2, -197.5, 98.8)
cam1_rot = unreal.Rotator(pitch=-0.1, yaw=128.3, roll=0.0)
cam1 = setup_cine_cam("Film_Cam_Showcase_Ensemble_v02", cam1_loc, cam1_rot, 35.0, 2.8, 310.0)

# Shot 2: Dana Hero Close-Up Portrait
# Target Dana head: (15.9, 35.2, 85.0)
dana_head = unreal.Vector(15.9, 35.2, 85.0)
cam2_loc = unreal.Vector(110.0, -62.0, 89.0)
cam2_rot = unreal.MathLibrary.find_look_at_rotation(cam2_loc, dana_head)
dist2 = (dana_head - cam2_loc).length()
cam2 = setup_cine_cam("Film_Cam_Showcase_DanaPortrait_v02", cam2_loc, cam2_rot, 85.0, 2.5, dist2)

# Shot 3: Late-Night Crunch Rake (Low-Angle Desk Level)
# David is at (-142.4, -36.9, 50.0). Camera resting low near edge of desk looking across to David and room
david_head = unreal.Vector(-142.4, -36.9, 50.0)
cam3_loc = unreal.Vector(-45.0, -180.0, 72.0)
cam3_rot = unreal.MathLibrary.find_look_at_rotation(cam3_loc, david_head)
dist3 = (david_head - cam3_loc).length()
cam3 = setup_cine_cam("Film_Cam_Showcase_LowAngleRake_v02", cam3_loc, cam3_rot, 24.0, 3.2, dist3)

specs = {
    "Shot1_Ensemble": {
        "camera": cam1.get_actor_label(),
        "location": [cam1_loc.x, cam1_loc.y, cam1_loc.z],
        "rotation": [cam1_rot.pitch, cam1_rot.yaw, cam1_rot.roll],
        "focal_length_mm": 35.0,
        "aperture": 2.8,
        "focus_distance_cm": 310.0,
        "sensor_mm": [36.0, 20.25]
    },
    "Shot2_DanaPortrait": {
        "camera": cam2.get_actor_label(),
        "location": [cam2_loc.x, cam2_loc.y, cam2_loc.z],
        "rotation": [cam2_rot.pitch, cam2_rot.yaw, cam2_rot.roll],
        "focal_length_mm": 85.0,
        "aperture": 2.5,
        "focus_distance_cm": round(dist2, 1),
        "sensor_mm": [36.0, 20.25]
    },
    "Shot3_LowAngleRake": {
        "camera": cam3.get_actor_label(),
        "location": [cam3_loc.x, cam3_loc.y, cam3_loc.z],
        "rotation": [cam3_rot.pitch, cam3_rot.yaw, cam3_rot.roll],
        "focal_length_mm": 24.0,
        "aperture": 3.2,
        "focus_distance_cm": round(dist3, 1),
        "sensor_mm": [36.0, 20.25]
    }
}

(OUT / "showcase_cameras_calibrated.json").write_text(json.dumps(specs, indent=2), encoding="utf-8")
print("Showcase cameras calibrated successfully:")
print(json.dumps(specs, indent=2))
