import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "HDA_Cubicle_Hive":
        a.set_actor_location(unreal.Vector(825.0, -400.0, 0.0), False, False)
        print("Set HDA_Cubicle_Hive location to (825, -400, 0)")
        loc = a.get_actor_location()
        print("New location:", loc)
        origin, extent = a.get_actor_bounds(False)
        print("  Bounds Origin:", origin)
        print("  Bounds Extent:", extent)

LES.save_current_level()
