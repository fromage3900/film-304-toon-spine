import unreal
import json

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

dirty_maps = [p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
dirty_content = [p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]

all_actors = eas.get_all_level_actors()
actor_labels = [a.get_actor_label() for a in all_actors]

# Cast inspection
cast_info = {}
for a in all_actors:
    lbl = a.get_actor_label()
    if any(k in lbl.lower() for k in ["dana", "david", "sam", "spider", "cast"]):
        skc = a.get_component_by_class(unreal.SkeletalMeshComponent)
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        info = {
            "class": a.get_class().get_name(),
            "location": [round(v, 1) for v in [a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z]],
            "rotation": [round(v, 1) for v in [a.get_actor_rotation().pitch, a.get_actor_rotation().yaw, a.get_actor_rotation().roll]],
            "folder": str(a.get_folder_path()),
        }
        if skc:
            anim = skc.get_editor_property("animation_data")
            anim_to_play = anim.get_editor_property("anim_to_play") if anim else None
            info["skel_mesh"] = skc.skeletal_mesh.get_name() if skc.skeletal_mesh else "None"
            info["anim_mode"] = str(skc.get_editor_property("animation_mode"))
            info["anim_asset"] = anim_to_play.get_name() if anim_to_play else "None"
            info["mats"] = [skc.get_material(i).get_name() if skc.get_material(i) else "None" for i in range(skc.get_num_materials())]
        elif smc:
            info["static_mesh"] = smc.static_mesh.get_name() if smc.static_mesh else "None"
        cast_info[lbl] = info

# Lights inspection
lights_info = {}
for a in all_actors:
    for c in a.get_components_by_class(unreal.LightComponent):
        prio = c.get_editor_property("forward_shading_priority") if c.get_class().get_name() == "DirectionalLightComponent" else "N/A"
        vol_scat = c.get_editor_property("volumetric_scattering_intensity") if hasattr(c, "get_editor_property") and hasattr(c, "volumetric_scattering_intensity") else "N/A"
        col = c.get_editor_property("light_color") if hasattr(c, "get_editor_property") else None
        lights_info[f"{a.get_actor_label()} / {c.get_name()}"] = {
            "type": c.get_class().get_name(),
            "intensity": round(c.intensity, 1),
            "color": [round(col.r, 2), round(col.g, 2), round(col.b, 2)] if col else None,
            "forward_shading_priority": prio,
            "volumetric_scattering": round(vol_scat, 2) if isinstance(vol_scat, (int, float)) else vol_scat,
            "visible": c.is_visible(),
            "casts_shadows": c.cast_shadows,
        }

# Cameras inspection
cams_info = {}
for a in all_actors:
    cam = a.get_component_by_class(unreal.CineCameraComponent)
    if cam:
        focus = cam.focus_settings
        cams_info[a.get_actor_label()] = {
            "location": [round(v, 1) for v in [a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z]],
            "rotation": [round(v, 1) for v in [a.get_actor_rotation().pitch, a.get_actor_rotation().yaw, a.get_actor_rotation().roll]],
            "focal_length": round(cam.current_focal_length, 1),
            "aperture": round(cam.current_aperture, 2),
            "focus_method": str(focus.focus_method),
            "manual_focus_distance": round(focus.manual_focus_distance, 1),
        }

result = {
    "world": world.get_path_name() if world else "None",
    "dirty_maps": dirty_maps,
    "dirty_content_count": len(dirty_content),
    "dirty_content": dirty_content[:15],
    "total_actors": len(all_actors),
    "cast": cast_info,
    "cameras_count": len(cams_info),
    "cameras": cams_info,
    "lights": lights_info,
}

print("=== LIVE SCENE PROBE RESULT ===")
print(json.dumps(result, indent=2))
