"""Carry verified face/sleep/cloud content into current-map shot bindings."""
import json
from pathlib import Path
import unreal

def main():
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert 'L_Film_Office_Assembly_20261018_v02.' in world.get_path_name()
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    bylabel={a.get_actor_label():a for a in actors.get_all_level_actors()}
    source=unreal.load_asset('/Game/Sequences/Film304Idle_20261017/LS_OfficeCast_SleepFaces_48f_v03_SoftSnore')
    assert source
    dest='/Game/Sequences/Film304Closeout_20261018'
    records=[]
    for stem,camera_label in [('Medium','Film_Cam_OfficeMedium'),('David','Film_Cam_David_DeskSleep'),
                               ('Ceiling','Film_Cam_Closeout_CeilingReview')]:
        name='LS_Closeout_'+stem+'48f_v01'
        assert not unreal.EditorAssetLibrary.does_asset_exist(dest+'/'+name)
        seq=unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(name,dest,source)
        clips=[]
        for binding in list(seq.get_possessables()):
            skeletal=[t for t in binding.get_tracks() if isinstance(t,unreal.MovieSceneSkeletalAnimationTrack)]
            if not skeletal:continue
            label=binding.get_name();assert label in bylabel,label
            params=[s.params for t in skeletal for s in t.get_sections()]
            binding.remove()
            new=seq.add_possessable(bylabel[label])
            for data in params:
                track=new.add_track(unreal.MovieSceneSkeletalAnimationTrack)
                section=track.add_section();section.set_range(0,48);section.params=data
                clips.append({'actor':label,'animation':data.animation.get_path_name()})
        camera=seq.add_possessable(bylabel[camera_label])
        cut=seq.add_track(unreal.MovieSceneCameraCutTrack)
        section=cut.add_section();section.set_range(0,48)
        identifier=unreal.MovieSceneObjectBindingID();identifier.set_editor_property('guid',camera.get_id())
        section.set_camera_binding_id(identifier)
        assert unreal.EditorAssetLibrary.save_loaded_asset(seq)
        records.append({'sequence':seq.get_path_name(),'camera':camera_label,'cast_clips':clips,
                        'spawnables':len(seq.get_spawnables()),'fps':24,'range':[0,48]})
    # Make playback and review use the new map-bound sequence in this copy only.
    medium=unreal.load_asset(records[0]['sequence'])
    playback=bylabel.get('Film_OfficeIdle_LoopPlayback')
    if playback:playback.set_sequence(medium)
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(medium)
    unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(20)
    out=Path(unreal.Paths.project_dir())/'Saved/Audit/Closeout_20261018/shot_sequences.json'
    out.write_text(json.dumps({'map':world.get_path_name(),'shots':records},indent=2))
    print(json.dumps(records))

if __name__=='__main__':main()
