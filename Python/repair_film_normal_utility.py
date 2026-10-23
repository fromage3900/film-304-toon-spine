"""Deduplicate only the film-owned normal utility, then rebuild its three calls.

The migrated function has ten appended copies of its graph/input names. A function
asset reassignment can therefore select a different unbound copy. Preserve one
complete output subtree and reconnect all inputs explicitly by their semantic role.
"""
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()); OUT=ROOT/'Saved/Audit/EveningExecution_20261017'
MAT='/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v05'
FN='/Game/Materials/Functions/Film304/MF_Film304_NormalAdjust'
ME=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary

def main():
    if unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering(): raise RuntimeError('Render active')
    graph=json.loads((OUT/'normal_adjust_function_graph.json').read_text())
    parents={}
    for edge in graph['connections']: parents.setdefault(edge['to'],[]).append(edge['from'])
    keep=set(); todo=[graph['outputs'][0]['id']]
    while todo:
        node=todo.pop()
        if node in keep: continue
        keep.add(node); todo.extend(parents.get(node,[]))
    fn=unreal.load_asset(FN); before=ME.get_material_function_expressions(fn)
    retained_names=[str(n.get_editor_property('input_name')) for n in before
        if isinstance(n,unreal.MaterialExpressionFunctionInput) and n.get_name() in keep]
    assert sorted(retained_names)==sorted(['Normal','NormalStrength','NormalPower','LayerNormalStrength'])
    for node in before:
        if node.get_name() not in keep: ME.delete_material_expression_in_function(fn,node)
    ME.update_material_function(fn); assert EAL.save_loaded_asset(fn,only_if_is_dirty=False)
    mat=unreal.load_asset(MAT); nodes={n.get_name():n for n in ME.get_material_expressions(mat)}
    source=json.loads((OUT/'universal_source_graph.json').read_text())
    plan=json.loads((OUT/'universal_trim_operations.json').read_text())
    rebuilt=[]
    for name in ['MaterialExpressionMaterialFunctionCall_32','MaterialExpressionMaterialFunctionCall_33','MaterialExpressionMaterialFunctionCall_34']:
        old=nodes[name]
        new=ME.create_material_expression(mat,unreal.MaterialExpressionMaterialFunctionCall,-1000,2000+len(rebuilt)*250)
        new.set_editor_property('material_function',fn)
        for edge in plan['connections']:
            if edge['to']!=name: continue
            target=edge['to_pin'].split(' (')[0]
            assert ME.connect_material_expressions(nodes[edge['from']],'' if edge['from_pin']=='None' else edge['from_pin'],new,target)
        for edge in plan['connections']:
            if edge['from']!=name: continue
            target=edge['to_pin'].split(' (')[0]
            if target=='None': target=''
            assert ME.connect_material_expressions(new,edge['from_pin'],nodes[edge['to']],target)
        ME.delete_material_expression(mat,old); rebuilt.append({'old':name,'new':new.get_name()})
    ME.recompile_material(mat); assert EAL.save_loaded_asset(mat,only_if_is_dirty=False)
    report={'function':FN,'before':len(before),'after':len(ME.get_material_function_expressions(fn)),
            'rebuilt_calls':rebuilt,'proof':'explicit utility repair; compile stats pending'}
    (OUT/'normal_utility_repair.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))

if __name__=='__main__':main()
