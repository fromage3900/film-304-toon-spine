import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== CLUTTER ACTORS TRANSFORMS ===")
for a in eas.get_all_level_actors():
    if "clutter" in a.get_actor_label().lower():
        print(f"{a.get_actor_label()}: Loc={a.get_actor_location()}, Rot={a.get_actor_rotation()}, Scale={a.get_actor_scale3d()}")
