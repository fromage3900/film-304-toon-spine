"""Comprehensive 3-Look Lighting Controller & Multi-Camera Capture for L_Film_Office.

Looks:
- 'day':   Midday High-Key (clean crisp shadows, natural blue sky, balanced interior)
- 'dusk':  Terracotta & Teal Dusk (golden hour raking sunbeams, deep teal sky, warm rim kicks)
- 'night': Overtime Night (troffers & desk lamps as primary keys, dark navy sky, glowing city skyline)
"""
import os
import math
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ME = unreal.MaterialEditingLibrary

OUT_DIR = "G:/film-304-toon-spine/Saved/Renders/FilmOffice/Looks"
os.makedirs(OUT_DIR, exist_ok=True)

cams = [
    ("SESSION_CAM_Cast", "shot1_hero_cast"),
    ("Film_Cam_OfficeWide", "shot2_office_wide"),
    ("Film_Cam_David_DeskSleep", "shot3_david_desk_sleep"),
    ("CineCam_Hero_WindowEstablishing", "shot4_window_establishing")
]

def apply_look(look_name: str):
    print(f"\n==========================================")
    print(f"=== APPLYING LIGHTING LOOK: {look_name.upper()} ===")
    print(f"==========================================")
    
    # 1. Post Process Volume & Exposure
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() in ["PPV_StorybookOutline", "PPV_P4_CleanCinematic"]:
            s = a.settings
            s.override_auto_exposure_method = True
            s.auto_exposure_method = unreal.AutoExposureMethod.AEM_HISTOGRAM
            s.override_auto_exposure_min_brightness = True
            s.auto_exposure_min_brightness = 0.03
            s.override_auto_exposure_max_brightness = True
            s.auto_exposure_max_brightness = 5.0
            s.override_bloom_intensity = True
            s.override_bloom_threshold = True
            
            if look_name == "day":
                s.override_auto_exposure_bias = True
                s.auto_exposure_bias = 0.75
                s.bloom_intensity = 0.25
                s.bloom_threshold = 1.2
            elif look_name == "dusk":
                s.override_auto_exposure_bias = True
                s.auto_exposure_bias = 0.95
                s.bloom_intensity = 0.40
                s.bloom_threshold = 0.95
            elif look_name == "night":
                s.override_auto_exposure_bias = True
                s.auto_exposure_bias = 0.85
                s.bloom_intensity = 0.50
                s.bloom_threshold = 0.85
            a.settings = s

    # 2. Lights Configuration
    for a in EAS.get_all_level_actors():
        lbl = a.get_actor_label()
        dl = a.get_component_by_class(unreal.DirectionalLightComponent)
        rl = a.get_component_by_class(unreal.RectLightComponent)
        pl = a.get_component_by_class(unreal.PointLightComponent)
        sl = a.get_component_by_class(unreal.SkyLightComponent)
        
        # Primary Sunbeam
        if lbl == "Light_Cinematic_SunBeam" and dl:
            if look_name == "day":
                dl.set_intensity(4.2)
                dl.set_light_color(unreal.LinearColor(1.0, 0.96, 0.90, 1.0)) # Warm white daylight
                a.set_actor_rotation(unreal.Rotator(pitch=-38.0, yaw=150.0, roll=0.0), False)
            elif look_name == "dusk":
                dl.set_intensity(5.5)
                dl.set_light_color(unreal.LinearColor(1.0, 0.55, 0.22, 1.0)) # Rich Terracotta / Golden
                a.set_actor_rotation(unreal.Rotator(pitch=-12.0, yaw=158.0, roll=0.0), False) # Low raking angle
            elif look_name == "night":
                dl.set_intensity(0.0) # Sun set
                
        # Rim Kicker
        elif lbl == "Cast_RimKicker_Light" and dl:
            if look_name == "day":
                dl.set_intensity(1.2)
                dl.set_light_color(unreal.LinearColor(0.85, 0.92, 1.0, 1.0))
            elif look_name == "dusk":
                dl.set_intensity(2.8)
                dl.set_light_color(unreal.LinearColor(1.0, 0.65, 0.30, 1.0)) # Warm rim kick
            elif look_name == "night":
                dl.set_intensity(0.4)
                dl.set_light_color(unreal.LinearColor(0.20, 0.40, 0.80, 1.0)) # Cool night rim
                
        # Fill Light
        elif lbl == "EST_Fill_E1" and dl:
            if look_name == "day":
                dl.set_intensity(0.8)
                dl.set_light_color(unreal.LinearColor(0.70, 0.85, 1.0, 1.0))
            elif look_name == "dusk":
                dl.set_intensity(1.2)
                dl.set_light_color(unreal.LinearColor(0.15, 0.45, 0.60, 1.0)) # Deep teal sky fill
            elif look_name == "night":
                dl.set_intensity(0.3)
                dl.set_light_color(unreal.LinearColor(0.05, 0.10, 0.25, 1.0))
                
        # Ceiling Troffers
        elif "Troffer" in lbl and rl:
            if look_name == "day":
                rl.set_intensity(2.2)
                rl.set_light_color(unreal.LinearColor(0.92, 0.95, 1.0, 1.0))
            elif look_name == "dusk":
                rl.set_intensity(2.5)
                rl.set_light_color(unreal.LinearColor(1.0, 0.92, 0.82, 1.0))
            elif look_name == "night":
                rl.set_intensity(3.8) # Primary light source at night
                rl.set_light_color(unreal.LinearColor(0.88, 0.94, 1.0, 1.0))
                
        # Desk Lamps
        elif "DeskLamp" in lbl or "Lamp" in lbl:
            if pl:
                if look_name == "day":
                    pl.set_intensity(3.0)
                    pl.set_light_color(unreal.LinearColor(1.0, 0.90, 0.75, 1.0))
                elif look_name == "dusk":
                    pl.set_intensity(4.5)
                    pl.set_light_color(unreal.LinearColor(1.0, 0.82, 0.60, 1.0))
                elif look_name == "night":
                    pl.set_intensity(6.5) # Warm pools over sleeping David & desks
                    pl.set_light_color(unreal.LinearColor(1.0, 0.78, 0.50, 1.0))
                    
        # Skylight
        elif sl:
            if look_name == "day":
                sl.set_intensity(1.2)
            elif look_name == "dusk":
                sl.set_intensity(0.8)
            elif look_name == "night":
                sl.set_intensity(0.3)

    # 3. Living Window Materials on Skyline Towers
    mi_warm = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_Glazing_WarmOffice")
    mi_cool = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_Glazing_CoolOffice")
    
    if mi_warm and mi_cool:
        if look_name == "day":
            ME.set_material_instance_scalar_parameter_value(mi_warm, "GlowIntensity", 0.3)
            ME.set_material_instance_scalar_parameter_value(mi_cool, "GlowIntensity", 0.2)
        elif look_name == "dusk":
            ME.set_material_instance_scalar_parameter_value(mi_warm, "GlowIntensity", 1.8)
            ME.set_material_instance_scalar_parameter_value(mi_cool, "GlowIntensity", 1.2)
        elif look_name == "night":
            ME.set_material_instance_scalar_parameter_value(mi_warm, "GlowIntensity", 3.2)
            ME.set_material_instance_scalar_parameter_value(mi_cool, "GlowIntensity", 2.4)
        ME.update_material_instance(mi_warm)
        ME.update_material_instance(mi_cool)

    # 4. Troffer Diffuser Material
    mat_troffer = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Office_Troffer")
    if mat_troffer:
        if look_name == "day":
            ME.set_material_instance_scalar_parameter_value(mat_troffer, "EmissiveIntensity", 0.02)
        elif look_name == "dusk":
            ME.set_material_instance_scalar_parameter_value(mat_troffer, "EmissiveIntensity", 0.03)
        elif look_name == "night":
            ME.set_material_instance_scalar_parameter_value(mat_troffer, "EmissiveIntensity", 0.06)
        ME.update_material_instance(mat_troffer)

    unreal.EditorLevelLibrary.save_current_level()
    print(f"Applied look {look_name.upper()} successfully!")

def render_look(look_name: str):
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    # Grab active post process settings
    ppv_settings = None
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == "PPV_StorybookOutline":
            ppv_settings = a.settings
            break
            
    for cam_label, shot_prefix in cams:
        cam_actor = None
        for a in EAS.get_all_level_actors():
            if a.get_actor_label() == cam_label:
                cam_actor = a
                break
        if not cam_actor:
            print(f"Warning: camera {cam_label} not found!")
            continue
            
        loc = cam_actor.get_actor_location()
        rot = cam_actor.get_actor_rotation()
        cc = cam_actor.get_component_by_class(unreal.CineCameraComponent)
        fov = cc.field_of_view if cc else 60.0
        
        rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, format=unreal.TextureRenderTargetFormat.RTF_RGBA8)
        cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, loc, rot)
        comp = cap.get_component_by_class(unreal.SceneCaptureComponent2D)
        comp.texture_target = rt
        comp.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
        comp.fov_angle = fov
        if ppv_settings:
            comp.post_process_settings = ppv_settings
            
        comp.capture_scene()
        filename = f"{shot_prefix}_{look_name}.png"
        unreal.RenderingLibrary.export_render_target(world, rt, OUT_DIR, filename)
        unreal.EditorLevelLibrary.destroy_actor(cap)
        print(f"  Rendered {filename}")

if __name__ == "__main__":
    import sys
    look = sys.argv[1] if len(sys.argv) > 1 else "dusk"
    apply_look(look)
    render_look(look)
