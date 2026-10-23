import unreal

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
cam_loc = unreal.Vector(240.0, -220.0, 115.0)

for name, bay_loc in [
    ("Bay 1", unreal.Vector(-371.2, 145.2, 150.0)),
    ("Bay 2", unreal.Vector(-274.0, 353.7, 150.0)),
    ("Bay 3", unreal.Vector(-176.8, 562.1, 150.0)),
]:
    ray_dir = (bay_loc - cam_loc).normal()
    # Find all actors intersecting this ray
    print(f"\n--- Tracing {name} (Dir: {ray_dir}) ---")
    # Step along the ray from dist 500 to 20000 in steps of 200
    for d in range(600, 25000, 400):
        pos = cam_loc + ray_dir * float(d)
        # check if pos is inside any actor bounds
        pass
    
    # Or use multi line trace
    hits = unreal.SystemLibrary.line_trace_multi(
        world, cam_loc, cam_loc + ray_dir * 50000.0,
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
        False, [], unreal.DrawDebugTrace.NONE, True
    )
    print(f"Total hits along {name}: {len(hits)}")
    for h in hits:
        hit_dict = h.to_dict()
        actor = hit_dict.get("actor")
        comp = hit_dict.get("component")
        dist = hit_dict.get("distance")
        print(f"  Hit at dist={dist:.1f}: {actor.get_actor_label() if actor else 'None'} ({comp.get_name() if comp else 'None'})")

