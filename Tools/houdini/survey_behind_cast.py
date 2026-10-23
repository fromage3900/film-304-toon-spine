import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== ACTORS DIRECTLY BEHIND CAST DESK (X < 0, Y in [-200, 500]) ===")
for a in EAS.get_all_level_actors():
    loc = a.get_actor_location()
    if -500.0 <= loc.x <= 50.0 and -300.0 <= loc.y <= 600.0 and loc.z >= 0.0:
        lbl = a.get_actor_label()
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        mesh_name = smc.get_editor_property("static_mesh").get_name() if smc and smc.get_editor_property("static_mesh") else "NoMesh"
        mat_name = smc.get_material(0).get_name() if smc and smc.get_material(0) else "NoMat"
        print(f"  {lbl:35s} | Mesh: {mesh_name:25s} | Mat: {mat_name:30s} | Loc: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f})")
