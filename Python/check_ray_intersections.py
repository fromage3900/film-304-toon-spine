import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
cam_loc = unreal.Vector(240.0, -220.0, 115.0)

bays = [
    ("Bay 1", unreal.Vector(-371.2, 145.2, 150.0)),
    ("Bay 2", unreal.Vector(-274.0, 353.7, 150.0)),
    ("Bay 3", unreal.Vector(-176.8, 562.1, 150.0)),
]

for name, bay_loc in bays:
    ray_dir = (bay_loc - cam_loc).normal()
    print(f"\nActors intersecting ray {name} (Dir={ray_dir}):")
    # For each actor in level, check if line segment from bay_loc to bay_loc + ray_dir * 10000 intersects actor bounds
    p0 = bay_loc
    p1 = bay_loc + ray_dir * 30000.0
    for a in eas.get_all_level_actors():
        origin, extent = a.get_actor_bounds(False)
        if extent.length() < 10.0:
            continue
        # Check AABB intersection with segment p0-p1
        # Simple test: project center onto ray
        v = origin - cam_loc
        proj = v.dot(ray_dir)
        if proj > 500.0:
            perp_dist = (v - ray_dir * proj).length()
            if perp_dist < extent.length():
                print(f"  {a.get_actor_label()} ({a.get_class().get_name()}): Origin={origin} Extent={extent} PerpDist={perp_dist:.1f} ProjDist={proj:.1f}")

