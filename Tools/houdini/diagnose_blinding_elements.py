import unreal

print("=== DIAGNOSING TROFFERS, LIGHTS, AND EMISSIVES ===")
actors = unreal.EditorLevelLibrary.get_all_level_actors()

print("\n--- 1. LIGHT ACTORS & INTENSITIES ---")
for a in actors:
    lbl = a.get_actor_label()
    # Check all lights
    lights = a.get_components_by_class(unreal.LightComponent)
    if lights:
        for lc in lights:
            intensity = lc.get_editor_property("intensity")
            cast_shadows = lc.get_editor_property("cast_shadows")
            print(f"Actor: {lbl} | Class: {lc.get_class().get_name()} | Intensity: {intensity} | CastShadows: {cast_shadows} | Pos: {a.get_actor_location()}")

print("\n--- 2. TROFFER STATIC MESHES & MATERIALS ---")
for a in actors:
    lbl = a.get_actor_label()
    if "troffer" in lbl.lower() or "ceiling" in lbl.lower() or "light" in lbl.lower():
        smcs = a.get_components_by_class(unreal.StaticMeshComponent)
        for smc in smcs:
            mats = [smc.get_material(i).get_name() if smc.get_material(i) else "None" for i in range(smc.get_num_materials())]
            print(f"Actor: {lbl} | Mesh: {smc.static_mesh.get_name() if smc.static_mesh else 'None'} | Mats: {mats} | Pos: {a.get_actor_location()}")

print("\n--- 3. WINDOW BAYS & SKYLINE MESHES (Looking for pure white/blown out actors) ---")
for a in actors:
    lbl = a.get_actor_label()
    if any(k in lbl.lower() for k in ["glass", "window", "sky", "backdrop", "sun", "white"]):
        loc = a.get_actor_location()
        print(f"Actor: {lbl} | Class: {a.get_class().get_name()} | Pos: {loc}")

print("\n--- 4. INSPECTING MI_Toon_Office_Troffer PARAMETERS ---")
mat_path = "/Game/Materials/MI_Toon_Office_Troffer"
mat = unreal.EditorAssetLibrary.load_asset(mat_path)
if mat:
    print(f"Found {mat.get_name()}, parent: {mat.parent.get_name() if hasattr(mat, 'parent') and mat.parent else 'None'}")
    # Inspect scalar and vector parameters
    for sp in mat.scalar_parameter_values:
        print(f"  ScalarParam: {sp.parameter_info.name} = {sp.parameter_value}")
    for vp in mat.vector_parameter_values:
        v = vp.parameter_value
        print(f"  VectorParam: {vp.parameter_info.name} = ({v.r}, {v.g}, {v.b}, {v.a})")
else:
    print(f"Material {mat_path} not found!")

