import unreal

cam = None
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "SESSION_CAM_Cast":
        cam = a
        break

if cam:
    loc = cam.get_actor_location()
    rot = cam.get_actor_rotation()
    print(f"SESSION_CAM_Cast Location: {loc}")
    print(f"SESSION_CAM_Cast Rotation: {rot}")
    cc = cam.get_component_by_class(unreal.CineCameraComponent)
    if cc:
        print(f"Focal length: {cc.current_focal_length}, FOV: {cc.field_of_view}")
        print(f"Focus settings: {cc.focus_settings.focus_method}")
        print(f"Current aperture: {cc.current_aperture}")
        pp = cc.post_process_settings
        print(f"Auto exposure min/max: min_ev100={pp.auto_exposure_min_brightness}, max_ev100={pp.auto_exposure_max_brightness}")

print("\n--- ACTORS NEAR UPPER LEFT / CEILING IN SHOT 1 ---")
# Check what meshes are in the room around x = 0..300, y = 0..400, z = 200..400
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    l = a.get_actor_location()
    lbl = a.get_actor_label()
    # Check for anything with high emissive or lights
    lights = a.get_components_by_class(unreal.LightComponent)
    if lights:
        for lc in lights:
            print(f"LIGHT: {lbl} at {l} | class: {lc.get_class().get_name()} | intensity: {lc.get_editor_property('intensity')}")
    # Also check any static meshes with materials
    smcs = a.get_components_by_class(unreal.StaticMeshComponent)
    for smc in smcs:
        for i in range(smc.get_num_materials()):
            m = smc.get_material(i)
            if m and any(k in m.get_name().lower() for k in ["white", "emissive", "troffer", "glazing", "light"]):
                print(f"MESH WITH EMISSIVE/LIGHT MAT: {lbl} (Mesh: {smc.static_mesh.get_name() if smc.static_mesh else 'None'}) mat[{i}]={m.get_name()} at {l}")
