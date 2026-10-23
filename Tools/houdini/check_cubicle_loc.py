import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "HDA_Cubicle_Hive":
        loc = a.get_actor_location()
        print("HDA_Cubicle_Hive current location:", loc)
        origin, extent = a.get_actor_bounds(False)
        print("  Bounds Origin:", origin)
        print("  Bounds Extent:", extent)
