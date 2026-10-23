import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Find what actor is causing this diagonal structure
cam = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SESSION_CAM_Cast":
        cam = a
        break

cam_loc = cam.get_actor_location() # (898.7, -685.6, 184.6)
# Dana is at (11.3, 28.9, 0)
print(f"Cam loc: {cam_loc}")

print("\n=== ACTORS BETWEEN CAM (898, -685, 184) AND DANA (11, 29, 0) ===")
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    smc = a.get_component_by_class(unreal.StaticMeshComponent)
    if smc and smc.static_mesh:
        origin, extent = a.get_actor_bounds(False)
        # Check if bounds overlap the space between cam and characters
        if origin.x > -200 and origin.x < 1000 and origin.y > -800 and origin.y < 400:
            if extent.x > 100 or extent.y > 100 or extent.z > 50:
                print(f"Actor: {lbl:45s} | Mesh: {smc.static_mesh.get_name():35s} | Pos: {a.get_actor_location()} | Rot: {a.get_actor_rotation()} | Origin: ({origin.x:.1f},{origin.y:.1f},{origin.z:.1f}) Extent: ({extent.x:.1f},{extent.y:.1f},{extent.z:.1f})")
