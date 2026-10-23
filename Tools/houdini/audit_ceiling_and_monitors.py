import unreal

print("=== CHECKING CEILING TILES, HVAC, AND TROFFER ALIGNMENT ===")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if any(k in lbl.lower() for k in ["ceiling", "hvac", "troffer", "slab"]):
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        sc = a.get_actor_scale3d()
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        mesh_name = smc.static_mesh.get_name() if smc and smc.static_mesh else "None"
        mats = [smc.get_material(i).get_name() if smc.get_material(i) else "None" for i in range(smc.get_num_materials())] if smc else []
        print(f"Actor: {lbl:40s} | Mesh: {mesh_name:30s} | Pos: ({loc.x:7.1f},{loc.y:7.1f},{loc.z:7.1f}) | Rot: ({rot.pitch:5.1f},{rot.yaw:5.1f},{rot.roll:5.1f}) | Mats: {mats}")

print("\n=== CHECKING COMPUTER MONITORS ===")
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if any(k in lbl.lower() for k in ["monitor", "screen", "computer", "pc", "laptop"]):
        loc = a.get_actor_location()
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        mesh_name = smc.static_mesh.get_name() if smc and smc.static_mesh else "None"
        mats = [smc.get_material(i).get_name() if smc.get_material(i) else "None" for i in range(smc.get_num_materials())] if smc else []
        print(f"Monitor: {lbl:35s} | Mesh: {mesh_name:25s} | Mats: {mats} | Pos: ({loc.x:7.1f},{loc.y:7.1f},{loc.z:7.1f})")
