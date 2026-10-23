import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== ALL LAMPS IN LEVEL ===")
for a in eas.get_all_level_actors():
    if "lamp" in a.get_actor_label().lower():
        loc = a.get_actor_location()
        print(f"Actor: {a.get_actor_label()} | Loc: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f})")
