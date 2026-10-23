"""Attach only new closeout shot clouds to David's existing head bone."""
import json
from pathlib import Path
import unreal

def main():
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert 'L_Film_Office_Assembly_20261018_v02.' in world.get_path_name()
    head=unreal._closeout_head_transform
    assert head.scale3d.x>1
    records=[]
    for shot in ['Medium','David','Ceiling','WindowHero']:
        path='/Game/Sequences/Film304Closeout_20261018/LS_Closeout_'+shot+'48f_v01'
        seq=unreal.load_asset(path);assert seq
        david=next(b for b in seq.get_possessables() if b.get_name()=='Film_Cast_David')
        target=unreal.MovieSceneObjectBindingID();target.set_editor_property('guid',david.get_id())
        for cloud in seq.get_spawnables():
            if not cloud.get_name().startswith('Film_David_SoftSnore_'):continue
            assert not any(isinstance(t,unreal.MovieScene3DAttachTrack) for t in cloud.get_tracks())
            transform=next(t for t in cloud.get_tracks() if isinstance(t,unreal.MovieScene3DTransformTrack))
            channels=transform.get_sections()[0].get_all_channels()
            keys=[c.get_keys() for c in channels];assert all(len(k)==49 for k in keys)
            for index in range(49):
                old=unreal.Vector(*(keys[c][index].get_value() for c in range(3)))
                local=head.inverse_transform_location(old)
                for c,value in enumerate(local.to_tuple()):keys[c][index].set_value(value)
                for c,scale in zip(range(6,9),head.scale3d.to_tuple()):
                    keys[c][index].set_value(keys[c][index].get_value()/scale)
            track=cloud.add_track(unreal.MovieScene3DAttachTrack)
            section=track.add_section();section.set_range(0,48)
            section.set_constraint_binding_id(target)
            section.attach_component_name='SkeletalMeshComponent0';section.attach_socket_name='Head_M'
            section.attachment_location_rule=unreal.AttachmentRule.KEEP_RELATIVE
            section.attachment_rotation_rule=unreal.AttachmentRule.KEEP_RELATIVE
            section.attachment_scale_rule=unreal.AttachmentRule.KEEP_RELATIVE
            section.detachment_location_rule=unreal.DetachmentRule.KEEP_WORLD
            section.detachment_rotation_rule=unreal.DetachmentRule.KEEP_WORLD
            section.detachment_scale_rule=unreal.DetachmentRule.KEEP_WORLD
            records.append({'shot':shot,'cloud':cloud.get_name(),'head_socket':'Head_M'})
        assert unreal.EditorAssetLibrary.save_loaded_asset(seq)
    out=Path(unreal.Paths.project_dir())/'Saved/Audit/Closeout_20261018/cloud_head_anchor.json'
    out.write_text(json.dumps({'world':world.get_path_name(),'records':records,'live_gate':'pending'},indent=2))
    unreal.LevelSequenceEditorBlueprintLibrary.close_level_sequence()
    seq=unreal.load_asset('/Game/Sequences/Film304Closeout_20261018/LS_Closeout_David48f_v01')
    unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(seq)
    unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(20)
    print('HEAD_ANCHORS_AUTHORED',len(records))

if __name__=='__main__':main()
