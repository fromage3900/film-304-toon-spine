# UE Python: Audit stale Material Instances in L_Film_Office
import json
from pathlib import Path
import unreal

OUT = Path(unreal.Paths.project_dir()) / 'Saved/Audit/Film304_Finish_20261018'
OUT.mkdir(parents=True, exist_ok=True)

actors = unreal.EditorLevelLibrary.get_all_level_actors()

cast_labels = {'Film_Cast_David', 'Film_Cast_Sam', 'Film_Cast_Dana', 'Spider', 'SK_Spider', 'Film_Spider'}

results = []
stale = []
for a in actors:
    try:
        label = a.get_actor_label()
    except:
        continue
    comps = []
    try:
        comps.extend(unreal.EditorUtilityLibrary.get_components_of_class(a, unreal.SkeletalMeshComponent))
    except:
        pass
    try:
        comps.extend(unreal.EditorUtilityLibrary.get_components_of_class(a, unreal.StaticMeshComponent))
    except:
        pass
    for c in comps:
        try:
            mats = c.get_materials()
        except:
            mats = []
        for i, m in enumerate(mats):
            if not m:
                continue
            try:
                mpath = m.get_path_name()
            except:
                mpath = str(m)
            entry = {
                'actor': label,
                'component': c.get_name(),
                'slot': i,
                'mat_path': mpath
            }
            results.append(entry)
            mlow = mpath.lower()
            if 'onedriverigs' in mlow or 'one_drive_rigs' in mlow:
                stale.append({**entry, 'reason': 'references OneDriveRigs_* (stale override)'})
            if label in cast_labels and i == 0:
                if '/materials/instances/film304/' not in mlow:
                    stale.append({**entry, 'reason': 'cast slot 0 not under /Game/Materials/Instances/Film304/'})

(Path(OUT)/'material_instances_all.json').write_text(json.dumps(results, indent=2), 'utf-8')
(Path(OUT)/'material_instances_stale.json').write_text(json.dumps(stale, indent=2), 'utf-8')

print('ALL:', len(results))
print('STALE:', len(stale))
for s in stale:
    print('STALE', s)
