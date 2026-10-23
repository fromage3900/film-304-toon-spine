import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cast_Sam":
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        skm = a.skeletal_mesh_component
        anim = skm.animation_data.anim_to_play if skm and hasattr(skm, 'animation_data') else None
        print(f"Sam Current Status (READ ONLY):")
        print(f"  Location: ({loc.x:.2f}, {loc.y:.2f}, {loc.z:.2f})")
        print(f"  Rotation: (pitch={rot.pitch:.2f}, yaw={rot.yaw:.2f}, roll={rot.roll:.2f})")
        print(f"  Anim: {anim.get_path_name() if anim else 'None'}")
