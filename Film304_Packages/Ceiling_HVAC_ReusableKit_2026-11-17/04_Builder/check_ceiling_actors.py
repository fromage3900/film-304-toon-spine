import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
print("=== CHECKING ALL CEILING ACTORS ===")
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if any(k in lbl.lower() for k in ["ceiling", "hvac", "troffer"]):
        try:
            print(f"Actor: {lbl:42s} | Pos: {a.get_actor_location()} | Rot: {a.get_actor_rotation()}")
        except Exception as e:
            print(f"Actor {lbl} error: {e}")
