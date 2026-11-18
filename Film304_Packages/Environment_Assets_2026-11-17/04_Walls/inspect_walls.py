import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if 'Wall' in lbl or 'Header' in lbl or 'Perimeter' in lbl:
        loc = a.get_actor_location()
        bounds = a.get_actor_bounds(False)
        print(f"{lbl:35} | loc=({loc.x:6.1f}, {loc.y:6.1f}, {loc.z:6.1f}) | bounds_origin=({bounds[0].x:6.1f}, {bounds[0].y:6.1f}, {bounds[0].z:6.1f}) | bounds_ext=({bounds[1].x:6.1f}, {bounds[1].y:6.1f}, {bounds[1].z:6.1f}) | top_z={bounds[0].z + bounds[1].z:6.1f}")
