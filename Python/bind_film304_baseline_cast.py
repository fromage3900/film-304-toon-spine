"""Apply film-owned Toon baseline to repaired staging meshes only."""
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()); OUT=ROOT/'Saved/Audit/EveningExecution_20261017'
ME=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary

def main():
    assert not unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering()
    previous=json.loads((OUT/'repaired_cast_bindings.json').read_text())
    parts=json.loads((OUT/'film_cast_part_instances.json').read_text())
    lookup={(r['character'],r['part']):r['instance'] for r in parts['instances']}
    report={'scene_modified':False,'characters':{}}
    for character in ['Dana','David','Sam']:
        version='v10e' if character=='Dana' else 'v01'
        path='/Game/Staging/Film304Repaired_20261017/'+character+'/SK_'+character+'_Film304_'+version
        mesh=unreal.load_asset(path);assert mesh
        source={r['slot']:r for r in previous['characters'][character]['slots']}
        slots=list(mesh.get_editor_property('materials'));rows=[]
        for slot in slots:
            name=str(slot.get_editor_property('material_slot_name')); old=source[name];part=old['part']
            target='/Game/Materials/Instances/Film304/Cast/'+character+'/MI_Film304_'+character+'_Skin_Toon' if part=='Skin' else lookup.get((character,part))
            if not target:
                assert part in ['Teeth','Mouth'],(character,part)
                folder='/Game/Materials/Instances/Film304/Cast/'+character
                instance_name='MI_Film304_'+character+'_'+part+'_Toon';target=folder+'/'+instance_name
                if not EAL.does_asset_exist(target):
                    material=EAL.duplicate_asset(old['material'].split('.')[0],target);assert material
                    ME.set_material_instance_parent(material,unreal.load_asset('/Game/Materials/Instances/Film304/MI_Film304_Toon'))
                    ME.set_material_instance_static_switch_parameter_value(material,'bFilmUseUDIM',False)
                    ME.set_material_instance_scalar_parameter_value(material,'TextureWeight',0)
                    ME.update_material_instance(material);assert EAL.save_loaded_asset(material,only_if_is_dirty=False)
            material=unreal.load_asset(target);assert material
            slot.set_editor_property('material_interface',material)
            rows.append({'slot':name,'part':part,'material':material.get_path_name(),'previous_material':old['material']})
        mesh.set_editor_property('materials',slots);assert EAL.save_loaded_asset(mesh,only_if_is_dirty=False)
        assert all(s.get_editor_property('material_interface').get_path_name()==r['material'] for s,r in zip(mesh.get_editor_property('materials'),rows))
        report['characters'][character]={'mesh':path,'slots':rows,'saved_binding_gate':True,'visual_gate':False}
    report['proof']='film-owned baseline mesh-default bindings only; actor overrides and visual approval remain open'
    (OUT/'film_baseline_cast_bindings.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'bound_sections':sum(len(r['slots']) for r in report['characters'].values()),'scene_modified':False}))

if __name__=='__main__':main()
