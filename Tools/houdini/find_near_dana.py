import unreal, math

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

dana_loc = unreal.Vector(11.3, 28.9, -0.7)

for a in eas.get_all_level_actors():
    loc = a.get_actor_location()
    dx = loc.x - dana_loc.x
    dy = loc.y - dana_loc.y
    dz = loc.z - dana_loc.z
    dist = math.sqrt(dx*dx + dy*dy + dz*dz)
    if dist < 600.0:
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        m_name = smc.static_mesh.get_name() if smc and smc.static_mesh else "None"
        b = a.get_actor_bounds(False)
        print(f"{a.get_actor_label():35} | mesh={m_name:25} | dist={dist:5.1f} | loc=({loc.x:6.1f},{loc.y:6.1f},{loc.z:6.1f}) | ext=({b[1].x:5.1f},{b[1].y:5.1f},{b[1].z:5.1f})")
