"""Import corrected ceiling variants into the preserved assembly map only."""
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
OUT=ROOT/'Saved/Audit/Closeout_20261018'
MAP='/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office_Assembly_20261018_v01'
ASSETS='/Game/Meshes/Architecture/Closeout20261018'

def main():
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name()==MAP+'.'+MAP.rsplit('/',1)[1], world.get_path_name()
    report=json.loads((OUT/'ceiling_native_convergence.json').read_text())
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    rows=[]
    for row in report['meshes']:
        name=row['source_stem']+'_Converged_v03'
        path=ASSETS+'/'+name
        assert not unreal.EditorAssetLibrary.does_asset_exist(path), path
        task=unreal.AssetImportTask();task.filename=row['fbx'];task.destination_path=ASSETS
        task.destination_name=name;task.automated=True;task.save=False;task.replace_existing=False
        options=unreal.FbxImportUI();options.import_mesh=True;options.import_materials=False
        options.import_textures=False;options.import_animations=False;options.import_as_skeletal=False
        options.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH
        options.static_mesh_import_data.combine_meshes=True
        options.static_mesh_import_data.convert_scene=True
        options.static_mesh_import_data.convert_scene_unit=False
        options.static_mesh_import_data.import_uniform_scale=1.0
        task.options=options
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        mesh=unreal.load_asset(path);assert isinstance(mesh,unreal.StaticMesh),task.imported_object_paths
        bounds=mesh.get_bounds()
        native_mid=(row['bounds_min_cm'][2]+row['bounds_max_cm'][2])*.5
        assert abs(bounds.origin.z-native_mid)<.1, str(bounds)
        assert bounds.box_extent.x>1400 and bounds.box_extent.y>1400 and bounds.box_extent.z<40, str(bounds)
        matpath=('/Game/Materials/Instances/Film304/Scene/Dusk20261018/MI_Dusk_Ceiling'
                 if row['material_class']=='Concrete' else
                 '/Game/Materials/Instances/Film304/Scene/Dusk20261018/MI_Dusk_Metal')
        material=unreal.load_asset(matpath);assert material,matpath
        for i in range(len(mesh.static_materials)):mesh.set_material(i,material)
        assert unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        label='Film_Closeout_Ceiling_'+row['material_class']
        actor=next((a for a in actors.get_all_level_actors() if a.get_actor_label()==label),None)
        if actor is None:actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,0))
        actor.set_actor_label(label);actor.set_folder_path('Film304/FinalAssembly/Ceiling')
        comp=actor.static_mesh_component;comp.set_static_mesh(mesh)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        # Room yaw is already baked in the source geometry. Do not rotate twice.
        actor.set_actor_rotation(unreal.Rotator(0,0,0),False)
        actor.set_actor_scale3d(unreal.Vector(1,1,1))
        rows.append({'actor':label,'asset':mesh.get_path_name(),'material':matpath,
            'bounds_origin_cm':[bounds.origin.x,bounds.origin.y,bounds.origin.z],
            'bounds_extent_cm':[bounds.box_extent.x,bounds.box_extent.y,bounds.box_extent.z],
            'sections':mesh.get_num_sections(0)})
    report['unreal_import_verified']=True;report['assembly']=rows
    report['working_map']=MAP
    (OUT/'ceiling_native_convergence.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'assembly':rows,'actor_count':len(actors.get_all_level_actors()),'map_saved':False}))

if __name__=='__main__':main()
