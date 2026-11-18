import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_Houdini_Ceiling_HVAC_Grid":
        loc = a.get_actor_location()
        bounds = a.get_actor_bounds(False)
        print(f"SM_Houdini_Ceiling_HVAC_Grid bounds:")
        print(f"  loc: {loc}")
        print(f"  origin: {bounds[0]}")
        print(f"  extent: {bounds[1]}")
        print(f"  min_z: {bounds[0].z - bounds[1].z}, max_z: {bounds[0].z + bounds[1].z}")
