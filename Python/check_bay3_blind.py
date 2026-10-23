import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for lbl in ["SM_VenetianBlind_Bay_01", "SM_VenetianBlind_Bay_02", "SM_VenetianBlind_Bay_03"]:
    a = eas.get_actor_reference(f"/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office.L_Film_Office:PersistentLevel.{lbl}")
    if a:
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        bounds = a.get_actor_bounds(False)
        print(f"{lbl}: Origin={bounds[0]} BoxExtent={bounds[1]} Hidden={smc.is_hidden_in_game()} Mesh={smc.static_mesh.get_name()}")
    else:
        print(f"{lbl} NOT FOUND")
