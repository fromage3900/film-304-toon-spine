import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== CHECKING ALL ACTORS IN OFFICE AREA ===")
for a in eas.get_all_level_actors():
    smc = a.get_component_by_class(unreal.StaticMeshComponent)
    if smc and smc.static_mesh:
        loc = a.get_actor_location()
        lbl = a.get_actor_label()
        mesh_name = smc.static_mesh.get_name()
        mats = []
        for i in range(smc.get_num_materials()):
            mat = smc.get_material(i)
            mats.append(mat.get_name() if mat else "None")
        
        has_default = any("WorldGrid" in m or "Default" in m for m in mats)
        if has_default or "Troffer" in lbl or "Wall" in lbl or "Panel" in lbl or "Box" in lbl or "Infill" in lbl or "Cube" in mesh_name:
            print(f"{lbl:35} | mesh={mesh_name:25} | loc=({loc.x:6.1f},{loc.y:6.1f},{loc.z:6.1f}) | mats={mats}")
