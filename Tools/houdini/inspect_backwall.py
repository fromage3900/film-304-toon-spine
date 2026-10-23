import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in EAS.get_all_level_actors():
    if a.get_actor_label() in ["Film_BackWall", "Film_WarmWallPanel"]:
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        print(f"Actor: {a.get_actor_label()}")
        print(f"  Mesh: {smc.get_editor_property('static_mesh').get_name() if smc else 'None'}")
        print(f"  Loc: {a.get_actor_location()}")
        origin, extent = a.get_actor_bounds(False)
        print(f"  Bounds Origin: {origin}, Extent: {extent}")
