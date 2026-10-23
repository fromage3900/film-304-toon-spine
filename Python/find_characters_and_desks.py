import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== DAVID AND DESKS ===")
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if any(k in lbl for k in ["David", "Dana", "Sam", "Desk"]):
        loc = a.get_actor_location()
        print(f"Actor: {lbl} | Class: {a.get_class().get_name()} | Loc: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f})")
