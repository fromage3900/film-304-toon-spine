"""Probe Niagara user parameters + SDF textures, then build 3 test Dusk MIs.

Read-mostly: creates three test instances and assigns them to three actors so
the texture/ramp path can be verified in one viewport screenshot.
"""
import json
from pathlib import Path

import unreal
import claireon

ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / 'Saved/Audit/Film304_Finish_20261018'
OUT.mkdir(parents=True, exist_ok=True)
ME = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()

report = {'niagara': {}, 'textures': {}, 'tests': [], 'errors': []}

# ---- Niagara surface ----
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if isinstance(a, unreal.NiagaraActor):
        nc = a.get_editor_property('niagara_component')
        report['niagara']['actor'] = a.get_actor_label()
        report['niagara']['methods'] = sorted(
            m for m in dir(nc) if 'param' in m.lower() or 'variable' in m.lower())[:80]
        sys = nc.get_editor_property('asset')
        if sys:
            report['niagara']['system'] = sys.get_path_name()
            for attr in ('get_exposed_parameters', 'get_editor_property'):
                pass
            try:
                eps = sys.get_exposed_parameters()
                report['niagara']['exposed'] = str(eps)[:3000]
            except Exception as exc:
                report['niagara']['exposed_error'] = str(exc)[:200]
        break

# ---- texture availability ----
TEX = '/Game/Materials/Textures'
names = ['T_SDF_CarpetLoop', 'T_SDF_Woodgrain', 'T_SDF_Cracks', 'T_SDF_CeilingTile',
         'T_SDF_WeaveFine', 'T_SDF_Brushed', 'T_SDF_Dust' if False else 'T_SDF_FrostBands',
         'T_SDF_PaperGrain', 'T_SDF_Blinds', 'T_Gouache_PaperGrain']
for n in names:
    p = TEX + '/' + n
    t = unreal.load_asset(p)
    report['textures'][n] = t.get_path_name() if t else None

# ---- test instances ----
BASE = {
    'Wall': '/Game/Materials/Instances/Film304/Scene/MI_Film304_Wall',
    'Floor': '/Game/Materials/Instances/Film304/Scene/MI_Film304_Floor',
    'Desk': '/Game/Materials/Instances/Film304/Scene/MI_Film304_Desk',
}
FOLDER = '/Game/Materials/Instances/Film304/Scene/DuskTest20261018'
EAL.make_directory(FOLDER)


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexlin(h):
    h = h.lstrip('#')
    return unreal.LinearColor(srgb_to_linear(int(h[0:2], 16) / 255.0),
                              srgb_to_linear(int(h[2:4], 16) / 255.0),
                              srgb_to_linear(int(h[4:6], 16) / 255.0), 1.0)


TEST = {
    'Wall': {'tint': '#8A6A55', 'low': '#2F3B4A', 'mid': '#8A6A55', 'high': '#E8C79B',
             'texture': 'T_SDF_Cracks', 'weight': 0.28, 'uv': 2.0, 'rough': 0.8},
    'Floor': {'tint': '#7C7468', 'low': '#2F3B4A', 'mid': '#7C7468', 'high': '#CFC8B8',
              'texture': 'T_SDF_CarpetLoop', 'weight': 0.35, 'uv': 8.0, 'rough': 0.75},
    'Desk': {'tint': '#B08A5E', 'low': '#3A3340', 'mid': '#B08A5E', 'high': '#E8C79B',
             'texture': 'T_SDF_Woodgrain', 'weight': 0.30, 'uv': 3.0, 'rough': 0.55},
}

for key, cfg in TEST.items():
    name = 'MI_DuskTest_' + key
    path = FOLDER + '/' + name
    if EAL.does_asset_exist(path):
        mi = unreal.load_asset(path)
    else:
        mi = AT.create_asset(name, FOLDER, unreal.MaterialInstanceConstant,
                             unreal.MaterialInstanceConstantFactoryNew())
    ME.set_material_instance_parent(mi, unreal.load_asset(BASE[key]))
    ME.set_material_instance_vector_parameter_value(mi, 'BaseTint', hexlin(cfg['tint']))
    ME.set_material_instance_vector_parameter_value(mi, 'PaletteRampLow', hexlin(cfg['low']))
    ME.set_material_instance_vector_parameter_value(mi, 'PaletteRampMid', hexlin(cfg['mid']))
    ME.set_material_instance_vector_parameter_value(mi, 'PaletteRampHigh', hexlin(cfg['high']))
    ME.set_material_instance_scalar_parameter_value(mi, 'PaletteRampStrength', 0.85)
    ME.set_material_instance_scalar_parameter_value(mi, 'RampStrength', 0.85)
    ME.set_material_instance_scalar_parameter_value(mi, 'TextureWeight', cfg['weight'])
    ME.set_material_instance_scalar_parameter_value(mi, 'UVScale', cfg['uv'])
    ME.set_material_instance_scalar_parameter_value(mi, 'Roughness', cfg['rough'])
    tex = unreal.load_asset(TEX + '/' + cfg['texture'])
    if tex:
        ME.set_material_instance_texture_parameter_value(mi, 'Albedo', tex)
    ME.update_material_instance(mi)
    EAL.save_loaded_asset(mi, only_if_is_dirty=False)
    report['tests'].append({'key': key, 'instance': path, 'texture': cfg['texture'],
                            'weight': cfg['weight'], 'uv': cfg['uv']})


# ---- assign the three test instances ----
ASSIGN = {
    'Film_BackWall': 'MI_DuskTest_Wall',
    'Film_BackWall2': 'MI_DuskTest_Wall',
    'Film_Floor': 'MI_DuskTest_Floor',
    'Film_ExistingOfficeDesk': 'MI_DuskTest_Desk',
    'Film_DeskReturn': 'MI_DuskTest_Desk',
}
by_label = {}
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        by_label[a.get_actor_label()] = a
    except Exception:
        pass

for label, inst_name in ASSIGN.items():
    a = by_label.get(label)
    if a is None:
        report['errors'].append('actor missing: ' + label)
        continue
    mi = unreal.load_asset(FOLDER + '/' + inst_name)
    for comp in a.get_components_by_class(unreal.MeshComponent) or []:
        for i in range(len(comp.get_materials() or [])):
            comp.set_material(i, mi)
    report['tests'].append({'assigned': label, 'material': mi.get_path_name()})

# ---- screenshot from the office camera ----
cam = by_label.get('Film_Cam_OfficeMedium')
if cam:
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        cam.get_actor_location(), cam.get_actor_rotation())
res = claireon.slate_screenshot(target='level_viewport', filename='dusk_test_mats.png',
                                directory=str(OUT))
report['screenshot'] = res

(OUT / 'dusk_test_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('NIAGARA ' + json.dumps(report['niagara'])[:2500])
print('TEXTURES ' + json.dumps(report['textures']))
for t in report['tests']:
    print('TEST ' + json.dumps(t))
print('SHOT ' + json.dumps(res))
print('REPORT ' + str(OUT / 'dusk_test_report.json'))
