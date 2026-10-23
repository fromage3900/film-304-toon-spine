import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cast_David":
        skm = a.skeletal_mesh_component
        print("David Skeletal Mesh:", skm.skeletal_mesh.get_path_name())
        for i in range(skm.get_num_materials()):
            mat = skm.get_material(i)
            print(f"  Slot {i}: {mat.get_path_name() if mat else 'None'}")
