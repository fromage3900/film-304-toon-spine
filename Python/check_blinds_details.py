import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = eas.get_all_level_actors()

for a in actors:
    lbl = a.get_actor_label()
    if "Blind" in lbl or "Glass" in lbl or "Mullion" in lbl:
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        loc = a.get_actor_location()
        scale = a.get_actor_scale3d()
        rot = a.get_actor_rotation()
        print(f"{lbl} Loc: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}) Scale: ({scale.x:.1f}, {scale.y:.1f}, {scale.z:.1f}) Rot: (p={rot.pitch:.1f}, y={rot.yaw:.1f}, r={rot.roll:.1f}) Vis: {a.is_hidden_ed()}")

