import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    if isinstance(a, unreal.Light) or "Light" in a.get_actor_label():
        cname = a.get_class().get_name()
        loc = a.get_actor_location()
        print(f"LIGHT: {a.get_actor_label():30} | class={cname:20} | loc=({loc.x:6.1f},{loc.y:6.1f},{loc.z:6.1f})")
