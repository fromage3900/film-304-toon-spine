import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== ALL CINECAMERAS IN LEVEL ===")
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.CineCameraActor):
        c = a.get_cine_camera_component()
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        fl = c.current_focal_length
        ap = c.current_aperture
        fd = c.focus_settings.manual_focus_distance
        print(f"Camera: {a.get_actor_label()}")
        print(f"  Loc: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}) | Rot: (P={rot.pitch:.1f}, Y={rot.yaw:.1f}, R={rot.roll:.1f})")
        print(f"  FocalLength: {fl:.1f}mm | Aperture: f/{ap:.1f} | FocusDist: {fd:.1f}cm")
