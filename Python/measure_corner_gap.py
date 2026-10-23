import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for name in ["Film_West_NorthReturnWall", "Film_NorthWall_Full"]:
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == name:
            origin, extent = a.get_actor_bounds(False)
            loc = a.get_actor_location()
            rot = a.get_actor_rotation()
            scale = a.get_actor_scale3d()
            print(f"{name}: Loc={loc} Rot={rot} Scale={scale}")
            print(f"  Bounds: X=[{origin.x - extent.x:.1f}, {origin.x + extent.x:.1f}] Y=[{origin.y - extent.y:.1f}, {origin.y + extent.y:.1f}] Z=[{origin.z - extent.z:.1f}, {origin.z + extent.z:.1f}]")
