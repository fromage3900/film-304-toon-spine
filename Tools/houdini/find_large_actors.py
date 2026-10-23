import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    smc = a.get_component_by_class(unreal.StaticMeshComponent)
    if smc:
        bounds = a.get_actor_bounds(False)
        # Check if extent in any dimension is large (> 200) and it's near the center
        if bounds[1].x > 200 or bounds[1].y > 200 or bounds[1].z > 200:
            mesh_name = smc.static_mesh.get_name() if smc.static_mesh else "None"
            loc = a.get_actor_location()
            if abs(loc.x) < 2000 and abs(loc.y) < 2000:
                print(f"Large actor: {a.get_actor_label():30} | mesh={mesh_name:25} | loc=({loc.x:6.1f},{loc.y:6.1f},{loc.z:6.1f}) | ext=({bounds[1].x:6.1f},{bounds[1].y:6.1f},{bounds[1].z:6.1f})")
