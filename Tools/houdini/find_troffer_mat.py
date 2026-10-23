import unreal

print("=== FINDING MI_Toon_Office_Troffer ===")
reg = unreal.AssetRegistryHelpers.get_asset_registry()
assets = reg.get_assets_by_class("MaterialInstanceConstant")
for a in assets:
    if "troffer" in a.asset_name.lower():
        print(f"Found troffer material: {a.package_name}/{a.asset_name}")

print("\n=== INSPECTING ALL LIGHTS ===")
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    lights = a.get_components_by_class(unreal.LightComponent)
    if lights:
        for lc in lights:
            print(f"Light: {a.get_actor_label()} ({lc.get_class().get_name()}) | Intensity: {lc.get_editor_property('intensity')} | Attenuation: {lc.get_editor_property('attenuation_radius') if hasattr(lc, 'attenuation_radius') else 'N/A'}")
