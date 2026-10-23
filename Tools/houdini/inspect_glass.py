import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== WINDOW GLASS PROPERTIES ===")
for a in EAS.get_all_level_actors():
    if "glass" in a.get_actor_label().lower():
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc:
            print(f"Actor: {a.get_actor_label()}")
            for mi in range(smc.get_num_materials()):
                m = smc.get_material(mi)
                print(f"  Slot {mi}: {m.get_name() if m else 'None'} ({m.get_path_name() if m else ''})")
