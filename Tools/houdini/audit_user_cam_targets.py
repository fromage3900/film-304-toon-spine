import unreal
import math

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== EXACT USER CAMERA SIGHTLINE & TARGET AUDIT ===")

user_cams = [
    "SESSION_CAM_Cast",
    "Film_Cam_OfficeWide",
    "Film_Cam_OfficeMedium",
    "CineCam_Hero_WindowEstablishing",
    "CineCam_Hero_DeskLineup",
    "CineCam_Hero_LowAngleTension",
    "Film_Cam_David_DeskSleep",
    "SESSION_CAM_Verify"
]

cast_actors = ["Film_Subject_Dana_v08_CleanSkin", "Film_Cast_David", "Film_Cast_Sam", "Film_Cast_Spider"]
cast_locs = {}
for a in EAS.get_all_level_actors():
    if a.get_actor_label() in cast_actors:
        cast_locs[a.get_actor_label()] = a.get_actor_location()

for cname in user_cams:
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == cname:
            loc = a.get_actor_location()
            rot = a.get_actor_rotation()
            focal = 35.0
            if isinstance(a, unreal.CineCameraActor):
                focal = a.get_cine_camera_component().current_focal_length
            print(f"\nCamera: {cname} (Focal={focal:.0f}mm)")
            print(f"  Location: ({loc.x:7.1f}, {loc.y:7.1f}, {loc.z:7.1f})")
            print(f"  Rotation: Pitch={rot.pitch:5.1f}, Yaw={rot.yaw:6.1f}, Roll={rot.roll:5.1f}")
            for cast_name, cloc in cast_locs.items():
                dx = cloc.x - loc.x
                dy = cloc.y - loc.y
                dz = cloc.z - loc.z
                dist = math.sqrt(dx*dx + dy*dy + dz*dz)
                dist_xy = math.sqrt(dx*dx + dy*dy)
                target_yaw = math.degrees(math.atan2(dy, dx))
                target_pitch = math.degrees(math.atan2(dz, dist_xy))
                yaw_diff = (target_yaw - rot.yaw + 180) % 360 - 180
                pitch_diff = target_pitch - rot.pitch
                print(f"    -> Sightline to {cast_name[:15]:15s}: Dist={dist:6.1f}cm, Offset Yaw={yaw_diff:5.1f}°, Pitch={pitch_diff:5.1f}°")
