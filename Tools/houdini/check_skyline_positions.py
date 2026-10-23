import unreal

print("=== CHECKING SKYLINE TOWERS AND WHAT IS OUTSIDE WINDOW ===")
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    lbl = a.get_actor_label()
    if any(k in lbl.lower() for k in ["tower", "civic", "skyline", "cable", "spotlight"]):
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        sc = a.get_actor_scale3d()
        print(f"Actor: {lbl} | Pos: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}) | Rot: ({rot.pitch:.1f}, {rot.yaw:.1f}, {rot.roll:.1f}) | Scale: ({sc.x:.2f}, {sc.y:.2f}, {sc.z:.2f})")

print("\n=== CHECKING MATERIAL ON SM_Glass_WindowBay_01..03 ===")
for bay_id in ["01", "02", "03"]:
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_actor_label() == f"SM_Glass_WindowBay_{bay_id}":
            smc = a.get_component_by_class(unreal.StaticMeshComponent)
            mats = [smc.get_material(i).get_path_name() if smc.get_material(i) else "None" for i in range(smc.get_num_materials())]
            print(f"{a.get_actor_label()}: Mesh={smc.static_mesh.get_name() if smc.static_mesh else 'None'}, Mats={mats}, Pos={a.get_actor_location()}")
