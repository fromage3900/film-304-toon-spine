import unreal
actors = unreal.EditorLevelLibrary.get_all_level_actors()
for a in actors:
    label = a.get_actor_label()
    if label in ("Film_Cast_David","Film_Cast_Sam"):
        comp = a.get_component_by_class(unreal.SkeletalMeshComponent)
        print(label)
        if comp:
            for i in range(comp.get_num_materials()):
                m = comp.get_material(i)
                print("  slot", i, ":", m.get_path_name() if m else None)
