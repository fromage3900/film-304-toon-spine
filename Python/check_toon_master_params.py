import unreal

mat = unreal.load_asset("/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v06")
if mat:
    print("M_UniversalToon_Film304_v06 loaded!")
    # Check parameters
    for p in mat.get_editor_property("parameter_overview"):
        print(f"  Param: {p.parameter_info.name} ({p.type})")
else:
    print("Failed to load M_UniversalToon_Film304_v06")
