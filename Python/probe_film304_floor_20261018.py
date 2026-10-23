"""Isolate the pink floor: flat tint vs texture vs palette ramp.

Creates three debug instances, assigns each to Film_Floor in turn and captures
one screenshot per step. Restores MI_Dusk_Floor at the end.
"""
import json
from pathlib import Path

import unreal
import claireon

ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / 'Saved/Audit/Film304_Finish_20261018'
DIR = '/Game/Materials/Instances/Film304/Scene/DuskDebug20261018'
ME = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL.make_directory(DIR)
PARENT = '/Game/Materials/Instances/Film304/Scene/MI_Film304_Floor'
TEX = '/Game/Materials/Textures'
report = {'steps': [], 'errors': []}


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexlin(h):
    h = h.lstrip('#')
    return unreal.LinearColor(srgb_to_linear(int(h[0:2], 16) / 255.0),
                              srgb_to_linear(int(h[2:4], 16) / 255.0),
                              srgb_to_linear(int(h[4:6], 16) / 255.0), 1.0)


def make(name, tint, low, mid, high, ramp_strength, texture_weight, with_height):
    path = DIR + '/' + name
    if EAL.does_asset_exist(path):
        mi = unreal.load_asset(path)
    else:
        mi = AT.create_asset(name, DIR, unreal.MaterialInstanceConstant,
                             unreal.MaterialInstanceConstantFactoryNew())
    ME.set_material_instance_parent(mi, unreal.load_asset(PARENT))
    for k, v in (('BaseTint', tint), ('RampLow', low), ('RampMid', mid), ('RampHigh', high),
                 ('PaletteRampLow', low), ('PaletteRampMid', mid), ('PaletteRampHigh', high)):
        ME.set_material_instance_vector_parameter_value(mi, k, hexlin(v))
    for k, v in (('PaletteRampStrength', ramp_strength), ('RampStrength', 0.85),
                 ('TextureWeight', texture_weight), ('UVScale', 6.0),
                 ('Roughness', 0.72), ('Metallic', 0.0),
                 ('FilmGradeSaturation', 1.0), ('FilmGradeContrast', 1.0),
                 ('FilmGradeShadowLift', 0.0)):
        ME.set_material_instance_scalar_parameter_value(mi, k, float(v))
    if texture_weight > 0:
        albedo = unreal.load_asset(TEX + '/Film304/PBRImport20261018/T_Film304_PBR_terrazzo_D')
        if albedo:
            ME.set_material_instance_texture_parameter_value(mi, 'Albedo', albedo)
    if with_height:
        h = unreal.load_asset(TEX + '/T_SDF_CarpetLoop')
        if h:
            ME.set_material_instance_texture_parameter_value(mi, 'HeightMap', h)
            ME.set_material_instance_static_switch_parameter_value(mi, 'bUseHeightToNormal', True)
    ME.update_material_instance(mi)
    EAL.save_loaded_asset(mi, only_if_is_dirty=False)
    return unreal.load_asset(path)


steps = [
    ('01_flat', make('MI_Dbg_Floor_Flat', '#7C7468', '#7C7468', '#7C7468', '#7C7468', 0.0, 0.0, False)),
    ('02_texture', make('MI_Dbg_Floor_Tex', '#7C7468', '#7C7468', '#7C7468', '#7C7468', 0.0, 0.30, True)),
    ('03_ramp', make('MI_Dbg_Floor_Ramp', '#7C7468', '#2F3B4A', '#7C7468', '#A89C88', 0.55, 0.0, False)),
]

by_label = {}
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        by_label[a.get_actor_label()] = a
    except Exception:
        pass
floor = by_label.get('Film_Floor')
cam = by_label.get('Film_Cam_OfficeMedium')
if floor is None or cam is None:
    report['errors'].append('Film_Floor or camera missing')
else:
    comp = floor.get_components_by_class(unreal.StaticMeshComponent)[0]
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        cam.get_actor_location(), cam.get_actor_rotation())
    for tag, mi in steps:
        comp.set_material(0, mi)
        res = claireon.slate_screenshot(target='level_viewport',
                                        filename='floor_%s.png' % tag,
                                        directory=str(OUT))
        report['steps'].append({'step': tag, 'instance': mi.get_path_name(), 'shot': res})
    comp.set_material(0, unreal.load_asset(
        '/Game/Materials/Instances/Film304/Scene/Dusk20261018/MI_Dusk_Floor'))

(OUT / 'floor_probe_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('FLOOR_PROBE ' + json.dumps([s['step'] for s in report['steps']]) + ' errors=' + json.dumps(report['errors']))
for s in report['steps']:
    print(s['step'] + ' -> ' + s['shot']['data']['file_path'])
