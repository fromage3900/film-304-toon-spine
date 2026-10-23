import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
print("Actors near the back/side wall around X: -250 to 100, Y: 400 to 800:")
for a in eas.get_all_level_actors():
    loc = a.get_actor_location()
    if -300 <= loc.x <= 300 and 400 <= loc.y <= 900:
        bounds = a.get_actor_bounds(False)
        print(f"  {a.get_actor_label()} ({a.get_class().get_name()}) Loc={loc} Extent={bounds[1]}")
