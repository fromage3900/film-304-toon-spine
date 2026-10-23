"""Read-only recursive dependency audit of the film look shelf."""
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()); OUT=ROOT/'Saved/Audit/EveningExecution_20261017'
PARENT='/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v06'
LABELS=['Toon','Smooth','Watercolour','Gouache','Halftone','OrderedDither','NoiseDither']

def main():
    ar=unreal.AssetRegistryHelpers.get_asset_registry()
    options=unreal.AssetRegistryDependencyOptions(include_soft_package_references=True,
        include_hard_package_references=True,include_searchable_names=False,
        include_soft_management_references=False,include_hard_management_references=False)
    roots=[PARENT,'/Game/Materials/Masters/Film304/M_Film304_CorneaClear']+['/Game/Materials/Instances/Film304/MI_Film304_'+s for s in LABELS]
    todo=roots[:]; seen=set(); links={}
    while todo:
        path=todo.pop()
        if path in seen: continue
        seen.add(path)
        deps=[str(d) for d in ar.get_dependencies(path,options)]
        links[path]=deps; todo.extend(d for d in deps if d.startswith('/Game/') and d not in seen)
    denied=[p for p in seen if any(s in p for s in ['/Melodia/','/EnvSandbox/',
        '/ParagonSparrow/','/UltraDynamicSky/','/Textures/sbs_','Madoka','Nikki','Itto','MeshBlend'])]
    outside_allowlist=[p for p in seen if not any(p.startswith(s) for s in [
        '/Game/Materials/Masters/Film304/','/Game/Materials/Instances/Film304/',
        '/Game/Materials/Functions/Film304/','/Game/Materials/Textures/Film304/'])
        and p not in ['/Game/Materials/ToonProfiles/TP_DanaFilm_Clean','/Game/Materials/ToonProfiles/TP_DanaFilm_Eye']]
    report={'root_master':PARENT,'packages':sorted(seen),'links':links,
        'denied':denied,'outside_allowlist':outside_allowlist,
        'dependency_gate_passed':not denied and not outside_allowlist,
        'proof':'saved package dependencies only; source/editor/render/reopen validation separate'}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'film_delivery_closure.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='links'},indent=2))

if __name__=='__main__':main()
