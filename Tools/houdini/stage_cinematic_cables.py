"""Stages procedural catenary industrial powerlines and utility cables bridging the Brutalist towers in L_Film_Office."""
import math
import unreal

def generate_catenary_points(p_start, p_end, sag_depth=120.0, num_segments=24):
    """Computes realistic catenary cable curve points with gravitational sag."""
    points = []
    dx = p_end.x - p_start.x
    dy = p_end.y - p_start.y
    dz = p_end.z - p_start.z
    
    for i in range(num_segments + 1):
        t = i / float(num_segments)
        # Parabolic approximation to catenary sag
        sag = 4.0 * sag_depth * t * (1.0 - t)
        px = p_start.x + (dx * t)
        py = p_start.y + (dy * t)
        pz = p_start.z + (dz * t) - sag
        points.append(unreal.Vector(px, py, pz))
    return points

def stage_cables():
    print("Staging procedural catenary utility cables...")
    
    # 1. Clean previous cables if any
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_folder_path() == "Baked_Skyline_Cables":
            unreal.EditorLevelLibrary.destroy_actor(a)
            
    cylinder_mesh = unreal.load_asset("/Engine/BasicShapes/Cylinder")
    mat_cable = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistAsphalt")
    
    # Cable corridor runs across the exterior alley visible through the office windows
    runs = [
        # Run 1: High-voltage triple bundle from Office exterior facade to Midground Punched Estate
        {
            "name": "Cables_Corridor_Office_to_Estate",
            "start": unreal.Vector(-280.0, 180.0, 180.0),
            "end": unreal.Vector(-3100.0, 1500.0, 1200.0),
            "sag": 220.0,
            "bundle_offsets": [
                unreal.Vector(0.0, 0.0, 0.0),
                unreal.Vector(0.0, 12.0, -8.0),
                unreal.Vector(0.0, -12.0, -8.0)
            ],
            "thickness": 0.04 # 4cm cable radius
        },
        # Run 2: Midground utility lines slung between Punched Estate and Tower Ribbon 01
        {
            "name": "Cables_Corridor_Estate_to_Ribbon",
            "start": unreal.Vector(-3100.0, 1700.0, 1400.0),
            "end": unreal.Vector(-4600.0, 2900.0, 2200.0),
            "sag": 320.0,
            "bundle_offsets": [
                unreal.Vector(0.0, 0.0, 0.0),
                unreal.Vector(0.0, 18.0, -12.0)
            ],
            "thickness": 0.05
        },
        # Run 3: Lower secondary telephone corridor crossing the street canyon
        {
            "name": "Cables_Corridor_StreetCrossing",
            "start": unreal.Vector(-2200.0, 900.0, 400.0),
            "end": unreal.Vector(-4200.0, 2200.0, 600.0),
            "sag": 280.0,
            "bundle_offsets": [
                unreal.Vector(0.0, 0.0, 0.0)
            ],
            "thickness": 0.04
        }
    ]
    
    created_actors = []
    
    for run in runs:
        holder = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor,
            run["start"],
            unreal.Rotator(0.0, 0.0, 0.0)
        )
        holder.set_actor_label(run["name"])
        holder.set_folder_path("Baked_Skyline_Cables")
        
        # We use an HISM component on the holder actor
        hism = unreal.new_object(unreal.HierarchicalInstancedStaticMeshComponent, holder, name=f"{run['name']}_HISM")
        hism.attach_to_component(holder.root_component, unreal.Name(), unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE, False)
        hism.set_static_mesh(cylinder_mesh)
        if mat_cable:
            hism.set_material(0, mat_cable)
        hism.set_editor_property("cast_shadow", True)
        
        for b_off in run["bundle_offsets"]:
            p0 = run["start"] + b_off
            p1 = run["end"] + b_off
            pts = generate_catenary_points(p0, p1, sag_depth=run["sag"], num_segments=20)
            
            # Segment cylinders between each pair of points
            for i in range(len(pts) - 1):
                seg_start = pts[i]
                seg_end = pts[i+1]
                mid_pt = (seg_start + seg_end) * 0.5
                diff = seg_end - seg_start
                length = math.sqrt(diff.x*diff.x + diff.y*diff.y + diff.z*diff.z)
                if length < 1e-4: continue
                
                # Cylinder in UE BasicShapes is along Z axis, length 100, radius 50
                # Scale Z by length / 100, X and Y by thickness
                scale = unreal.Vector(run["thickness"], run["thickness"], length / 100.0)
                
                # Compute rotation pointing from seg_start to seg_end
                # Yaw = atan2(dy, dx), Pitch = atan2(dz, sqrt(dx^2 + dy^2))
                h_dist = math.sqrt(diff.x*diff.x + diff.y*diff.y)
                yaw_deg = math.degrees(math.atan2(diff.y, diff.x))
                # UE Cylinder is Z-up, so to point along +Z we pitch by (90 - angle_above_horizon) or -pitch
                pitch_deg = math.degrees(math.atan2(diff.z, h_dist)) - 90.0
                rot = unreal.Rotator(pitch=pitch_deg, yaw=yaw_deg, roll=0.0)
                
                # Relative transform to holder
                rel_loc = mid_pt - run["start"]
                t = unreal.Transform(location=rel_loc, rotation=rot, scale=scale)
                hism.add_instance(t)
                
        created_actors.append(holder)
        print(f"Spawned {run['name']} with catenary cable instances!")

    print(f"Step 4 COMPLETE: {len(created_actors)} catenary cable corridors active in Baked_Skyline_Cables.")

if __name__ == "__main__":
    stage_cables()
