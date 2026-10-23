import os, shutil, gc
import unreal

WORLD = unreal.EditorLevelLibrary.get_editor_world()
OUT_DIR = "G:/film-304-toon-spine/Saved/Renders/FilmOffice"
ARTIFACT_DIR = "C:/Users/froma/.gemini/antigravity-ide/brain/10d93b13-68af-4057-ae2d-343574ed43dd"
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

# Find PPV_StorybookOutline for comfortable filmic auto-exposure and toon finish
ppv_settings = None
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "PPV_StorybookOutline":
        ppv_settings = a.settings
        break

cams = [
    ("SESSION_CAM_Cast", "shot1_hero_cast_master.png"),
    ("Film_Cam_OfficeWide", "shot2_office_wide_master.png"),
    ("Film_Cam_David_DeskSleep", "shot3_david_desk_sleep_master.png"),
    ("CineCam_Hero_WindowEstablishing", "shot4_window_establishing_master.png")
]

print("=== CAPTURING 4 MASTER SCENES WITH CLEAN EXPOSURE ===")

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
    cc = cam_actor.get_component_by_class(unreal.CineCameraComponent)
    fov = cc.field_of_view if cc else 60.0
    
    rt = unreal.RenderingLibrary.create_render_target2d(WORLD, 1920, 1080, format=unreal.TextureRenderTargetFormat.RTF_RGBA8)
    cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, loc, rot)
    comp = cap.get_component_by_class(unreal.SceneCaptureComponent2D)
    comp.texture_target = rt
    comp.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
    comp.fov_angle = fov
    
    if ppv_settings:
        comp.post_process_settings = ppv_settings
        
    comp.capture_scene()
    unreal.RenderingLibrary.export_render_target(WORLD, rt, OUT_DIR, out_name)
    unreal.EditorLevelLibrary.destroy_actor(cap)
    
    src = f"{OUT_DIR}/{out_name}"
    dst = f"{ARTIFACT_DIR}/{out_name}"
    if os.path.exists(src):
        shutil.copy2(src, dst)
        sz = os.path.getsize(dst)
        print(f"Exported {out_name} ({sz} bytes)")
    gc.collect()

print("ALL 4 MASTER SCENES EXPORTED!")
