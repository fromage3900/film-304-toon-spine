import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== CHECKING TROFFER MATERIAL & LIGHTS ===")
mat_troffer = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Office_Troffer")
if mat_troffer:
    print("MI_Toon_Office_Troffer parent:", mat_troffer.get_editor_property("parent").get_name())
    for sp in mat_troffer.get_editor_property("scalar_parameter_values"):
        pname = sp.get_editor_property("parameter_info").name
        val = sp.get_editor_property("parameter_value")
        print(f"  Scalar {pname}: {val}")
    for vp in mat_troffer.get_editor_property("vector_parameter_values"):
        pname = vp.get_editor_property("parameter_info").name
        val = vp.get_editor_property("parameter_value")
        print(f"  Vector {pname}: {val}")

for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if "Troffer" in lbl:
        rl = a.get_component_by_class(unreal.RectLightComponent)
        if rl:
            print(f"  RectLight {lbl}: intensity={rl.intensity}, color={rl.light_color}")
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc:
            mats = [smc.get_material(i).get_name() if smc.get_material(i) else "None" for i in range(smc.get_num_materials())]
            print(f"  Mesh {lbl}: mats={mats}")
