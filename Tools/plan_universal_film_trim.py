"""Compute explicit neutral rewires and reachability from a live Universal export.

Never runs Unreal or edits the source. Each removed live branch has a replacement;
reachability is measured AFTER rewires, not inferred from dangling input nodes.
"""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'Saved/Audit/EveningExecution_20261017'

def main():
    source = BASE / 'universal_source_graph.json'
    graph = json.loads(source.read_text())
    nodes = {n['id']: n for n in graph['nodes']+graph['custom_hlsl_nodes']}
    original = list(graph['connections'])
    # Read the previous explicit content parameter inventory without executing it.
    tree = ast.parse((ROOT/'Python/trim_master_take2.py').read_text())
    drop = set()
    for stmt in tree.body:
        if isinstance(stmt,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DROP_PARAMS' for t in stmt.targets):
            drop=set(stmt.value.args[0].func.value.value.split())
    drop.update('DreamIntensity DreamRimStrength DreamCompositeBlend ShadowDreamStrength NikkiHeroGradeStrength NikkiHeroBlend NikkiHeroStrength CymaticAmplitude Cymatic_EmissiveScale Cymatic_IridescenceShift Cymatic_UVDistortion NoteScrollAmp'.split())
    removed_switches = set('bNikkiHero bMeshBlendActivator_Active bCelestial_Active bCelestialUsesDreamPalette bFairyDust_Active bWeather_Active bElemental_Active bDreamRim_Active bDFContactBlend_Active bGemstone_Active bSparkleAdvanced UseUDSTimeOfDay'.split())
    drop.update(removed_switches)
    substitutions = {}
    reasons = {}
    constants = {'FILM_ZERO':0.0,'FILM_ONE':1.0}
    def ref(node,pin='None'): return {'id':node,'pin':pin}
    def incoming(node,prefix):
        matches=[e for e in original if e['to']==node and e['to_pin'].startswith(prefix)]
        if len(matches)!=1: raise RuntimeError('Ambiguous required input: '+node+' '+prefix)
        e=matches[0]; return ref(e['from'],e['from_pin'])
    def replace(node,target,reason): substitutions[node]=target; reasons[node]=reason
    for name,n in nodes.items():
        p=n.get('props',{}); cls=n.get('class','Custom')
        if cls=='Constant': constants[name]=float(p.get('R',0))
        if cls=='StaticSwitchParameter' and p.get('ParameterName') in removed_switches:
            replace(name,incoming(name,'False'),'private switch resolved to false')
        elif cls=='ScalarParameter' and p.get('ParameterName') in drop:
            replace(name,ref('FILM_ZERO'),'private content parameter neutralized')
        elif cls=='CollectionParameter':
            replace(name,ref('FILM_ZERO'),'project MPC dependency removed')
        elif name=='MaterialExpressionCustom_30':
            replace(name,incoming(name,'BaseColor'),'private dream compositor bypassed')
    # Outputs are substituted separately because functions have different neutral
    # values per output. Expand outgoing links explicitly before deleting calls.
    output_replacements={}
    private_functions=[]
    for name,n in nodes.items():
        fn=n.get('props',{}).get('MaterialFunction','')
        if not any(s in fn for s in ['MF_Madoka.','MF_Itto.','MF_NikkiDreamGrade.',
                    'MF_SpaceParallax.','Day_to_Night_Color.','MF_DF_ContactBlend.','MF_MeshBlend_Activator']):
            continue
        private_functions.append(name)
        for e in original:
            if e['from']!=name: continue
            target=ref('FILM_ZERO')
            if 'MF_Itto.' in fn and e['from_pin']=='Color': target=incoming(name,'BaseColor ')
            elif 'MF_NikkiDreamGrade.' in fn and e['from_pin']=='Color': target=incoming(name,'BaseColorIn ')
            elif 'Day_to_Night_Color.' in fn: target=incoming(name,'Day ')
            output_replacements[(name,e['from_pin'])]=target
    def resolve(r):
        seen=set()
        while True:
            key=(r['id'],r['pin'])
            if key in seen: raise RuntimeError('Substitution cycle')
            seen.add(key)
            target=output_replacements.get(key,substitutions.get(r['id']))
            if target is None: return r
            r=target
    def edges():
        return [{**e,'from':resolve(ref(e['from'],e['from_pin']))['id'],
                  'from_pin':resolve(ref(e['from'],e['from_pin']))['pin']}
                 for e in original if e['to'] not in substitutions and e['to'] not in private_functions]
    # Exact neutral identities only. Never infer a default ScalarParameter is a
    # constant: artists must retain live control over all kept film features.
    for _ in range(len(nodes)):
        changed=False
        by_target={}
        for e in edges(): by_target.setdefault(e['to'],{})[e['to_pin']]=ref(e['from'],e['from_pin'])
        for name,inputs in by_target.items():
            if name in substitutions: continue
            cls=nodes[name].get('class'); p=nodes[name].get('props',{})
            a=inputs.get('A'); b=inputs.get('B'); alpha=inputs.get('Alpha')
            av=constants.get(a['id']) if a else float(p.get('ConstA',0))
            bv=constants.get(b['id']) if b else float(p.get('ConstB',0))
            target=None
            if cls=='Multiply':
                if av==0 or bv==0: target=ref('FILM_ZERO')
                elif av==1 and b: target=b
                elif bv==1 and a: target=a
            elif cls=='Add':
                if av==0 and b: target=b
                elif bv==0 and a: target=a
            elif cls=='Subtract' and bv==0 and a: target=a
            elif cls=='LinearInterpolate':
                value=constants.get(alpha['id']) if alpha else float(p.get('ConstAlpha',0.5))
                if value==0 and a: target=a
                elif value==1 and b: target=b
            if target:
                replace(name,target,'exact neutral arithmetic identity'); changed=True
        if not changed: break
    rewired=edges()
    outputs=[]
    for output in graph['outputs']:
        r=ref('FILM_ONE') if output['to_property']=='AmbientOcclusion' else resolve(ref(output['from'],output['from_pin']))
        outputs.append({**output,'from':r['id'],'from_pin':r['pin']})
    reachable=set(); stack=[o['from'] for o in outputs]
    parents={}
    for e in rewired: parents.setdefault(e['to'],[]).append(e['from'])
    while stack:
        node=stack.pop()
        if node in reachable: continue
        reachable.add(node); stack.extend(parents.get(node,[]))
    assert not set(private_functions)&reachable, 'Private call still live'
    result={'source':graph['asset_path'],'source_graph_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'source_count':len(nodes),'kept_ids':sorted(reachable & nodes.keys()),
        'delete_ids':sorted(nodes.keys()-reachable),'constants':{k:v for k,v in constants.items() if k.startswith('FILM_') and k in reachable},
        'connections':[e for e in rewired if e['to'] in reachable], 'outputs':outputs,
        'substitutions':{k:{'target':resolve(v),'reason':reasons[k]} for k,v in substitutions.items()},
        'removed_functions':[nodes[n]['props']['MaterialFunction'] for n in private_functions],
        'kept_functions':[n['props']['MaterialFunction'] for i,n in nodes.items() if i in reachable and n.get('class')=='MaterialFunctionCall'],
        'kept_parameters':sorted({n.get('props',{}).get('ParameterName') for i,n in nodes.items() if i in reachable and n.get('props',{}).get('ParameterName')}),
        'proof':'offline explicit-rewire plan; not compiled or visually verified'}
    target=BASE/'universal_trim_operations.json'; target.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'source_count':len(nodes),'kept':len(result['kept_ids']),
        'deleted':len(result['delete_ids']),'kept_functions':result['kept_functions'],
        'kept_parameters':result['kept_parameters'],'report':str(target)},indent=2))

if __name__=='__main__': main()
