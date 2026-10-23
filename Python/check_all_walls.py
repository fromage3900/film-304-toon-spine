import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
print("--- ALL WALL AND ENCLOSURE ACTORS ---")
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if any(k in lbl.lower() for k in ["wall", "window", "door", "glass", "mullion", "blind", "header", "pillar", "column"]):
        loc = a.get_actor_location()
        scale = a.get_actor_scale3d()
        rot = a.get_actor_rotation()
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        mesh = smc.static_mesh.get_name() if smc and smc.static_mesh else "None"
        print(f"Actor: {lbl} Mesh: {mesh} Loc: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}) Rot: (p={rot.pitch:.1f}, y={rot.yaw:.1f}, r={rot.roll:.1f}) Scale: ({scale.x:.1f}, {scale.y:.1f}, {scale.z:.1f})")
