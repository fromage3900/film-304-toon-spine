import json
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[1]
builder = ROOT / "Python" / "build_dana_refined_uds.py"
source = builder.read_text(encoding="utf-8")
replacements = [
    ("'EyeWhite': {'RampStrength': .25, 'InkIntensity': .015, 'RimStrength': .0},",
     "'EyeWhite': {'RampStrength': .08, 'InkIntensity': .004, 'DryRoughness': .48, 'RimStrength': .0, 'BaseTint': (.82,.79,.73,1), 'AccentTint': (.96,.93,.86,1)},"),
    ("'Iris': {'RampStrength': .3, 'InkIntensity': .025, 'RimStrength': .0},",
     "'Iris': {'RampStrength': .10, 'InkIntensity': .006, 'DryRoughness': .30, 'RimStrength': .0, 'BaseTint': (.24,.095,.04,1), 'AccentTint': (.55,.25,.08,1)},"),
    ("'EyeInterior': {'RimStrength': .0},",
     "'EyeInterior': {'RampStrength': 0., 'InkIntensity': 0., 'DryRoughness': .48, 'RimStrength': .0, 'BaseTint': (.012,.008,.012,1), 'AccentTint': (.012,.008,.012,1)},"),
    ("unreal.LinearColor(.88,.93,.98,1)", "unreal.LinearColor(.94,.97,1.,1)"),
    ("'Coverage', 120, .09,", "'Coverage', 120, .16,"),
    ("'Roughness', 240, .10,", "'Roughness', 240, .06,"),
    ("'Specular', 360, .35,", "'Specular', 360, .45,"),
    ("'Coverage', .09)", "'Coverage', .16)"),
    ("'Roughness', .10)", "'Roughness', .06)"),
    ("'Specular', .35)", "'Specular', .45)"),
]
counts = [source.count(old) for old, new in replacements]
if counts != [1,1,1,2,1,1,1,1,1,1]:
    raise RuntimeError("Builder did not match expected eye tuning lines: " + repr(counts))
for old, new in replacements:
    source = source.replace(old, new)
builder.write_text(source, encoding="utf-8")

mi_settings = {
    "MI_DanaFilm_EyeWhite": {
        "scalar": {"RampStrength": .08, "InkIntensity": .004, "DryRoughness": .48},
        "vector": {"BaseTint": (.82,.79,.73,1), "AccentTint": (.96,.93,.86,1)},
    },
    "MI_DanaFilm_Iris": {
        "scalar": {"RampStrength": .10, "InkIntensity": .006, "DryRoughness": .30},
        "vector": {"BaseTint": (.24,.095,.04,1), "AccentTint": (.55,.25,.08,1)},
    },
    "MI_DanaFilm_EyeInterior": {
        "scalar": {"RampStrength": 0., "InkIntensity": 0., "DryRoughness": .48},
        "vector": {"BaseTint": (.012,.008,.012,1), "AccentTint": (.012,.008,.012,1)},
    },
    "MI_DanaFilm_Cornea": {
        "scalar": {"Coverage": .16, "Roughness": .06, "Specular": .45},
        "vector": {"CorneaTint": (.94,.97,1.,1)},
    },
}
me = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
rows = []
for name, groups in mi_settings.items():
    path = "/Game/Materials/Instances/DanaFilm/" + name
    mi = unreal.load_asset(path)
    if mi is None:
        raise RuntimeError("Missing eye material instance " + path)
    for key, value in groups["scalar"].items():
        me.set_material_instance_scalar_parameter_value(mi, key, value)
    for key, value in groups["vector"].items():
        me.set_material_instance_vector_parameter_value(mi, key, unreal.LinearColor(*value))
    me.update_material_instance(mi)
    if not eal.save_loaded_asset(mi, only_if_is_dirty=False):
        raise RuntimeError("Could not save " + path)
    rows.append({"asset": path, "scalars": groups["scalar"], "vectors": groups["vector"]})
report = {"result":"saved", "changes":rows, "reason":"Reduce face shader grading on eye surfaces; brighten sclera/iris separation and strengthen clear cornea highlight."}
out = ROOT / "Saved" / "Audit" / "dana_eye_material_fix.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("[DanaEyeFix] " + json.dumps(report))
