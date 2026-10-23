import unreal
import claireon
from pathlib import Path

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
OUT.mkdir(parents=True, exist_ok=True)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== STARTING MASTER SHOWCASE CONVERGENCE ===")

# Deselect all
eas.set_selected_level_actors([])

# =========================================================================
# 1. VOLUMETRIC WINDOW SHAFTS / GOD RAYS & DUST
# =========================================================================
# Compute look-at rotation for forward vector (0.817, -0.381, -0.433)
# pitch = asin(-0.433) = -25.66 deg, yaw = atan2(-0.381, 0.817) = -25.0 deg
rot_shaft = unreal.Rotator(pitch=-25.66, yaw=-25.0, roll=0.0)

shaft_coords = [
    ("Film_WindowShaft_01", unreal.Vector(-351.3, 135.9, 255.0)),
    ("Film_WindowShaft_02", unreal.Vector(-254.1, 344.4, 255.0)),
    ("Film_WindowShaft_03", unreal.Vector(-156.9, 552.8, 255.0)),
]

for label, pos in shaft_coords:
    shaft_actor = None
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == label:
            shaft_actor = a
            break
    
    if not shaft_actor:
        shaft_actor = eas.spawn_actor_from_class(unreal.SpotLight, pos, rot_shaft)
        shaft_actor.set_actor_label(label)
        shaft_actor.set_folder_path("Film304/FinalAssembly/WindowRays")
        print(f"Spawned {label} at {pos}")
    else:
        shaft_actor.set_actor_location(pos, False, False)
        shaft_actor.set_actor_rotation(rot_shaft, False)
        print(f"Updated {label}")
    
    c = shaft_actor.get_component_by_class(unreal.SpotLightComponent)
    if c:
        c.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
        c.set_editor_property("intensity", 140.0)
        c.set_editor_property("use_temperature", True)
        c.set_editor_property("temperature", 4300.0)
        c.set_editor_property("attenuation_radius", 1500.0)
        c.set_editor_property("inner_cone_angle", 11.0)
        c.set_editor_property("outer_cone_angle", 18.0)
        c.set_editor_property("volumetric_scattering_intensity", 6.0)
        c.set_editor_property("cast_volumetric_shadow", True)
        c.set_editor_property("cast_shadows", True)

# Exponential Height Fog Volumetric configuration
# Routed through film304_fog so the extinction scale comes from the render-reviewed
# baseline. This previously hard-coded 1.2, which silently reverted the reviewed 4.0
# recorded in Docs/GOAL_ESTABLISHING_SHOTS_20261017.md (v07 entry) on every re-run.
film304_fog.assert_single_owner(eas)
_fog_receipt = film304_fog.apply({"fog_density": 0.003}, film304_fog.INTENT_SHOT_LOOK, actors=eas)
_fog_baseline = film304_fog.apply_reviewed_baseline(actors=eas)
print("Configured fog on", film304_fog.FOG_ACTOR_LABEL, json.dumps({"shot": _fog_receipt["changed"],
                                                                  "baseline": _fog_baseline["changed"]}))

# Activate Film_WindowDust_Subtle
dust_sys = unreal.load_asset("/Game/VFX/Film304Closeout_20261018/NS_Film_WindowDust_v01")
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_WindowDust_Subtle":
        nc = a.get_component_by_class(unreal.NiagaraComponent)
        if nc and dust_sys:
            nc.set_asset(dust_sys)
            nc.activate(True)
            print("Activated subtle window dust motes")
        break

# Also turn on Light_Cinematic_SunBeam subtly
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Light_Cinematic_SunBeam":
        c = a.get_component_by_class(unreal.DirectionalLightComponent)
        if c:
            c.set_editor_property("intensity", 1.2)
            c.set_editor_property("volumetric_scattering_intensity", 2.5)
            print("Activated Light_Cinematic_SunBeam (1.2 cd)")
        break

# =========================================================================
# 2. CONVERGE POST PROCESS VOLUMES INTO ONE MASTER VOLUME & TUNE TOON OUTLINE
# =========================================================================
# Disable all competing PPVs
competing_ppvs = [
    "PPV_ToonOutlineHalftoneStack", "PPV_ToonOutlineOnly", "PPV_ToonOutlineClean",
    "PPV_ToonOutlineRiso", "PPV_P2_WatercolourPaper", "PPV_P3_RisoPrint",
    "PPV_P4_CleanCinematic", "EST_PPV_Ink"
]

for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl in competing_ppvs:
        a.set_editor_property("enabled", False)
        print(f"Disabled competing PPV: {lbl}")

# Calibrate master PPV: PPV_StorybookOutline
master_ppv = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() in ["PPV_StorybookOutline", "PPV_Film304_Master"]:
        master_ppv = a
        break

if master_ppv:
    master_ppv.set_actor_label("PPV_Film304_Master")
    master_ppv.set_editor_property("enabled", True)
    master_ppv.set_editor_property("unbound", True)
    master_ppv.set_editor_property("priority", 100.0)
    s = master_ppv.settings
    s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_HISTOGRAM)
    s.set_editor_property("auto_exposure_bias", -0.85)
    s.set_editor_property("auto_exposure_min_brightness", 0.005)
    s.set_editor_property("auto_exposure_max_brightness", 8.0)
    s.set_editor_property("auto_exposure_apply_physical_camera_exposure", False)
    # Lens aesthetics
    s.set_editor_property("bloom_intensity", 0.20)
    s.set_editor_property("vignette_intensity", 0.25)
    s.set_editor_property("film_grain_intensity", 0.05)
    s.set_editor_property("scene_fringe_intensity", 0.05)
    print("Calibrated PPV_Film304_Master")

# Tune Toon Outline Material (MI_StorybookOutline_Render2026) for punchy graphic read
outline_mat = unreal.load_asset("/Game/Melodia/_PROJECT/04_Materials/PostProcess/Render2026/MI_StorybookOutline_Render2026")
if outline_mat:
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(outline_mat, "OutlineWidth", 0.22)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(outline_mat, "EdgeStrength", 65.0)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(outline_mat, "DepthWeight", 2.2)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(outline_mat, "NormalWeight", 0.08)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(outline_mat, "MaxWidthPx", 1.5)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(outline_mat, "StencilCharacterWeight", 22.0)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(outline_mat, "SceneExposureEV", -0.85)
    print("Tuned MI_StorybookOutline_Render2026 parameters for crisp graphic read")

# =========================================================================
# 3. RE-INTRODUCE SAM WITH ARMS CROSSED POSE & BALANCED LIGHTING
# =========================================================================
sam_actor = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cast_Sam":
        sam_actor = a
        break

anim_crossed = unreal.load_asset("/Game/Staging/Film304Repaired_20261017/Poses_Headless/AS_Sam_ArmsCrossed_Polish01")

if sam_actor and anim_crossed:
    skm = sam_actor.skeletal_mesh_component
    skm.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    skm.override_animation_data(anim_crossed, is_looping=True, is_playing=True)
    sam_actor.set_actor_hidden_in_game(False)
    skm.set_editor_property("hidden_in_game", False)
    
    # Position Sam in midground right near Dana's desk in conversation stance
    # Dana is at (15.9, 35.2, 2.3). Sam at (95.0, -45.0, 2.0), rotated toward Dana
    sam_actor.set_actor_location(unreal.Vector(95.0, -45.0, 2.0), False, False)
    sam_actor.set_actor_rotation(unreal.Rotator(0.0, 140.0, 0.0), False)
    print("Positioned and staged Sam with AS_Sam_ArmsCrossed_Polish01 at (95.0, -45.0, 2.0)")

# Add warm practical key light on Sam so his face, hair, and crossed arms read
sam_key = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Light_Sam_HeroKey":
        sam_key = a
        break

if not sam_key:
    sam_key = eas.spawn_actor_from_class(unreal.PointLight, unreal.Vector(135.0, -85.0, 120.0), unreal.Rotator(0.0, 0.0, 0.0))
    sam_key.set_actor_label("Light_Sam_HeroKey")
    c = sam_key.get_component_by_class(unreal.PointLightComponent)
    if c:
        c.set_editor_property("intensity", 3.2)
        c.set_editor_property("attenuation_radius", 180.0)
        c.set_editor_property("light_color", unreal.Color(255, 225, 185, 255))
        c.set_editor_property("cast_shadows", False)
    print("Spawned Light_Sam_HeroKey")
else:
    sam_key.set_actor_location(unreal.Vector(135.0, -85.0, 120.0), False, False)
    c = sam_key.get_component_by_class(unreal.PointLightComponent)
    if c:
        c.set_editor_property("intensity", 3.2)
        c.set_editor_property("attenuation_radius", 180.0)
    print("Updated Light_Sam_HeroKey")

# =========================================================================
# 4. MATERIAL CONVERGENCE (APPLY MI_Dusk_* SUITE FROM V06)
# =========================================================================
dusk_materials = {
    "Wall": unreal.load_asset("/Game/Materials/Instances/Film304/Dusk/MI_Dusk_Wall"),
    "WarmWall": unreal.load_asset("/Game/Materials/Instances/Film304/Dusk/MI_Dusk_WarmWall"),
    "Floor": unreal.load_asset("/Game/Materials/Instances/Film304/Dusk/MI_Dusk_Floor"),
    "Desk": unreal.load_asset("/Game/Materials/Instances/Film304/Dusk/MI_Dusk_Desk"),
    "Ceiling": unreal.load_asset("/Game/Materials/Instances/Film304/Dusk/MI_Dusk_Ceiling"),
    "Glazing": unreal.load_asset("/Game/Materials/Instances/Film304/Dusk/MI_Dusk_Glazing"),
    "Metal": unreal.load_asset("/Game/Materials/Instances/Film304/Dusk/MI_Dusk_Metal"),
    "Plastic": unreal.load_asset("/Game/Materials/Instances/Film304/Dusk/MI_Dusk_Plastic"),
    "Blinds": unreal.load_asset("/Game/Materials/Instances/Film304/Dusk/MI_Dusk_Blinds"),
    "Chair": unreal.load_asset("/Game/Materials/Instances/Film304/Dusk/MI_Dusk_Chair"),
}

rebound_count = 0
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    smc = a.get_component_by_class(unreal.StaticMeshComponent)
    if not smc:
        continue
    
    # Floor
    if "Floor" in lbl and dusk_materials["Floor"]:
        smc.set_material(0, dusk_materials["Floor"])
        rebound_count += 1
    # Ceilings
    elif "Ceiling" in lbl and dusk_materials["Ceiling"]:
        smc.set_material(0, dusk_materials["Ceiling"])
        rebound_count += 1
    # Warm/Feature Wall
    elif "Feature" in lbl or "Warm" in lbl or "NorthReturn" in lbl:
        if dusk_materials["WarmWall"]:
            smc.set_material(0, dusk_materials["WarmWall"])
            rebound_count += 1
    # Normal Walls
    elif "Wall" in lbl and dusk_materials["Wall"]:
        smc.set_material(0, dusk_materials["Wall"])
        rebound_count += 1
    # Desks
    elif "Desk" in lbl and dusk_materials["Desk"]:
        for i in range(smc.get_num_materials()):
            smc.set_material(i, dusk_materials["Desk"])
            rebound_count += 1
    # Blinds
    elif "Blind" in lbl and dusk_materials["Blinds"]:
        for i in range(smc.get_num_materials()):
            smc.set_material(i, dusk_materials["Blinds"])
            rebound_count += 1
    # Window Glazing
    elif "Glass" in lbl and dusk_materials["Glazing"]:
        smc.set_material(0, dusk_materials["Glazing"])
        rebound_count += 1
    # Mullions / metal frames
    elif "Mullion" in lbl and dusk_materials["Metal"]:
        smc.set_material(0, dusk_materials["Metal"])
        rebound_count += 1

print(f"Re-bound {rebound_count} material slots with MI_Dusk_* instances")

# =========================================================================
# 5. RE-CALIBRATE CAMERAS & RENDER 3-SHOT SUITE
# =========================================================================
# Shot 1 (Master Ensemble): Frame Dana midground center, Sam foreground right, David midground left/right
cam_shot1 = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cam_Showcase_Ensemble_v02":
        cam_shot1 = a
        break

if cam_shot1:
    cam_shot1.set_actor_location(unreal.Vector(255.0, -215.0, 110.0), False, False)
    cam_shot1.set_actor_rotation(unreal.Rotator(pitch=-1.0, yaw=132.0, roll=0.0), False)
    c = cam_shot1.get_cine_camera_component()
    if c:
        c.set_editor_property("current_focal_length", 32.0)
        c.set_editor_property("current_aperture", 2.8)
        c.focus_settings.manual_focus_distance = 295.0

# Deselect all actors
eas.set_selected_level_actors([])

# Save level state cleanly
unreal.EditorLoadingAndSavingUtils.save_current_level()

# Render Proofs
shots = [
    ("Film_Cam_Showcase_Ensemble_v02", "Shot_01_Converged_MasterEnsemble.png"),
    ("Film_Cam_Showcase_DanaPortrait_v02", "Shot_02_Converged_DanaPortrait.png"),
    ("Film_Cam_Showcase_LowAngleRake_v02", "Shot_03_Converged_DavidRake.png"),
]

for cam_name, fname in shots:
    cam_actor = None
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == cam_name:
            cam_actor = a
            break
    if cam_actor:
        loc = cam_actor.get_actor_location()
        rot = cam_actor.get_actor_rotation()
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(loc, rot)
        res = claireon.slate_screenshot(target="level_viewport", filename=fname, directory=str(OUT))
        print(f"Delivered {cam_name} -> {fname}: {res.get('summary') if isinstance(res, dict) else res}")

print("=== MASTER SHOWCASE CONVERGENCE COMPLETED CLEANLY ===")
