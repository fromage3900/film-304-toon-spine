import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if any(k in lbl for k in ["Barbican", "SlenderTower", "TowerCluster"]):
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        scale = a.get_actor_scale3d()
        bounds = a.get_actor_bounds(False)
        print(f"{lbl} Loc={loc} Rot={rot} Scale={scale} BoxExtent={bounds[1]}")
