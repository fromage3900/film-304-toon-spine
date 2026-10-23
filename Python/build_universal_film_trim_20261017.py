"""Apply a measured surgical trim to a new Universal film candidate only."""
import hashlib
import json
import re
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
AUDIT=ROOT/'Saved/Audit/EveningExecution_20261017'
DEST='/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v01'
ME=unreal.MaterialEditingLibrary
EAL=unreal.EditorAssetLibrary

def main():
    if unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering():
        raise RuntimeError('Render active: candidate build deferred')
    source_file=AUDIT/'universal_source_graph.json'
    plan=json.loads((AUDIT/'universal_trim_operations.json').read_text())
    original=json.loads(source_file.read_text())
    assert hashlib.sha256(source_file.read_bytes()).hexdigest()==plan['source_graph_sha256']
    if EAL.does_asset_exist(DEST): raise RuntimeError('Existing candidate preserved')
    source=unreal.load_asset(plan['source'])
    source_nodes=ME.get_material_expressions(source)
    assert len(source_nodes)==plan['source_count'], 'Source changed; export again'
    if not EAL.duplicate_asset(plan['source'],DEST): raise RuntimeError('Duplicate failed')
    mat=unreal.load_asset(DEST)
    expressions={n.get_name():n for n in ME.get_material_expressions(mat)}
    assert set(expressions)=={n['id'] for n in original['nodes']+original['custom_hlsl_nodes']}
    for name,value in plan['constants'].items():
        node=ME.create_material_expression(mat,unreal.MaterialExpressionConstant,2500,1600+len(expressions))
        node.set_editor_property('r',value); node.set_editor_property('desc',name)
        expressions[name]=node
    previous={(e['to'],e['to_pin']):(e['from'],e['from_pin']) for e in original['connections']}
    def pin(name): return '' if name in ('None','') else re.sub(r' \([^)]*\)$','',name)
    changed=[]
    for edge in plan['connections']:
        old=previous.get((edge['to'],edge['to_pin']))
        if old==(edge['from'],edge['from_pin']): continue
        if not ME.connect_material_expressions(expressions[edge['from']],pin(edge['from_pin']),
                    expressions[edge['to']],pin(edge['to_pin'])):
            raise RuntimeError('Required rewire failed: '+str(edge))
        changed.append(edge)
    old_outputs={o['to_property']:(o['from'],o['from_pin']) for o in original['outputs']}
    for output in plan['outputs']:
        if old_outputs.get(output['to_property'])==(output['from'],output['from_pin']): continue
        prop=getattr(unreal.MaterialProperty,'MP_'+re.sub(r'(?<!^)(?=[A-Z])','_',output['to_property']).upper())
        if not ME.connect_material_property(expressions[output['from']],pin(output['from_pin']),prop):
            raise RuntimeError('Root output rewire failed')
    for name in plan['delete_ids']:
        ME.delete_material_expression(mat,expressions[name])
    current=ME.get_material_expressions(mat)
    private_calls=[]
    for node in current:
        if isinstance(node,unreal.MaterialExpressionMaterialFunctionCall):
            fn=node.get_editor_property('material_function')
            if any(x in fn.get_path_name() for x in ['Madoka','Itto','Nikki','SpaceParallax','DF_Contact','MeshBlend','Day_to_Night']):
                private_calls.append(fn.get_path_name())
    assert not private_calls, private_calls
    # Replace the private source toon profile with the existing clean film profile.
    profile=unreal.load_asset('/Game/Materials/ToonProfiles/TP_DanaFilm_Clean')
    assert profile
    for node in current:
        if isinstance(node,unreal.MaterialExpressionSubstrateToonBSDF):
            node.set_editor_property('toon_profile',profile)
    ME.recompile_material(mat)
    if not EAL.save_loaded_asset(mat,only_if_is_dirty=False): raise RuntimeError('Candidate save failed')
    report={'source':plan['source'],'candidate':DEST,'source_count':len(source_nodes),
        'candidate_count':len(current),'rewires':changed,'deleted_count':len(plan['delete_ids']),
        'private_functions_remaining':private_calls,'source_modified':False,
        'proof':'candidate authored and compile requested; compilation stats and visual comparison pending'}
    (AUDIT/'universal_trim_build.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='rewires'},indent=2))

if __name__=='__main__': main()
