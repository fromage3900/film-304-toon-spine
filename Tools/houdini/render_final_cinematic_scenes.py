"""Renders the 4 final cinematic scenes at 1920x1080 with proper pilot spacing and memory management."""
import gc
import os
import shutil
import time
import unreal

RENDER_DIR = "G:/film-304-toon-spine/Saved/Renders/FilmOffice"
ARTIFACT_DIR = "C:/Users/froma/.gemini/antigravity-ide/brain/10d93b13-68af-4057-ae2d-343574ed43dd"
os.makedirs(RENDER_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

cams = [
    ("SESSION_CAM_Cast", "final_shot1_hero_cast.png"),
    ("Film_Cam_OfficeWide", "final_shot2_office_wide.png"),
    ("Film_Cam_David_DeskSleep", "final_shot3_david_sleep.png"),
    ("CineCam_Hero_WindowEstablishing", "final_shot4_window_establishing.png")
]

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== STARTING CINEMATIC SCENE RENDER PIPELINE ===")

for cam_label, out_name in cams:
    cam_actor = None
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == cam_label:
            cam_actor = a
            break
            
    if not cam_actor:
        print(f"ERROR: Camera {cam_label} not found!")
        continue
        
    print(f"\n--- Piloting & Rendering: {cam_label} ---")
    unreal.EditorLevelLibrary.pilot_level_actor(cam_actor)
    time.sleep(1.0)
    
    out_path = f"{RENDER_DIR}/{out_name}"
    unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, out_path)
    print(f"Triggered capture -> {out_path}")
    
    time.sleep(1.5)
    gc.collect()

# Unpilot camera
unreal.EditorLevelLibrary.eject_pilot_level_actor()
print("\n=== All 4 camera renders triggered. Copying to artifacts... ===")

for _, out_name in cams:
    src = f"{RENDER_DIR}/{out_name}"
    dst = f"{ARTIFACT_DIR}/{out_name}"
    if os.path.exists(src):
        shutil.copy2(src, dst)
        sz = os.path.getsize(dst)
        print(f"Copied {out_name} to artifact directory ({sz} bytes)")
    else:
        print(f"Warning: {src} not found on disk yet.")

print("=== Render Pipeline Finished ===")
