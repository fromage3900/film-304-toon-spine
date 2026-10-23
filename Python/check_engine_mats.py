import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== CHECKING FOR ANY ENGINE / PROTOTYPE MATERIALS ===")

engine_mats = []
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    for comp in a.get_components_by_class(unreal.MeshComponent):
        for i in range(comp.get_num_materials()):
            mat = comp.get_material(i)
            mpath = mat.get_path_name() if mat else "None"
            if mpath.startswith("/Engine/") or "default" in mpath.lower() or "prototype" in mpath.lower():
                engine_mats.append((lbl, comp.get_name(), i, mpath))
                print(f"Engine/Prototype Mat: {lbl} [{i}] -> {mpath}")

print(f"Total Engine/Prototype slots found: {len(engine_mats)}")
