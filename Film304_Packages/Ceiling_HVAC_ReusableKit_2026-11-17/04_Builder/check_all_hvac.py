import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

actors = []
for a in eas.get_all_level_actors():
    if "HVAC" in a.get_actor_label():
        actors.append((a.get_actor_label(), a.get_actor_location(), a.get_actor_bounds(False)))

print(f"Total HVAC actors found: {len(actors)}")
for lbl, loc, b in actors:
    print(f"  {lbl} | loc={loc} | origin={b[0]}")
