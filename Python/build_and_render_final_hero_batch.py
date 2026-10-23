"""Build final hero sequences, MRQ configs, populate Q_Office_ReadyToRender, and capture proofs."""
import json
import math
from pathlib import Path
import unreal
import claireon

ROOT = Path(unreal.Paths.project_dir())
MAP_NAME = "L_Film_Office"
SEQ_DIR = "/Game/Sequences/Film304Hero_20261018"
CFG_DIR = "/Game/MoviePipelines/Hero20261018"
OUT_DIR = ROOT / "Showcase/Film304_Hero_20261018/Final"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EAL = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EL = unreal.EditorLevelLibrary
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

assert world.get_name() == MAP_NAME, f"Active world is {world.get_name()}, expected {MAP_NAME}"

actors_by_label = {a.get_actor_label(): a for a in EAS.get_all_level_actors()}

# 1. Professional Lighting, Exposure, and Camera Focus Polish
HERO_SPECS = [
    {
        "cam_label": "HERO01_Wide_Establishing",
        "stem": "HERO01_Wide_Establishing",
        "bias": 1.35,
        "focal_length": 24.0,
        "aperture": 3.5,
        "focus_dist": 700.0,
        "vignette": 0.35,
        "note": "24mm Wide Establishing: Full office volume, Bay 1-3 skyline, desk rows"
    },
    {
        "cam_label": "HERO02_Medium_TwoShot",
        "stem": "HERO02_Medium_TwoShot",
        "bias": 1.40,
        "focal_length": 35.0,
        "aperture": 2.8,
        "focus_dist": 380.0,
        "vignette": 0.35,
        "note": "35mm Medium Two-Shot: David sleeping FG, Dana working MG, breakroom BG"
    },
    {
        "cam_label": "HERO03_Close_Portrait",
        "stem": "HERO03_Close_Portrait",
        "bias": 1.45,
        "focal_length": 75.0,
        "aperture": 2.0,
        "focus_dist": 120.0,
        "vignette": 0.45,
        "note": "75mm Close Portrait: Intimate MCU of Dana, creamy bokeh, warm skin tones"
    },
    {
        "cam_label": "HERO04_Macro_Insert",
        "stem": "HERO04_Macro_Insert",
        "bias": 1.50,
        "focal_length": 100.0,
        "aperture": 2.8,
        "focus_dist": 68.0,
        "vignette": 0.45,
        "note": "100mm Macro Insert: Spider crawling on keyboard/monitor base"
    },
]

# Apply camera parameters
for spec in HERO_SPECS:
    cam = actors_by_label.get(spec["cam_label"])
    if not cam:
        continue
    cc = cam.get_cine_camera_component()
    cc.set_editor_property("current_focal_length", spec["focal_length"])
    cc.set_editor_property("current_aperture", spec["aperture"])
    
    fs = cc.get_editor_property("focus_settings")
    fs.set_editor_property("focus_method", unreal.CameraFocusMethod.MANUAL)
    fs.set_editor_property("manual_focus_distance", spec["focus_dist"])
    cc.set_editor_property("focus_settings", fs)
    
    pp = cc.get_editor_property("post_process_settings")
    pp.set_editor_property("override_auto_exposure_bias", True)
    pp.set_editor_property("auto_exposure_bias", spec["bias"])
    pp.set_editor_property("override_vignette_intensity", True)
    pp.set_editor_property("vignette_intensity", spec["vignette"])
    pp.set_editor_property("override_scene_fringe_intensity", True)
    pp.set_editor_property("scene_fringe_intensity", 0.15)
    cc.set_editor_property("post_process_settings", pp)
    print(f"Polished camera {spec['cam_label']}: {spec['focal_length']}mm f/{spec['aperture']} focus={spec['focus_dist']}cm bias={spec['bias']}")

# 2. Refine Global PPV (PPV_ToonOutlineClean)
ppv = actors_by_label.get("PPV_ToonOutlineClean")
if ppv:
    s = ppv.get_editor_property("settings")
    s.set_editor_property("override_bloom_intensity", True)
    s.set_editor_property("bloom_intensity", 0.65)
    s.set_editor_property("override_bloom_size_scale", True)
    s.set_editor_property("bloom_size_scale", 3.5)
    s.set_editor_property("override_film_grain_intensity", True)
    s.set_editor_property("film_grain_intensity", 0.035)
    ppv.set_editor_property("settings", s)
    print("Polished PPV_ToonOutlineClean bloom and film grain.")

# 3. Build Level Sequences for the 4 hero shots
ANIM_MAP = {
    "Film_Subject_Dana_v08_CleanSkin": "/Game/Staging/Film304Repaired_20261017/Poses_Headless/AS_Dana_LeanDesk_Polish01",
    "Film_Cast_David": "/Game/Animations/Film304Idle_20261017/AS_David_DeskSleep_PalmUp_48f_v03",
    "Film_Cast_Sam": "/Game/Animations/Film304Idle_20261017/AS_Sam_OfficeFaceIdle_48f_v02",
    "Spider_Deform_v2": "/Game/Animations/Film304Idle_20261017/AS_Spider_OfficeIdle_48f_v01",
}
SNORE_SUBSEQ = "/Game/Sequences/Film304Idle_20261017/LS_OfficeCast_SleepFaces_48f_v03_SoftSnore"
snore_asset = unreal.load_asset(SNORE_SUBSEQ)

for spec in HERO_SPECS:
    seq_name = f"{SEQ_DIR}/LS_{spec['stem']}"
    cam = actors_by_label.get(spec["cam_label"])
    if not cam:
        continue
    
    if EAL.does_asset_exist(seq_name):
        EAL.delete_asset(seq_name)
    
    seq = TOOLS.create_asset(f"LS_{spec['stem']}", SEQ_DIR, unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
    seq.set_display_rate(unreal.FrameRate(24, 1))
    seq.set_playback_start(0)
    seq.set_playback_end(48)
    
    # Possess camera
    cam_binding = seq.add_possessable(cam)
    cut_track = seq.add_track(unreal.MovieSceneCameraCutTrack)
    cut_section = cut_track.add_section()
    cut_section.set_range(0, 48)
    bind_id = unreal.MovieSceneObjectBindingID()
    bind_id.set_editor_property("guid", cam_binding.get_id())
    cut_section.set_camera_binding_id(bind_id)
    
    # Bind cast
    for actor_lbl, anim_path in ANIM_MAP.items():
        actor = actors_by_label.get(actor_lbl)
        clip = unreal.load_asset(anim_path)
        if actor and clip:
            cbinding = seq.add_possessable(actor)
            track = cbinding.add_track(unreal.MovieSceneSkeletalAnimationTrack)
            sec = track.add_section()
            sec.set_range(0, 48)
            params = sec.get_editor_property("params")
            params.set_editor_property("animation", clip)
            sec.set_editor_property("params", params)
    
    # Add snore subsequence so soft snore clouds evaluate at frame 20
    if snore_asset:
        sub_track = seq.add_track(unreal.MovieSceneSubTrack)
        sub_sec = sub_track.add_section()
        sub_sec.set_range(0, 48)
        sub_sec.set_editor_property("sub_sequence", snore_asset)
    
    EAL.save_loaded_asset(seq, False)
    print(f"Created LevelSequence: {seq_name}")

# 4. Build MRQ MasterConfigs
source_cfg = unreal.load_asset("/Game/MoviePipelines/Film304Closeout_20261018/CFG_Office_Still20_1080_v01")
for spec in HERO_SPECS:
    cfg_name = f"{CFG_DIR}/CFG_{spec['stem']}"
    if EAL.does_asset_exist(cfg_name):
        EAL.delete_asset(cfg_name)
    
    cfg = TOOLS.duplicate_asset(f"CFG_{spec['stem']}", CFG_DIR, source_cfg)
    out_set = cfg.find_setting_by_class(unreal.MoviePipelineOutputSetting)
    out_set.output_resolution = unreal.IntPoint(1920, 1080)
    out_set.use_custom_playback_range = True
    out_set.custom_start_frame = 20
    out_set.custom_end_frame = 21
    out_set.file_name_format = f"{spec['stem']}"
    out_set.output_directory = unreal.DirectoryPath(str(OUT_DIR))
    out_set.override_existing_output = True
    EAL.save_loaded_asset(cfg, False)
    print(f"Created MRQ MasterConfig: {cfg_name}")

# 5. Populate Q_Office_ReadyToRender
queue = unreal.load_asset("/Game/MoviePipelines/Film304Closeout_20261018/Q_Office_ReadyToRender")
if queue:
    queue.modify()
    queue.delete_all_jobs()
    
    # Add Hero Jobs (Frame 20 Stills)
    for idx, spec in enumerate(HERO_SPECS):
        seq = unreal.load_asset(f"{SEQ_DIR}/LS_{spec['stem']}")
        cfg = unreal.load_asset(f"{CFG_DIR}/CFG_{spec['stem']}")
        if seq and cfg:
            job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
            job.job_name = f"0{idx+1}_{spec['stem']}"
            job.map = unreal.SoftObjectPath(world.get_path_name())
            job.sequence = unreal.SoftObjectPath(seq.get_path_name())
            job.set_configuration(cfg)
    
    # Add Main Composed Shots
    for idx, name in enumerate(["Ensemble_Warm", "Ensemble_Cool", "Ensemble_Neutral", "Dana_Neutral", "David_Warm"]):
        seq = unreal.load_asset(f"/Game/Sequences/Film304Closeout_20261018/LS_MainOffice_{name}_48f_v01")
        cfg = unreal.load_asset("/Game/MoviePipelines/Film304Closeout_20261018/CFG_Office_Still20_1080_v01")
        if seq and cfg:
            job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
            job.job_name = f"0{len(HERO_SPECS)+idx+1}_{name}"
            job.map = unreal.SoftObjectPath(world.get_path_name())
            job.sequence = unreal.SoftObjectPath(seq.get_path_name())
            job.set_configuration(cfg)
    
    # Add Night Skyline Shots
    for idx, name in enumerate(["Skyline_BlueHour", "Skyline_Midnight"]):
        seq = unreal.load_asset(f"/Game/Sequences/Film304Closeout_20261018/Skyline/LS_{name}_48f_v01")
        cfg = unreal.load_asset(f"/Game/MoviePipelines/Film304Closeout_20261018/CFG_Closeout_{name}_Study_v60")
        if seq and cfg:
            job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
            job.job_name = f"{10+idx}_{name}"
            job.map = unreal.SoftObjectPath(world.get_path_name())
            job.sequence = unreal.SoftObjectPath(seq.get_path_name())
            job.set_configuration(cfg)
            
    EAL.save_loaded_asset(queue, False)
    print(f"Populated Q_Office_ReadyToRender with {len(queue.get_jobs())} jobs.")

# 6. Capture Clean Final Viewport Proofs for the 4 Hero Cameras
start_loc, start_rot = EL.get_level_viewport_camera_info()
EAS.set_selected_level_actors([])
unreal.SystemLibrary.execute_console_command(world, "ShowFlag.Editor 0")

captured_frames = []
try:
    for spec in HERO_SPECS:
        cam = actors_by_label.get(spec["cam_label"])
        if not cam:
            continue
        EL.set_level_viewport_camera_info(cam.get_actor_location(), cam.get_actor_rotation())
        filename = f"{spec['stem']}.png"
        res = claireon.slate_screenshot(target="level_viewport", filename=filename, directory=str(OUT_DIR))
        captured_frames.append({
            "shot": spec["stem"],
            "camera": spec["cam_label"],
            "file": (res or {}).get("data", {}).get("file_path"),
            "focal_length": spec["focal_length"],
            "aperture": spec["aperture"],
            "focus_dist": spec["focus_dist"],
        })
finally:
    unreal.SystemLibrary.execute_console_command(world, "ShowFlag.Editor 1")
    EL.set_level_viewport_camera_info(start_loc, start_rot)

# Save dirty level
unreal.EditorLoadingAndSavingUtils.save_current_level()
print("Saved active level L_Film_Office cleanly.")

manifest = {
    "status": "READY_TO_RENDER",
    "world": world.get_path_name(),
    "hero_shots": captured_frames,
    "queue_jobs": len(queue.get_jobs()) if queue else 0,
    "output_dir": str(OUT_DIR)
}
(OUT_DIR / "final_hero_manifest.json").write_text(json.dumps(manifest, indent=2))
print("HERO_BATCH_COMPLETE")
print(json.dumps(manifest, indent=2))
