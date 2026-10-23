"""Apply existing verified ceiling assets to the owner's actual Office level."""
import json
from pathlib import Path
import unreal

def main():
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name()=='/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office.L_Film_Office'
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    by={a.get_actor_label():a for a in actors.get_all_level_actors()}
    before=[]
    panelmat=unreal.load_asset('/Game/Materials/Instances/Film304/Scene/Closeout20261018/MI_Film_TrofferDiffuser_Steady_v01')
    assert panelmat
    for i in range(1,7):
        for suffix,z in [('Panel',333.2),('Housing',335.7),('Light',331.5)]:
            actor=by[f'Film_Troffer_{i}_{suffix}']
            before.append({'actor':actor.get_actor_label(),'transform':str(actor.get_actor_transform())})
            position=actor.get_actor_location()
            actor.modify()
            actor.set_actor_location(unreal.Vector(position.x,position.y,z),False,False)
            actor.set_actor_rotation(unreal.Rotator(pitch=-90 if suffix=='Light' else 0,
                                                    yaw=65 if suffix=='Light' else -25,roll=0),False)
            if suffix=='Panel':actor.static_mesh_component.set_material(0,panelmat)
            if suffix=='Light':
                c=actor.get_component_by_class(unreal.RectLightComponent)
                c.set_mobility(unreal.ComponentMobility.MOVABLE)
                c.set_source_width(110);c.set_source_height(50)
                assert actor.get_actor_forward_vector().z<-.999
    placed=[]
    for label,part in [('Film_Closeout_Ceiling_Concrete','Tiles'),('Film_Closeout_Ceiling_Metal','Metal')]:
        mesh=unreal.load_asset('/Game/Meshes/Architecture/Closeout20261018/SM_Houdini_Office_Ceiling_'+part+'_Converged_v03')
        assert mesh
        actor=by.get(label)
        if actor is None:actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,0))
        actor.set_actor_label(label);actor.set_folder_path('Film304/Office/CeilingHVAC')
        actor.static_mesh_component.set_static_mesh(mesh)
        actor.set_actor_transform(unreal.Transform(),False,False)
        assert all(actor.static_mesh_component.get_material(i) for i in range(actor.static_mesh_component.get_num_materials()))
        placed.append({'actor':label,'mesh':mesh.get_path_name(),'bounds':str(actor.get_actor_bounds(False))})
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report={'world':world.get_path_name(),'fixture_count':6,'fixture_before':before,'ceiling':placed,
            'new_levels_created':0,'shared_material_graphs_edited':False,'saved_actual_office':True}
    (Path(unreal.Paths.project_dir())/'Saved/Audit/Closeout_20261018/main_office_ceiling_applied.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))

if __name__=='__main__':main()
