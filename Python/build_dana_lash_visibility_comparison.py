"""Build a dedicated canonical-vs-visible-lash FBX comparison level."""
import json
import math
import sys
import time
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[1]
MAP = "/Game/Maps/Lookdev/L_Dana_LashVisibility_Compare"
MESHES = [
    ("Canonical", "/Game/Meshes/Office/Props/C_DanaRenderTest_OSC", 0.0),
    ("VisibleLashes", "/Game/Preview/DanaLashesVisibleV02/Dana_WeightedLashesVisible_v02", 0.0),
]
OUT = ROOT / "Saved/Audit/dana_lash_visibility_comparison.json"
SLOTS = {
    "danahair_mat": "/Game/Materials/Instances/DanaFilm/MI_DanaFilm_Hair",
    "danairis_mat": "/Game/Materials/Instances/DanaFilm/MI_DanaFilm_Iris",
    "danaeye_mat": "/Game/Materials/Instances/DanaFilm/MI_DanaFilm_EyeWhite",
    "danacornea_mat": "/Game/Materials/Instances/DanaFilm/MI_DanaFilm_Cornea",
    "danaeyeint_mat": "/Game/Materials/Instances/DanaFilm/MI_DanaFilm_EyeInterior",
    "danashoes_mat": "/Game/Materials/Instances/DanaFilm/MI_DanaFilm_Shoes",
    "danapantsbutton_mat": "/Game/Materials/Instances/DanaFilm/MI_DanaFilm_Button",
    "danapants_mat": "/Game/Materials/Instances/DanaFilm/MI_DanaFilm_Skirt",
    "danashirt_mat": "/Game/Materials/Instances/DanaFilm/MI_DanaFilm_Shirt",
    "danaskin_mat": "/Game/Materials/Instances/DanaFilm/MI_DanaFilm_Skin",
    "openpbr_shader1": "/Game/Materials/Masters/DanaFilm/M_DanaFilm_ImportHelpers_Hidden",
}
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
eal = unreal.EditorAssetLibrary
prefix = "DANA_LASHCMP_"

def spawn(cls, loc, rot, name):
    a = sub.spawn_actor_from_class(cls, loc, rot, transient=False)
    if not a: raise RuntimeError("spawn failed: " + name)
    a.set_actor_label(prefix + name)
    return a

def look_at(a, b):
    d = unreal.Vector(b.x-a.x,b.y-a.y,b.z-a.z)
    return unreal.MathLibrary.find_look_at_rotation(a,b)

def build():
    if eal.does_asset_exist(MAP):
        if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP):
            raise RuntimeError("could not load comparison level")
        for actor in list(sub.get_all_level_actors()):
            if actor.get_actor_label().startswith(prefix): sub.destroy_actor(actor)
    else:
        if not unreal.EditorLevelLibrary.new_level(MAP): raise RuntimeError("new map failed")
        if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP):
            raise RuntimeError("could not load new comparison level")
    report=[]
    for name,path,y in MESHES:
        mesh=unreal.load_asset(path)
        if not mesh: raise RuntimeError("mesh missing: "+path)
        x=-40.0 if name=="Canonical" else 40.0
        a=spawn(unreal.SkeletalMeshActor,unreal.Vector(x,y,0),unreal.Rotator(0,0,-115),name)
        c=a.get_component_by_class(unreal.SkeletalMeshComponent)
        c.set_skeletal_mesh_asset(mesh)
        assigned=[]
        for i,slot in enumerate(mesh.materials):
            key=str(slot.material_slot_name).lower()
            matpath=SLOTS.get(key)
            mat=unreal.load_asset(matpath) if matpath else None
            if not mat: raise RuntimeError("material not mapped: "+key)
            c.set_material(i,mat)
            assigned.append({"slot":str(slot.material_slot_name),"material":mat.get_path_name()})
        report.append({"variant":name,"mesh":mesh.get_path_name(),"materials":assigned})
    floor=spawn(unreal.StaticMeshActor,unreal.Vector(0,0,-1),unreal.Rotator(0,0,0),"Floor")
    fc=floor.get_component_by_class(unreal.StaticMeshComponent)
    fc.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Plane"))
    fc.set_world_scale3d(unreal.Vector(6,6,1))
    # Match the working Dana lookdev camera relative to Dana's own facing.
    front=unreal.MathLibrary.get_forward_vector(unreal.Rotator(0,-115,0))
    right=unreal.MathLibrary.get_right_vector(unreal.Rotator(0,-115,0))
    center_y=0.0
    target=unreal.Vector(0,center_y,57)
    camloc=unreal.Vector(front.x*270+right.x*14,center_y+front.y*270+right.y*14,70)
    cam=spawn(unreal.CineCameraActor,camloc,look_at(camloc,target),"Camera")
    cc=cam.get_cine_camera_component(); cc.set_editor_property("current_focal_length",45.0)
    cc.set_editor_property("filmback",unreal.CameraFilmbackSettings(sensor_width=35,sensor_height=19.6875))
    pp=unreal.PostProcessSettings()
    pp.set_editor_property("override_auto_exposure_method",True)
    pp.set_editor_property("auto_exposure_method",unreal.AutoExposureMethod.AEM_MANUAL)
    pp.set_editor_property("override_auto_exposure_min_brightness",True)
    pp.set_editor_property("override_auto_exposure_max_brightness",True)
    pp.set_editor_property("auto_exposure_min_brightness",1.0)
    pp.set_editor_property("auto_exposure_max_brightness",1.0)
    cc.set_editor_property("post_process_settings",pp); cc.set_editor_property("post_process_blend_weight",1.0)
    lights=[]
    for name,loc,lumen,color in (("Key",unreal.Vector(front.x*160+right.x*55,front.y*160+right.y*55,132),2600,(255,244,229)),
                                 ("Fill",unreal.Vector(front.x*145-right.x*100,front.y*145-right.y*100,78),750,(221,233,255)),
                                 ("Rim",unreal.Vector(-front.x*95+right.x*30,-front.y*95+right.y*30,125),1100,(255,249,239))):
        l=spawn(unreal.RectLight,loc,look_at(loc,target),"Light_"+name)
        lc=l.get_component_by_class(unreal.RectLightComponent)
        lc.set_intensity_units(unreal.LightUnits.LUMENS); lc.set_editor_property("intensity",lumen)
        lc.set_editor_property("light_color",unreal.Color(*color,255)); lc.set_editor_property("source_width",100.0)
        lc.set_editor_property("source_height",140.0)
        lc.set_editor_property("cast_shadows",name!="Fill")
        lights.append(name)
    if not unreal.EditorLoadingAndSavingUtils.save_current_level(): raise RuntimeError("level save failed")
    seq_dir="/Game/Sequences/DanaLashCompare"
    cfg_dir="/Game/MoviePipelines/DanaLashCompare"
    eal.make_directory(seq_dir); eal.make_directory(cfg_dir)
    seq_path=seq_dir+"/LS_DANA_LASH_VISIBILITY_COMPARE_v01"
    sequence=unreal.load_asset(seq_path)
    if sequence is None:
        sequence=unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "LS_DANA_LASH_VISIBILITY_COMPARE_v01",seq_dir,unreal.LevelSequence,
            unreal.LevelSequenceFactoryNew())
    if not sequence: raise RuntimeError("comparison sequence create failed")
    for track in list(sequence.get_tracks()): sequence.remove_track(track)
    sequence.set_display_rate(unreal.FrameRate(24,1)); sequence.set_playback_start(0); sequence.set_playback_end(1)
    binding=sequence.add_possessable(cam)
    track=sequence.add_track(unreal.MovieSceneCameraCutTrack); section=track.add_section(); section.set_range(0,1)
    bind_id=unreal.MovieSceneObjectBindingID(); bind_id.set_editor_property("guid",binding.get_id())
    section.set_camera_binding_id(bind_id); eal.save_loaded_asset(sequence)
    job="DANA_LASH_VISIBILITY_COMPARE_v01"
    config=eal.load_asset(cfg_dir+"/CFG_"+job)
    if config is None:
        config=unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "CFG_"+job,cfg_dir,unreal.MoviePipelineMasterConfig,
            unreal.MoviePipelinePrimaryConfigFactory())
    out=config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting,True)
    out.set_editor_property("output_resolution",unreal.IntPoint(1600,900))
    out.set_editor_property("output_directory",unreal.DirectoryPath(str(ROOT/"Saved/Renders/dana_lash_compare")))
    out.set_editor_property("file_name_format",job)
    out.set_editor_property("override_existing_output",True)
    png=config.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG,True)
    png.set_is_enabled(True)
    config.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase,True)
    go=config.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting,True)
    go.set_editor_property("texture_streaming",unreal.MoviePipelineTextureStreamingMethod.FULLY_LOAD)
    go.set_editor_property("cinematic_quality_settings",True)
    aa=config.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting,True)
    aa.set_editor_property("engine_warm_up_count",24); aa.set_editor_property("render_warm_up_count",12)
    aa.set_editor_property("override_anti_aliasing",True)
    aa.set_editor_property("anti_aliasing_method",unreal.AntiAliasingMethod.AAM_TEMPORAL_AA)
    aa.set_editor_property("spatial_sample_count",1); aa.set_editor_property("temporal_sample_count",1)
    eal.save_loaded_asset(config,False)
    OUT.write_text(json.dumps({"result":"built","map":MAP,"variants":report,"lights":lights,
        "camera":cam.get_path_name(),"sequence":sequence.get_path_name(),"config":config.get_path_name(),
        "note":"side-by-side static source-pose comparison; imported preview skeleton is separate."},indent=2),encoding="utf-8")
    unreal.log("[DanaLashCompare] "+json.dumps({"map":MAP,"variants":len(report),"lights":lights,"sequence":sequence.get_path_name(),"config":config.get_path_name()}))

action="build"
build()
