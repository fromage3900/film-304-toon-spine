"""High-Fidelity Cinematic Render Pipeline for L_Film_Office.

Captures all 4 hero cameras at 1920x1080 with full film post-processing:
1. SESSION_CAM_Cast -> shot1_hero_cast_master.png
2. Film_Cam_OfficeWide -> shot2_office_wide_master.png
3. Film_Cam_David_DeskSleep -> shot3_david_desk_sleep_master.png
4. CineCam_Hero_WindowEstablishing -> shot4_window_establishing_master.png
"""
import gc
import os
import shutil
import unreal

WORLD = unreal.EditorLevelLibrary.get_editor_world()
OUT_DIR = "G:/film-304-toon-spine/Saved/Renders/FilmOffice"
ARTIFACT_DIR = "C:/Users/froma/.gemini/antigravity-ide/brain/10d93b13-68af-4057-ae2d-343574ed43dd"
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

# Find PostProcessVolume_1 for cinematic grading
ppv_settings = None
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "PostProcessVolume_1":
        ppv = a.get_component_by_class(unreal.PostProcessComponent) or a
        if hasattr(ppv, "settings"):
            ppv_settings = ppv.settings
        break

cams = [
    ("SESSION_CAM_Cast", "shot1_hero_cast_master.png"),
    ("Film_Cam_OfficeWide", "shot2_office_wide_master.png"),
    ("Film_Cam_David_DeskSleep", "shot3_david_desk_sleep_master.png"),
    ("CineCam_Hero_WindowEstablishing", "shot4_window_establishing_master.png")
]

print("=== STARTING CINEMATIC HIGH-FIDELITY RENDER PIPELINE ===")

for cam_label, out_name in cams:
    cam_actor = None
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_actor_label() == cam_label:
            cam_actor = a
            break
            
    if not cam_actor:
        print(f"ERROR: Camera {cam_label} not found!")
        continue

    loc = cam_actor.get_actor_location()
    rot = cam_actor.get_actor_rotation()
    
    # Get accurate FOV from CineCameraComponent
    cc = cam_actor.get_component_by_class(unreal.CineCameraComponent)
    fov = 60.0
    if cc:
        fov = cc.field_of_view
    
    print(f"\n--- Rendering: {cam_label} (FOV: {fov:.1f} deg) -> {out_name} ---")
    
    # Create 1920x1080 RGBA8 Render Target
    rt = unreal.RenderingLibrary.create_render_target2d(
        WORLD, width=1920, height=1080,
        format=unreal.TextureRenderTargetFormat.RTF_RGBA8
    )
    
    # Spawn dedicated SceneCapture2D at camera transform
    cap_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SceneCapture2D, loc, rot
    )
    cap_comp = cap_actor.get_component_by_class(unreal.SceneCaptureComponent2D)
    cap_comp.texture_target = rt
    cap_comp.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
    cap_comp.fov_angle = fov
    
    # Inherit post-process volume grading
    if ppv_settings:
        cap_comp.post_process_settings = ppv_settings
        
    # Render scene to texture
    cap_comp.capture_scene()
    
    # Export render target to PNG
    unreal.RenderingLibrary.export_render_target(WORLD, rt, OUT_DIR, out_name)
    
    # Clean up transient actor
    unreal.EditorLevelLibrary.destroy_actor(cap_actor)
    
    # Copy to artifact directory
    src = f"{OUT_DIR}/{out_name}"
    dst = f"{ARTIFACT_DIR}/{out_name}"
    if os.path.exists(src):
        shutil.copy2(src, dst)
        sz = os.path.getsize(dst)
        print(f"SUCCESS: Exported {out_name} ({sz} bytes) to {dst}")
    else:
        print(f"WARNING: {src} not found on disk after export!")
        
    gc.collect()

print("\n========================================================")
print("CINEMATIC HIGH-FIDELITY RENDER PIPELINE FINISHED!")
print("========================================================")
