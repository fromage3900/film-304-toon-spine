import unreal

# Line of sight from SESSION_CAM_Cast (898.7, -685.6, 184.6)
# Dana is at (11.3, 28.9, 0.0) -> vector Cam -> Dana: (-887.4, +714.5, -184.6)
# Looking past Dana: X goes to -300..-600, Y goes to +200..+600
# Coffee machine area: where is it?

print("=== COFFEE MACHINE AND COUNTER ACTORS ===")
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    lbl = a.get_actor_label()
    if any(k in lbl.lower() for k in ["coffee", "espresso", "counter", "kitchen", "breakroom", "cabinet"]):
        print(f"Actor: {lbl} at {a.get_actor_location()}")

print("\n=== ACTORS BEHIND DANA (X: -600..0, Y: -200..600, Z: 0..400) ===")
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    l = a.get_actor_location()
    if -800 <= l.x <= 0 and -300 <= l.y <= 700:
        # Check mesh and material
        smcs = a.get_components_by_class(unreal.StaticMeshComponent)
        for smc in smcs:
            mats = [smc.get_material(i).get_name() if smc.get_material(i) else "None" for i in range(smc.get_num_materials())]
            if any("glass" in m.lower() or "white" in m.lower() or "sky" in m.lower() or "troffer" in m.lower() for m in mats):
                print(f"Candidate Blown Actor: {a.get_actor_label()} ({smc.static_mesh.get_name() if smc.static_mesh else 'None'}) mats={mats} pos={l}")

print("\n=== DIRECTIONAL LIGHTS AND SKY SPHERE ===")
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if "sun" in a.get_actor_label().lower() or "sky" in a.get_actor_label().lower() or "light" in a.get_actor_label().lower():
        lcs = a.get_components_by_class(unreal.DirectionalLightComponent)
        if lcs:
            for lc in lcs:
                print(f"DirectionalLight: {a.get_actor_label()} intensity={lc.get_editor_property('intensity')} rot={a.get_actor_rotation()} color={lc.get_editor_property('light_color')}")
        sky = a.get_components_by_class(unreal.SkyLightComponent)
        if sky:
            for sk in sky:
                print(f"SkyLight: {a.get_actor_label()} intensity={sk.get_editor_property('intensity')}")
