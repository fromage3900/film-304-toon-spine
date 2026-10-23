"""Update named Office cast only; no map save, layout, lighting or camera edits."""
import json
from pathlib import Path
import unreal

OUT=Path(unreal.Paths.project_dir())/'Saved/Audit/EveningExecution_20261017'
OFFICE='/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office.L_Film_Office'

def vec(v):return [v.x,v.y,v.z]
def snapshot(actor):
    c=actor.get_component_by_class(unreal.SkeletalMeshComponent)
    origin,extent=actor.get_actor_bounds(False)
    return {'actor':actor.get_actor_label(),'location':vec(actor.get_actor_location()),
        'rotation':str(actor.get_actor_rotation()),'scale':vec(actor.get_actor_scale3d()),
        'mesh':c.get_editor_property('skeletal_mesh_asset').get_path_name(),
        'materials':[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())],
        'animation_data':str(c.get_editor_property('animation_data')),
        'height_cm':2*extent.z,'bottom_z':origin.z-extent.z}

def main():
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name()==OFFICE,'Office only; never switch maps'
    assert not unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering()
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    targets={c:next(a for a in actors if a.get_actor_label()=='Film_Cast_'+c) for c in ['David','Sam']}
    before={c:snapshot(a) for c,a in targets.items()}
    receipt=OUT/'office_cast_apply_david_sam.json'
    if receipt.exists():raise RuntimeError('Application already recorded; inspect current actor state before reapplying')
    report={'world':OFFICE,'before':before,'after':{},'map_saved':False,
        'scale_policy':'170cm / Dana native height; preserves source human proportions, provisional pending owner view',
        'position_policy':'preserve XY and yaw; correct obsolete upside-down import pitch/roll; ground bounds to z=0'}
    # Preserve the pre-change actor state even if a later editor operation fails.
    (OUT/'office_cast_before_david_sam.json').write_text(json.dumps(report,indent=2))
    scale=170.0/76.92473535053432
    with unreal.ScopedEditorTransaction('Film304 repaired David and Sam held lineup'):
        for character,actor in targets.items():
            actor.modify();c=actor.get_component_by_class(unreal.SkeletalMeshComponent);c.modify()
            base='/Game/Staging/Film304Repaired_20261017/'+character
            mesh=unreal.load_asset(base+'/SK_'+character+'_Film304_v01')
            animation=unreal.load_asset(base+'/Poses/AS_'+character+'_HeldPose_v02')
            assert mesh and animation
            c.set_skeletal_mesh_asset(mesh)
            c.set_editor_property('override_materials',[])
            c.override_animation_data(animation,True,False,0.0,1.0)
            c.set_update_animation_in_editor(True)
            c.play_animation(animation,True)
            c.set_position(0.0,False)
            rotation=actor.get_actor_rotation()
            actor.set_actor_rotation(unreal.Rotator(pitch=0,yaw=rotation.yaw,roll=0),False)
            actor.set_actor_scale3d(unreal.Vector(scale,scale,scale))
            origin,extent=actor.get_actor_bounds(False)
            location=actor.get_actor_location();location.z-=origin.z-extent.z
            actor.set_actor_location(location,False,False)
            report['after'][character]=snapshot(actor)
            assert report['after'][character]['location'][:2]==before[character]['location'][:2]
            assert len(report['after'][character]['materials']) in [11,12]
    receipt.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
