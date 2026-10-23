"""Read-only: which bone represents the seated pelvis? Print world Z per bone."""
import json
from pathlib import Path
import unreal

AP = unreal.AnimPoseExtensions
OUT = Path(unreal.Paths.project_dir()) / "Saved/Audit/Poses"
OUT.mkdir(parents=True, exist_ok=True)

anim = unreal.load_asset("/Game/Staging/Film304Repaired_20261017/Poses_Headless/AS_David_Seated")
mesh = unreal.load_asset("/Game/Staging/Film304Repaired_20261017/David/SK_David_Film304_v01")
opts = unreal.AnimPoseEvaluationOptions()
opts.set_editor_properties({"should_retarget": False, "extract_root_motion": False,
                            "optional_skeletal_mesh": mesh})
pose = AP.get_anim_pose_at_time(anim, 0.0, opts)
names = [str(n) for n in AP.get_bone_names(pose)]

rows = {}
for n in names:
    t = AP.get_bone_pose(pose, n, unreal.AnimPoseSpaces.WORLD).translation
    rows[n] = [round(t.x, 2), round(t.y, 2), round(t.z, 2)]

interesting = [n for n in names if any(k in n.lower() for k in
               ("root", "hip", "pelvis", "spine1", "spine2", "chest", "knee", "ankle", "toe"))]
out = {"bone_count": len(names),
       "selected": {n: rows[n] for n in interesting},
       "z_min": min(rows.items(), key=lambda kv: kv[1][2]),
       "z_max": max(rows.items(), key=lambda kv: kv[1][2])}
(OUT / "david_seated_bones.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))
