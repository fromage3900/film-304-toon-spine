import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = eas.get_all_level_actors()

print("--- WINDOW BAYS & EXTERIOR ACTORS ---")
for a in actors:
    lbl = a.get_actor_label()
    if any(k in lbl for k in ["Glass_WindowBay", "VenetianBlind", "Ext_", "Horizon", "EST_", "BackWall", "NorthWall", "West_"]):
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        scale = a.get_actor_scale3d()
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        mesh_name = smc.static_mesh.get_name() if (smc and smc.static_mesh) else "None"
        mats = [smc.get_material(i).get_name() if smc.get_material(i) else "None" for i in range(smc.get_num_materials())] if smc else []
        print(f"Actor: {lbl} Mesh: {mesh_name} Loc: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}) Scale: ({scale.x:.1f}, {scale.y:.1f}, {scale.z:.1f}) Mats: {mats}")
