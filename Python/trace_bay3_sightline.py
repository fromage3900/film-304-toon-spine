import unreal
import json

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

cam = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cam_Showcase_Ensemble_v02":
        cam = a
        break

if not cam:
    print("Camera Film_Cam_Showcase_Ensemble_v02 not found")
else:
    cam_loc = cam.get_actor_location()
    cam_rot = cam.get_actor_rotation()
    print(f"Cam loc: {cam_loc}, rot: {cam_rot}")

    # Bay 3 location is around (-176.8, 562.1, 150.0)
    bay3_loc = unreal.Vector(-176.8, 562.1, 150.0)
    ray_dir = (bay3_loc - cam_loc).normal()
    print(f"Ray from cam to Bay 3 center: dir = {ray_dir}")

    # Ray trace out 500,000 units
    end_loc = cam_loc + ray_dir * 500000.0
    hits = unreal.SystemLibrary.line_trace_multi(
        world, cam_loc, end_loc,
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
        False, [], unreal.DrawDebugTrace.NONE, True
    )

    print(f"Total collision hits through Bay 3: {len(hits)}")
    for h in hits:
        hd = h.to_dict()
        act = hd.get("actor")
        comp = hd.get("component")
        dist = hd.get("distance")
        loc = hd.get("location")
        print(f"  Dist {dist:.1f}: Actor '{act.get_actor_label() if act else 'None'}' ({act.get_class().get_name() if act else 'None'}), Comp: {comp.get_name() if comp else 'None'}, Loc: {loc}")

    # Also check what actors are within a cone around this ray
    print("\n--- Actors with bounds intersecting Bay 3 sightline cone ---")
    intersected = []
    for a in eas.get_all_level_actors():
        origin, extent = a.get_actor_bounds(False)
        if extent.length() < 20.0:
            continue
        v = origin - cam_loc
        proj = v.dot(ray_dir)
        if proj > 300.0:
            perp = (v - ray_dir * proj).length()
            if perp < (extent.length() + proj * 0.15):
                smc = a.get_component_by_class(unreal.StaticMeshComponent)
                mats = [smc.get_material(i).get_name() if smc and smc.get_material(i) else "None" for i in range(smc.get_num_materials())] if smc else []
                intersected.append({
                    "label": a.get_actor_label(),
                    "class": a.get_class().get_name(),
                    "origin": [round(origin.x, 1), round(origin.y, 1), round(origin.z, 1)],
                    "extent": [round(extent.x, 1), round(extent.y, 1), round(extent.z, 1)],
                    "proj_dist": round(proj, 1),
                    "perp_dist": round(perp, 1),
                    "materials": mats,
                    "hidden_ed": a.is_hidden_ed(),
                })
    
    intersected.sort(key=lambda x: x["proj_dist"])
    print(json.dumps(intersected, indent=2))
