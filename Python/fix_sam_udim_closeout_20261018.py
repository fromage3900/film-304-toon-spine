"""Repair only the assembly actor's shifted skin texture overrides; no graph edits."""
import json
from pathlib import Path
import unreal

def main():
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert 'L_Film_Office_Assembly_20261018_v02.' in world.get_path_name()
    sam=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='Film_Cast_Sam')
    comp=sam.get_component_by_class(unreal.SkeletalMeshComponent)
    original=comp.get_material(0)
    dest='/Game/Materials/Instances/Film304/Cast/Sam/Closeout20261018'
    name='MI_Sam_Skin_Toon_BrowA_UDIMCorrect_v01'
    assert not unreal.EditorAssetLibrary.does_asset_exist(dest+'/'+name)
    fixed=unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(name,dest,original)
    textures={1001:'T_SamSkin_Tile1_BrowA',1002:'T_SamSkin_Tile2',1003:'T_SamSkin_Tile3'}
    for tile,name in textures.items():
        tex=unreal.load_asset('/Game/Materials/Textures/OneDriveRigs_20261016/'+name)
        assert tex and tex.virtual_texture_streaming
        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(fixed,'BaseColorTile'+str(tile),tex)
    unreal.MaterialEditingLibrary.update_material_instance(fixed)
    assert unreal.MaterialEditingLibrary.get_material_instance_static_switch_parameter_value(fixed,'bFilmUseUDIM')
    assert unreal.EditorAssetLibrary.save_loaded_asset(fixed)
    comp.modify();comp.set_material(0,fixed)
    cam=actors.spawn_actor_from_class(unreal.CineCameraActor,unreal.Vector(25,-230,135))
    cam.set_actor_label('Film_Cam_Closeout_SamUDIM');cam.set_folder_path('Film304/FinalAssembly/Cameras')
    cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(cam.get_actor_location(),unreal.Vector(-55,-55,115)),False)
    cine=cam.get_cine_camera_component();cine.current_focal_length=45;cine.current_aperture=8
    fb=cine.filmback;fb.sensor_width=36;cine.filmback=fb
    focus=cine.focus_settings;focus.focus_method=unreal.CameraFocusMethod.DISABLE;cine.focus_settings=focus
    report={'world':world.get_path_name(),'source_instance':original.get_path_name(),'corrected_instance':fixed.get_path_name(),
            'slot':0,'tiles':{str(k):v for k,v in textures.items()},'parent_unchanged':original.parent==fixed.parent,
            'shared_graphs_edited':False,'mesh_uvs_edited':False,'visual_gate':'pending close-up'}
    out=Path(unreal.Paths.project_dir())/'Saved/Audit/Closeout_20261018/sam_udim_fix.json'
    out.write_text(json.dumps(report,indent=2));print(json.dumps(report))

if __name__=='__main__':main()
