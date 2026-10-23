"""Master Cinematic Lookdev, Houdini Engine Bakes, VFX, and Set Dressing Execution for L_Film_Office.

Executes:
1. Houdini Engine HDA instantiation & cooking:
   - HDA_Cubicle_Hive (scene_mode=1)
   - HDA_Breakroom_Sanctuary (scene_mode=3)
   - Native baking via Houdini Engine to InstancedStaticMesh actors
2. Procedural Houdini (hython) ceiling HVAC & troffer grid placement
3. Atmospheric Volumetric VFX:
   - ExponentialHeightFog volumetric fog on the single owner EST_Fog_E1, forward Mie
     scattering 0.65 and render-reviewed extinction scale (see Python/film304_fog.py)
   - Golden sunbeam volumetric scattering intensity (4.0)
   - Niagara floating dust motes actor in window sunbeams
   - Imperfecter post-process polish (lens dirt 2.0, chromatic fringe 0.18, vignette 0.42, 35mm grain)
4. 4 Composed Cinematic CineCameras:
   - CineCam_Hero_CubicleEstablishing (24mm, high-angle overhead labyrinth)
   - CineCam_Hero_CubicleTrench (35mm, claustrophobic aisle tracking)
   - CineCam_Hero_BreakroomEstablishing (35mm, ZMJ breakroom sanctuary)
   - CineCam_Hero_CorridorWatercooler (50mm, watercooler pause vignette)
5. Clean level saving and verification.
"""
import json
import math
import unreal

import film304_fog

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ELL = unreal.EditorLevelLibrary

def execute_lookdev():
    unreal.log("==================================================================")
    unreal.log("[HoudiniLookdev] Executing Master Houdini Engine & VFX Integration...")
    unreal.log("==================================================================")
    
    # -------------------------------------------------------------------------
    # 1. HOUDINI ENGINE: Instantiate, Cook, and Bake Cubicle Hive & Breakroom
    # -------------------------------------------------------------------------
    api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
    hda = unreal.load_asset("/Game/Houdini/HDA_Brutalist_ShotComposer")
    
    # Clean old HDA actors if any
    for a in ELL.get_all_level_actors():
        lbl = a.get_actor_label()
        if lbl in ["HDA_Cubicle_Hive", "HDA_Breakroom_Sanctuary"]:
            ELL.destroy_actor(a)

    # 1A. Cubicle Hive HDA
    unreal.log("[HoudiniLookdev] Instantiating HDA_Cubicle_Hive via Houdini Engine...")
    trans_cubicle = unreal.Transform(location=[400.0, -250.0, 0.0], rotation=[0.0, 0.0, 0.0], scale=[1.0, 1.0, 1.0])
    wrap_cubicle = api.instantiate_asset(
        houdini_asset=hda,
        instantiate_at=trans_cubicle,
        enable_auto_cook=True,
        enable_auto_bake=False
    )
    if wrap_cubicle:
        actor_c = wrap_cubicle.get_houdini_asset_actor()
        actor_c.set_actor_label("HDA_Cubicle_Hive")
        if hasattr(actor_c, "set_folder_path"):
            actor_c.set_folder_path("Houdini_Engine_Cubicle_Hive")
        wrap_cubicle.set_int_parameter_value("scene_mode", 1) # Interior Cubicle Hive
        wrap_cubicle.recook()
        wrap_cubicle.bake_all_outputs()
        unreal.log("[HoudiniLookdev] HDA_Cubicle_Hive cooked and baked successfully.")

    # 1B. Breakroom Sanctuary HDA
    unreal.log("[HoudiniLookdev] Instantiating HDA_Breakroom_Sanctuary via Houdini Engine...")
    trans_br = unreal.Transform(location=[350.0, 450.0, 0.0], rotation=[0.0, 0.0, 0.0], scale=[1.0, 1.0, 1.0])
    wrap_br = api.instantiate_asset(
        houdini_asset=hda,
        instantiate_at=trans_br,
        enable_auto_cook=True,
        enable_auto_bake=False
    )
    if wrap_br:
        actor_br = wrap_br.get_houdini_asset_actor()
        actor_br.set_actor_label("HDA_Breakroom_Sanctuary")
        if hasattr(actor_br, "set_folder_path"):
            actor_br.set_folder_path("Houdini_Engine_Breakroom")
        wrap_br.set_int_parameter_value("scene_mode", 3) # Interior ZMJ Break Room
        wrap_br.recook()
        wrap_br.bake_all_outputs()
        unreal.log("[HoudiniLookdev] HDA_Breakroom_Sanctuary cooked and baked successfully.")

    # -------------------------------------------------------------------------
    # 2. HOUDINI PROCEDURAL CEILING HVAC & TROFFER GRID
    # -------------------------------------------------------------------------
    ceiling_mesh = unreal.load_asset("/Game/Meshes/Architecture/SM_Houdini_Ceiling_HVAC_Grid")
    mat_powder = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Office_PowderCoat")
    if ceiling_mesh:
        for a in ELL.get_all_level_actors():
            if a.get_actor_label() == "Houdini_Ceiling_HVAC_Grid":
                ELL.destroy_actor(a)
        
        ceil_actor = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, 0.0))
        ceil_actor.set_actor_label("Houdini_Ceiling_HVAC_Grid")
        smc = ceil_actor.get_component_by_class(unreal.StaticMeshComponent)
        smc.set_static_mesh(ceiling_mesh)
        smc.set_mobility(unreal.ComponentMobility.MOVABLE)
        if mat_powder:
            for mi in range(smc.get_num_materials()):
                smc.set_material(mi, mat_powder)
        if hasattr(ceil_actor, "set_folder_path"):
            ceil_actor.set_folder_path("Houdini_Bakes_Ceiling_Grid")
        unreal.log("[HoudiniLookdev] Staged Houdini_Ceiling_HVAC_Grid above cubicle labyrinth.")

    # -------------------------------------------------------------------------
    # 3. ATMOSPHERIC VOLUMETRIC VFX & IMPERFECTER POLISH
    # -------------------------------------------------------------------------
    # 3A. Exponential Height Fog
    # Routed through film304_fog. This previously looped over every height fog actor
    # of class and hard-coded extinction 1.2, which both re-enabled fog on any
    # duplicate actor and reverted the render-reviewed 4.0 on every re-run.
    film304_fog.assert_single_owner()
    _fog_receipt = film304_fog.apply(
        {"fog_density": 0.002},
        film304_fog.INTENT_SHOT_LOOK,
    )
    _fog_baseline = film304_fog.apply_reviewed_baseline()
    unreal.log(
        f"[HoudiniLookdev] Volumetric fog on {film304_fog.FOG_ACTOR_LABEL} "
        f"(Mie scattering {film304_fog.REVIEWED_SCATTERING_DISTRIBUTION}): "
        f"{json.dumps({'shot': _fog_receipt['changed'], 'baseline': _fog_baseline['changed']})}"
    )

    # 3B. Directional SunBeam Volumetric Scattering
    lights = unreal.GameplayStatics.get_all_actors_of_class(ELL.get_editor_world(), unreal.DirectionalLight)
    for l in lights:
        if "SunBeam" in l.get_actor_label():
            lc = l.get_component_by_class(unreal.DirectionalLightComponent)
            if lc:
                lc.set_editor_property("volumetric_scattering_intensity", 4.0)
                lc.set_editor_property("intensity", 18.0)
                unreal.log(f"[HoudiniLookdev] Dialed sunbeam volumetric scattering on {l.get_actor_label()} to 4.0.")

    # 3C. Niagara Floating Dust Motes in Sunbeam Cone
    dust_sys = unreal.load_asset("/Game/_ThirdParty/UltraDynamicSky/Particles/Dust")
    if dust_sys:
        for a in ELL.get_all_level_actors():
            if a.get_actor_label() == "VFX_DustMotes_WindowRays":
                ELL.destroy_actor(a)
        
        dust_actor = EAS.spawn_actor_from_class(unreal.NiagaraActor, unreal.Vector(50.0, 100.0, 140.0))
        dust_actor.set_actor_label("VFX_DustMotes_WindowRays")
        nc = dust_actor.get_component_by_class(unreal.NiagaraComponent)
        if nc:
            nc.set_asset(dust_sys)
            nc.set_editor_property("auto_activate", True)
        if hasattr(dust_actor, "set_folder_path"):
            dust_actor.set_folder_path("Baked_Cinematic_VFX")
        unreal.log("[HoudiniLookdev] Spawned Niagara floating dust motes actor in window sunbeams.")

    # 3D. PostProcessVolume_1 Polish (Imperfecter Lens Dirt + 35mm Grain + Anamorphic Fringe)
    ppvs = unreal.GameplayStatics.get_all_actors_of_class(ELL.get_editor_world(), unreal.PostProcessVolume)
    for pp in ppvs:
        if pp.get_actor_label() == "PostProcessVolume_1":
            s = pp.get_editor_property("settings")
            s.set_editor_property("bloom_method", unreal.BloomMethod.BM_SOG)
            s.set_editor_property("bloom_intensity", 0.75)
            s.set_editor_property("bloom_dirt_mask_intensity", 2.0)
            s.set_editor_property("scene_fringe_intensity", 0.18) # Anamorphic chromatic aberration
            s.set_editor_property("vignette_intensity", 0.42)
            s.set_editor_property("film_grain_intensity_shadows", 0.85)
            s.set_editor_property("film_grain_intensity_midtones", 0.70)
            s.set_editor_property("film_grain_intensity_highlights", 0.50)
            pp.set_editor_property("settings", s)
            unreal.log("[HoudiniLookdev] Dialed Imperfecter post-process settings on PostProcessVolume_1.")

    # -------------------------------------------------------------------------
    # 4. COMPOSED CINEMATIC CINECAMERAS
    # -------------------------------------------------------------------------
    def spawn_camera(label: str, loc: tuple, target: tuple, focal: float, f_stop: float, folder: str):
        for a in ELL.get_all_level_actors():
            if a.get_actor_label() == label:
                ELL.destroy_actor(a)
        
        cam = EAS.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(*loc))
        cam.set_actor_label(label)
        if hasattr(cam, "set_folder_path"):
            cam.set_folder_path(folder)

        dx = target[0] - loc[0]
        dy = target[1] - loc[1]
        dz = target[2] - loc[2]
        dist_xy = math.sqrt(dx*dx + dy*dy)
        yaw = math.degrees(math.atan2(dy, dx))
        pitch = math.degrees(math.atan2(dz, dist_xy))
        cam.set_actor_rotation(unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0), False)

        comp = cam.get_cine_camera_component()
        comp.current_focal_length = focal
        comp.filmback.sensor_width = 36.0
        comp.filmback.sensor_height = 20.25 # 16:9
        comp.lens_settings.min_f_stop = 1.2
        comp.lens_settings.max_f_stop = 22.0
        comp.current_aperture = f_stop
        
        dist_3d = math.sqrt(dx*dx + dy*dy + dz*dz)
        comp.focus_settings.focus_method = unreal.CameraFocusMethod.MANUAL
        comp.focus_settings.manual_focus_distance = dist_3d
        return cam

    # 4A. Hero Cubicle Establishing Shot (High-angle wide diagonal sweeping across the labyrinth)
    spawn_camera(
        label="CineCam_Hero_CubicleEstablishing",
        loc=(220.0, -950.0, 420.0),
        target=(850.0, -100.0, 90.0),
        focal=24.0,
        f_stop=3.2,
        folder="Cinematic_Cameras"
    )
    # 4B. Hero Cubicle Trench Shot (Low-angle claustrophobic aisle tracking)
    spawn_camera(
        label="CineCam_Hero_CubicleTrench",
        loc=(825.0, -780.0, 95.0),
        target=(825.0, 250.0, 95.0),
        focal=35.0,
        f_stop=2.4,
        folder="Cinematic_Cameras"
    )
    # 4C. Hero Breakroom Establishing Shot (ZMJ Kitchen Sanctuary)
    spawn_camera(
        label="CineCam_Hero_BreakroomEstablishing",
        loc=(200.0, 280.0, 140.0),
        target=(450.0, 450.0, 110.0),
        focal=35.0,
        f_stop=2.8,
        folder="Cinematic_Cameras"
    )
    # 4D. Hero Corridor Watercooler Vignette
    spawn_camera(
        label="CineCam_Hero_CorridorWatercooler",
        loc=(120.0, 360.0, 115.0),
        target=(230.0, 410.0, 110.0),
        focal=50.0,
        f_stop=2.0,
        folder="Cinematic_Cameras"
    )

    unreal.log("[HoudiniLookdev] Staged 4 hero CineCameras.")

    # -------------------------------------------------------------------------
    # 5. SAVE ACTIVE LEVEL
    # -------------------------------------------------------------------------
    saved = ELL.save_current_level()
    unreal.log(f"[HoudiniLookdev] ALL STAGES COMPLETE. Level save status: {saved}")
    return saved

if __name__ == "__main__":
    execute_lookdev()
