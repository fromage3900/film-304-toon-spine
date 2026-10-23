import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== INSPECTING UDS AND FOG PROPERTIES ===")

uds_actor = None
fog_actor = None

for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if "uds" in lbl.lower() or "sky" in lbl.lower():
        if "Ultra_Dynamic_Sky" in a.get_class().get_name():
            uds_actor = a
    elif isinstance(a, unreal.ExponentialHeightFog):
        fog_actor = a

if uds_actor:
    print(f"UDS Actor: {uds_actor.get_actor_label()} ({uds_actor.get_class().get_name()})")
    # Check key UDS properties related to horizon fog and atmosphere
    uds_props = [
        "Time of Day", "Sun Angle", "Horizon Fog Addition", "Fog Density Multiplier",
        "Overall Fog Density", "Enable Fog", "Volumetric Fog", "Cloud Coverage",
        "Cloud Opacity", "Night Horizon Blur", "Light Pollution", "Sky Glow",
        "Horizon Blur", "Horizon Height", "Sun Falloff", "Sky Mode"
    ]
    for p in uds_props:
        try:
            val = uds_actor.get_editor_property(p)
            print(f"  {p}: {val}")
        except Exception:
            pass
else:
    print("No UDS Actor found")

if fog_actor:
    fc = fog_actor.component
    print(f"\nFog Actor: {fog_actor.get_actor_label()}")
    fog_props = [
        "fog_density", "fog_inscattering_luminance", "directional_inscattering_exponent",
        "enable_volumetric_fog", "volumetric_fog_scattering_distribution",
        "volumetric_fog_extinction_scale", "volumetric_fog_distance",
        "fog_height_falloff"
    ]
    for p in fog_props:
        try:
            val = fc.get_editor_property(p)
            print(f"  {p}: {val}")
        except Exception:
            pass
