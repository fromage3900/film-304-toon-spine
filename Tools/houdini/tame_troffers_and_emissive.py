"""Tames blinding troffer glare, balances sun intensities, adds Fresnel to emissive materials,
and sets film-grade comfortable exposure.
"""
import unreal

ME = unreal.MaterialEditingLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== 1. TAMING TROFFER INTENSITY & RECTLIGHTS ===")
for a in EAS.get_all_level_actors():
    lbl = a.get_actor_label()
    if "Troffer" in lbl:
        rl = a.get_component_by_class(unreal.RectLightComponent)
        if rl:
            rl.set_intensity(1.5)
            print(f"  Reduced {lbl} RectLight intensity to 1.5")
    elif lbl == "Light_Workstation_Row_Troffer":
        rl = a.get_component_by_class(unreal.RectLightComponent)
        if rl:
            rl.set_intensity(1.8)
            print(f"  Reduced {lbl} RectLight intensity to 1.8")

# Troffer diffuser material: gentle milk acrylic, no glare
mat_troffer = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Office_Troffer")
if mat_troffer:
    ME.set_material_instance_scalar_parameter_value(mat_troffer, "EmissiveIntensity", 0.02)
    ME.set_material_instance_scalar_parameter_value(mat_troffer, "GlowIntensity", 0.02)
    ME.set_material_instance_scalar_parameter_value(mat_troffer, "BloomBoost", 0.05)
    ME.set_material_instance_scalar_parameter_value(mat_troffer, "InnerGlowIntensity", 0.02)
    ME.set_material_instance_scalar_parameter_value(mat_troffer, "RimPower", 3.0)
    ME.set_material_instance_scalar_parameter_value(mat_troffer, "RimIntensity", 0.5)
    ME.set_material_instance_vector_parameter_value(mat_troffer, "BaseTint", unreal.LinearColor(0.35, 0.38, 0.40, 1.0))
    ME.set_material_instance_vector_parameter_value(mat_troffer, "AccentTint", unreal.LinearColor(0.50, 0.52, 0.55, 1.0))
    ME.set_material_instance_vector_parameter_value(mat_troffer, "EmissiveColor", unreal.LinearColor(0.40, 0.45, 0.50, 1.0))
    ME.update_material_instance(mat_troffer)
    print("  Tamed MI_Toon_Office_Troffer: soft diffused glow, zero eye strain")

print("=== 2. BALANCING SUN & DIRECTIONAL LIGHTS ===")
for a in EAS.get_all_level_actors():
    lbl = a.get_actor_label()
    dl = a.get_component_by_class(unreal.DirectionalLightComponent)
    if dl:
        if lbl == "Light_Cinematic_SunBeam":
            dl.set_intensity(2.2)
            print("  Balanced Light_Cinematic_SunBeam to 2.2")
        elif lbl == "Cast_RimKicker_Light":
            dl.set_intensity(0.8)
            print("  Balanced Cast_RimKicker_Light to 0.8")
        elif lbl == "EST_Fill_E1":
            dl.set_intensity(0.3)
            print("  Balanced EST_Fill_E1 to 0.3")
        elif "UDS" in lbl:
            dl.set_intensity(1.2)
            print("  Balanced UDS DirectionalLight to 1.2")

print("=== 3. ADDING FRESNEL ATTENUATION TO EMISSIVE LIVING WINDOWS ===")
for path in [
    "/Game/Materials/Instances/Film304/Environment/MI_Film304_Glazing_WarmOffice",
    "/Game/Materials/Instances/Film304/Environment/MI_Film304_Glazing_CoolOffice"
]:
    mi = unreal.load_asset(path)
    if mi:
        ME.set_material_instance_scalar_parameter_value(mi, "GlowIntensity", 0.8)
        ME.set_material_instance_scalar_parameter_value(mi, "BloomBoost", 0.4)
        ME.set_material_instance_scalar_parameter_value(mi, "RimPower", 2.5)
        ME.set_material_instance_scalar_parameter_value(mi, "RimIntensity", 1.2)
        ME.update_material_instance(mi)
        print(f"  Added Fresnel & tamed bloom on {mi.get_name()}")

print("=== 4. FILM-GRADE POST PROCESS EXPOSURE ===")
for a in EAS.get_all_level_actors():
    if a.get_actor_label() in ["PPV_StorybookOutline", "PPV_P4_CleanCinematic"]:
        s = a.settings
        s.override_auto_exposure_method = True
        s.auto_exposure_method = unreal.AutoExposureMethod.AEM_HISTOGRAM
        s.override_auto_exposure_bias = True
        s.auto_exposure_bias = 0.0 # Clean neutral eye-comfortable exposure
        s.override_auto_exposure_min_brightness = True
        s.auto_exposure_min_brightness = 0.2
        s.override_auto_exposure_max_brightness = True
        s.auto_exposure_max_brightness = 15.0
        # Gentle bloom
        s.override_bloom_intensity = True
        s.bloom_intensity = 0.35
        s.override_bloom_threshold = True
        s.bloom_threshold = 1.0
        a.settings = s
        print(f"  Configured comfortable film exposure on {a.get_actor_label()}")

unreal.EditorLevelLibrary.save_current_level()
print("SUCCESS: Lighting, troffers, and emissive materials completely tamed and balanced!")
