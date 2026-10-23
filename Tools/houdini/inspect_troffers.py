import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if "Troffer" in lbl or "Panel" in lbl:
        loc = a.get_actor_location()
        scale = a.get_actor_scale3d()
        rot = a.get_actor_rotation()
        bounds = a.get_actor_bounds(False)
        print(f"{lbl:30} | loc=({loc.x:6.1f},{loc.y:6.1f},{loc.z:6.1f}) | scale=({scale.x:6.2f},{scale.y:6.2f},{scale.z:6.2f}) | ext=({bounds[1].x:6.1f},{bounds[1].y:6.1f},{bounds[1].z:6.1f})")
