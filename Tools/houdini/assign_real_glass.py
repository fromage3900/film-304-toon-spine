import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
mat_toon_glass = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Glass")

for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if "WindowBay" in lbl or "Glass" in lbl:
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc:
            smc.set_material(0, mat_toon_glass)
            print(f"Assigned MI_Toon_Glass to {lbl}")

unreal.EditorLevelLibrary.save_current_level()
