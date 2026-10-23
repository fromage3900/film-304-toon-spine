import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl in ["SM_VenetianBlind_Bay_01", "SM_VenetianBlind_Bay_02", "SM_VenetianBlind_Bay_03"]:
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        bounds = a.get_actor_bounds(False)
        mats = [smc.get_material(i).get_name() if smc.get_material(i) else "None" for i in range(smc.get_num_materials())]
        hidden = smc.get_editor_property("hidden_in_game")
        print(f"{lbl}: Origin={bounds[0]} BoxExtent={bounds[1]} HiddenInGame={hidden} Mesh={smc.static_mesh.get_name()} Mats={mats}")
