import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    loc = a.get_actor_location()
    dist = ((loc.x - 220)**2 + (loc.y - -180)**2 + (loc.z - 110)**2)**0.5
    if dist < 200:
        print(f"Near camera: {a.get_actor_label()} ({a.get_class().get_name()}) at {loc}")
