import unreal

mat = unreal.load_asset("/Game/Materials/Masters/M_Master_Toon_Glass")
if mat:
    tlm = mat.get_editor_property("translucency_lighting_mode")
    print(f"M_Master_Toon_Glass translucency_lighting_mode: {tlm}")
    # Also check other properties
    for prop in ["screen_space_reflections", "apply_fogging", "translucency_pass"]:
        try:
            val = mat.get_editor_property(prop)
            print(f"  {prop}: {val}")
        except:
            pass
else:
    print("M_Master_Toon_Glass not found!")
