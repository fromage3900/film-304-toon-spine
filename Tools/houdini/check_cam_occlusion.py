import unreal
import math

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== CHECKING WHAT IS CURRENTLY IN FRONT OF USER CAMERAS ===")

user_cams = [
    "SESSION_CAM_Cast",
    "Film_Cam_OfficeWide",
    "Film_Cam_OfficeMedium",
    "CineCam_Hero_WindowEstablishing",
    "CineCam_Hero_DeskLineup",
    "SESSION_CAM_Verify",
    "SESSION_FaceReview_Dana",
    "SESSION_FaceReview_Sam",
    "Film_Cam_David_DeskSleep"
]

cam_actors = {}
for a in EAS.get_all_level_actors():
    if a.get_actor_label() in user_cams:
        cam_actors[a.get_actor_label()] = a

# First, let's find any actors within 300cm of each camera or in their forward cone
for name, cam in cam_actors.items():
    c_loc = cam.get_actor_location()
    c_rot = cam.get_actor_rotation()
    
    # Calculate forward vector
    pitch_rad = math.radians(c_rot.pitch)
    yaw_rad = math.radians(c_rot.yaw)
    fwd = unreal.Vector(
        math.cos(pitch_rad) * math.cos(yaw_rad),
        math.cos(pitch_rad) * math.sin(yaw_rad),
        math.sin(pitch_rad)
    )
    
    print(f"\nCamera: {name}")
    print(f"  Pos: ({c_loc.x:.1f}, {c_loc.y:.1f}, {c_loc.z:.1f})")
    print(f"  Forward: ({fwd.x:.2f}, {fwd.y:.2f}, {fwd.z:.2f}) (Yaw: {c_rot.yaw:.1f})")
    
    # Check staged actors
    for a in EAS.get_all_level_actors():
        lbl = a.get_actor_label()
        if any(tag in lbl for tag in ["HDA", "Houdini", "Troffer", "Whiteboard", "Clock", "Breakroom", "Cubicle"]):
            origin, extent = a.get_actor_bounds(False)
            
            # Check if camera is inside bounds
            inside_x = (origin.x - extent.x) <= c_loc.x <= (origin.x + extent.x)
            inside_y = (origin.y - extent.y) <= c_loc.y <= (origin.y + extent.y)
            inside_z = (origin.z - extent.z) <= c_loc.z <= (origin.z + extent.z)
            if inside_x and inside_y and inside_z:
                print(f"  >>> CRITICAL CLIPPING: Camera is INSIDE bounds of {lbl}!")
            
            # Vector from cam to object origin
            to_obj = unreal.Vector(origin.x - c_loc.x, origin.y - c_loc.y, origin.z - c_loc.z)
            dist = math.sqrt(to_obj.x**2 + to_obj.y**2 + to_obj.z**2)
            if dist > 0.1:
                dot = (to_obj.x * fwd.x + to_obj.y * fwd.y + to_obj.z * fwd.z) / dist
                if dot > 0.7 and dist < 1200.0:
                    print(f"  >>> OCCLUSION: {lbl} is DIRECTLY in front of camera! Dist={dist:.1f}cm, Dot={dot:.2f}")
