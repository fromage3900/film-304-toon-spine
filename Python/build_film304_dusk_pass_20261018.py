"""Film 304 - Dusk colour + texture pass (palette A: terracotta & teal).

Creates NEW child instances under .../Scene/Dusk20261018/, leaving every
existing instance untouched, then repoints the level's environment/prop slots
to the Dusk children. The v06 master is never edited.

Albedo uses real PBR diffuse maps imported from Saved/PBR (and the existing
Paragon wood diffuse for desks). The T_SDF_* office maps are RG distance
fields, so they are used ONLY as HeightMap (bUseHeightToNormal), never as
albedo - binding them as colour is what turned the test floor pink.

Run inside the live editor:
    powershell -File Tools/mcp_exec.ps1 -Path Python/build_film304_dusk_pass_20261018.py
"""
import json
import math
from pathlib import Path

import unreal
import claireon

ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / 'Saved/Audit/Film304_Finish_20261018'
OUT.mkdir(parents=True, exist_ok=True)

ME = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()

DUSK_DIR = '/Game/Materials/Instances/Film304/Scene/Dusk20261018'
PBR_DIR = '/Game/Materials/Textures/Film304/PBRImport20261018'
SDF = '/Game/Materials/Textures'
PBR_SRC = ROOT / 'Saved/PBR'

report = {'imported': {}, 'instances': [], 'repointed': [], 'errors': [],
          'lights': [], 'vfx': [], 'ppv': [], 'map': None}


def log(m):
    unreal.log('[Dusk2026] ' + str(m))
    print(m)


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexlin(h):
    h = h.lstrip('#')
    return unreal.LinearColor(srgb_to_linear(int(h[0:2], 16) / 255.0),
                              srgb_to_linear(int(h[2:4], 16) / 255.0),
                              srgb_to_linear(int(h[4:6], 16) / 255.0), 1.0)


def ensure_dir(p):
    if not EAL.does_directory_exist(p):
        EAL.make_directory(p)


ensure_dir(DUSK_DIR)
ensure_dir(PBR_DIR)

START_WORLD = unreal.EditorLevelLibrary.get_editor_world()
START_PATH = START_WORLD.get_path_name() if START_WORLD else 'NONE'
print('START_WORLD ' + START_PATH)
if not START_PATH.endswith('L_Film_Office.L_Film_Office'):
    raise RuntimeError('Refusing to build: live world is %s, expected L_Film_Office' % START_PATH)


def import_diffuse(stem):
    """Import Saved/PBR/<stem>/<stem>_D.png as a film-owned sRGB diffuse."""
    name = 'T_Film304_PBR_' + stem + '_D'
    path = PBR_DIR + '/' + name
    if EAL.does_asset_exist(path):
        report['imported'][stem] = path
        return unreal.load_asset(path)
    src = PBR_SRC / stem / (stem + '_D.png')
    if not src.exists():
        report['errors'].append('missing source ' + str(src))
        return None
    task = unreal.AssetImportTask()
    task.set_editor_property('filename', str(src))
    task.set_editor_property('destination_path', PBR_DIR)
    task.set_editor_property('destination_name', name)
    task.set_editor_property('replace_existing', True)
    task.set_editor_property('automated', True)
    task.set_editor_property('save', True)
    AT.import_asset_tasks([task])
    tex = unreal.load_asset(path)
    if tex is None:
        report['errors'].append('import failed ' + stem)
        return None
    try:
        tex.set_editor_property('srgb', True)
        tex.set_editor_property('compression_settings',
                                unreal.TextureCompressionSettings.TC_DEFAULT)
        tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_WORLD)
        EAL.save_loaded_asset(tex, only_if_is_dirty=False)
    except Exception as exc:
        report['errors'].append('texture settings %s: %s' % (stem, str(exc)[:100]))
    report['imported'][stem] = path
    log('imported ' + path)
    return tex


PBR = {s: import_diffuse(s) for s in ('concrete', 'terrazzo', 'steel', 'glazing')}
WOOD = unreal.load_asset('/Game/ParagonSparrow/Characters/Global/MaterialLayers/Wood/T_Wood01_D')
log('wood texture: %s' % (WOOD.get_path_name() if WOOD else 'MISSING'))


# ---------------------------------------------------------------------------
# Palette A - Dusk Terracotta & Teal
# ---------------------------------------------------------------------------
PARENTS = {
    'Wall': '/Game/Materials/Instances/Film304/Scene/MI_Film304_Wall',
    'WarmWall': '/Game/Materials/Instances/Film304/Scene/MI_Film304_WarmWall',
    'Floor': '/Game/Materials/Instances/Film304/Scene/MI_Film304_Floor',
    'Desk': '/Game/Materials/Instances/Film304/Scene/MI_Film304_Desk',
    'Ceiling': '/Game/Materials/Instances/Film304/Scene/MI_Film304_Wall',
    'Glazing': '/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistGlazing',
    'Metal': '/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Metal',
    'Plastic': '/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Plastic',
    'Ceramic': '/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Ceramic',
    'Paper': '/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Paper',
    'LampShade': '/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_LampShade',
    'Frame': '/Game/Materials/Instances/Film304/Scene/MI_Film304_Frame',
    'Plant': '/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Leaf',
    'Chair': '/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Metal',
    'Breakroom': '/Game/Materials/Instances/Film304/Scene/MI_Film304_Env_SM_BreakRoomTogether_ZMJ_FilmStage',
    'Whiteboard': '/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Paper',
    'Monitor': '/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Screen',
    'Blinds': '/Game/Materials/Instances/Film304/Scene/MI_Film304_Frame',
}

SPEC = {
    'Wall':      dict(tint='#7E604C', low='#2F3B4A', mid='#7E604C', high='#C9A57A',
                      weight=0.28, uv=2.0, rough=0.80, metal=0.0, driver=0.45,
                      albedo='concrete', height='T_SDF_Cracks', hstr=0.8),
    'WarmWall':  dict(tint='#9E523C', low='#3A2E33', mid='#9E523C', high='#D98A5E',
                      weight=0.25, uv=2.0, rough=0.82, metal=0.0, driver=0.45,
                      albedo='concrete', height='T_SDF_Cracks', hstr=0.8),
    'Floor':     dict(tint='#6A6258', low='#2F3B4A', mid='#6A6258', high='#A89C88',
                      weight=0.28, uv=10.0, rough=0.72, metal=0.0, driver=0.40,
                      albedo='terrazzo', height='T_SDF_CarpetLoop', hstr=0.9),
    'Desk':      dict(tint='#A98153', low='#3A3340', mid='#A98153', high='#D9B27A',
                      weight=0.30, uv=2.0, rough=0.55, metal=0.0, driver=0.45,
                      albedo='wood', height='T_SDF_Woodgrain', hstr=0.7),
    'Ceiling':   dict(tint='#C4BCAA', low='#6A6A66', mid='#C4BCAA', high='#E8E1D0',
                      weight=0.20, uv=8.0, rough=0.90, metal=0.0, driver=0.30,
                      albedo='concrete', height='T_SDF_CeilingTile', hstr=0.8),
    'Glazing':   dict(tint='#2E6F6B', low='#12333A', mid='#2E6F6B', high='#7FC6C4',
                      weight=0.15, uv=2.0, rough=0.15, metal=0.2, driver=0.50,
                      albedo='glazing', height='T_SDF_FrostBands', hstr=0.5),
    'Metal':     dict(tint='#4C5157', low='#1E242A', mid='#4C5157', high='#8A939C',
                      weight=0.30, uv=3.0, rough=0.45, metal=0.6, driver=0.50,
                      albedo='steel', height='T_SDF_Brushed', hstr=0.5),
    'Plastic':   dict(tint='#4C5157', low='#22262B', mid='#4C5157', high='#9BA3A8',
                      weight=0.10, uv=3.0, rough=0.50, metal=0.0, driver=0.40,
                      albedo='steel', height=None, hstr=0.0),
    'Ceramic':   dict(tint='#B4553C', low='#3A2E33', mid='#B4553C', high='#E8A37A',
                      weight=0.00, uv=1.0, rough=0.25, metal=0.0, driver=0.45),
    'Paper':     dict(tint='#EDE6D6', low='#8A8270', mid='#EDE6D6', high='#FFFFFF',
                      weight=0.15, uv=2.0, rough=0.90, metal=0.0, driver=0.30,
                      albedo='concrete', height='T_SDF_PaperGrain', hstr=0.4),
    'LampShade': dict(tint='#E8C79B', low='#6A4F2A', mid='#E8C79B', high='#FFF0CC',
                      weight=0.00, uv=1.0, rough=0.80, metal=0.0, driver=0.45),
    'Frame':     dict(tint='#4C5157', low='#1E242A', mid='#4C5157', high='#8A939C',
                      weight=0.10, uv=3.0, rough=0.50, metal=0.4, driver=0.50,
                      albedo='steel', height=None, hstr=0.0),
    'Plant':     dict(tint='#4F6B4A', low='#1E2A22', mid='#4F6B4A', high='#8FAE7A',
                      weight=0.00, uv=1.0, rough=0.70, metal=0.0, driver=0.45),
    'Chair':     dict(tint='#34383D', low='#1A1E22', mid='#34383D', high='#6E757B',
                      weight=0.20, uv=4.0, rough=0.80, metal=0.0, driver=0.40,
                      albedo='steel', height='T_SDF_WeaveFine', hstr=0.8),
    'Breakroom': dict(tint='#B08A5E', low='#3A3340', mid='#B08A5E', high='#D9B27A',
                      weight=0.25, uv=2.0, rough=0.65, metal=0.0, driver=0.45,
                      albedo='wood', height='T_SDF_Woodgrain', hstr=0.7),
    'Whiteboard': dict(tint='#E8E6E0', low='#9AA0A0', mid='#E8E6E0', high='#FFFFFF',
                       weight=0.05, uv=2.0, rough=0.15, metal=0.0, driver=0.30,
                       albedo='concrete', height=None, hstr=0.0),
    'Monitor':   dict(tint='#22262B', low='#0E1114', mid='#22262B', high='#3A4046',
                      weight=0.00, uv=1.0, rough=0.30, metal=0.1, driver=0.40),
    'Blinds':    dict(tint='#C9C4B8', low='#5A5A55', mid='#C9C4B8', high='#EDE8DA',
                      weight=0.00, uv=4.0, rough=0.70, metal=0.0, driver=0.30,
                      height='T_SDF_Blinds', hstr=1.0),
}


def texture_for(key):
    if key == 'wood':
        return WOOD
    return PBR.get(key)


def build_instance(surface):
    cfg = SPEC[surface]
    name = 'MI_Dusk_' + surface
    path = DUSK_DIR + '/' + name
    if EAL.does_asset_exist(path):
        mi = unreal.load_asset(path)
    else:
        mi = AT.create_asset(name, DUSK_DIR, unreal.MaterialInstanceConstant,
                             unreal.MaterialInstanceConstantFactoryNew())
    parent = unreal.load_asset(PARENTS[surface])
    if parent is None:
        report['errors'].append('parent missing ' + PARENTS[surface])
        return None
    ME.set_material_instance_parent(mi, parent)

    # Keep the parent's proven toon ramp. The PaletteRamp path collapses the
    # whole surface to one stop when driven (measured on the floor probe), so
    # it stays off; colour is BaseTint + lighting, exactly the recipe the
    # existing film instances already use.
    for p in ('RampLow', 'RampMid', 'RampHigh'):
        try:
            ME.set_material_instance_vector_parameter_value(
                mi, p, ME.get_material_instance_vector_parameter_value(parent, p))
        except Exception:
            pass
    for p in ('RampStrength', 'RampContrast'):
        try:
            ME.set_material_instance_scalar_parameter_value(
                mi, p, ME.get_material_instance_scalar_parameter_value(parent, p))
        except Exception:
            pass

    tint = hexlin(cfg['tint'])
    for pname in ('BaseTint', 'PaletteRampLow', 'PaletteRampMid', 'PaletteRampHigh'):
        ME.set_material_instance_vector_parameter_value(mi, pname, tint)

    scalars = {
        'PaletteRampStrength': 0.0,
        'PaletteRampDriver': 0.0,
        'TextureWeight': cfg['weight'],
        'UVScale': cfg['uv'],
        'Roughness': cfg['rough'],
        'Metallic': cfg['metal'],
        'FilmGradeSaturation': 1.08,
        'FilmGradeContrast': 1.02,
        'FilmGradeShadowLift': 0.02,
        'HeightToNormalStrength': cfg.get('hstr', 0.0),
        'DetailStrength': 0.15,
    }
    for k, v in scalars.items():
        ME.set_material_instance_scalar_parameter_value(mi, k, float(v))

    if cfg.get('albedo'):
        tex = texture_for(cfg['albedo'])
        if tex:
            ME.set_material_instance_texture_parameter_value(mi, 'Albedo', tex)
    if cfg.get('height'):
        htex = unreal.load_asset(SDF + '/' + cfg['height'])
        if htex:
            ME.set_material_instance_texture_parameter_value(mi, 'HeightMap', htex)
            ME.set_material_instance_static_switch_parameter_value(
                mi, 'bUseHeightToNormal', True)

    ME.set_material_instance_static_switch_parameter_value(mi, 'bFilmUseUDIM', False)
    ME.set_material_instance_static_switch_parameter_value(mi, 'bFilmPrintActive', False)
    ME.update_material_instance(mi)
    EAL.save_loaded_asset(mi, only_if_is_dirty=False)
    rec = {'surface': surface, 'instance': path, 'parent': parent.get_path_name(),
           'albedo': cfg.get('albedo'), 'height': cfg.get('height')}
    report['instances'].append(rec)
    log('instance %s (albedo=%s height=%s)' % (path, cfg.get('albedo'), cfg.get('height')))
    return mi


DUSK = {s: build_instance(s) for s in SPEC}



# ---------------------------------------------------------------------------
# Repoint the level's slots to the Dusk children
# ---------------------------------------------------------------------------
def dusk_key_for(mat_path, actor_label):
    p = mat_path or ''
    a = actor_label or ''
    if 'MI_Film304_WarmWall' in p or 'MI_Film_WarmWall' in p:
        return 'WarmWall'
    if 'MI_Film304_Wall' in p or 'MI_Film_Wall' in p:
        return 'Wall'
    if 'MI_Film304_Floor' in p:
        return 'Floor'
    if ('MI_Film304_Desk' in p or 'MI_Film304_Env_SM_P_OfficeDesk' in p
            or 'OfficeDesk' in p or 'DeskDrawers' in p or 'BreakroomTable' in p):
        return 'Desk'
    if 'MI_Film304_Frame' in p or 'MI_Film304_Prop_Frame' in p or 'WindowMullion' in a:
        return 'Frame'
    if 'MI_Film304_Prop_Metal' in p or 'PowderCoat' in p:
        return 'Metal'
    if 'MI_Film304_Prop_Ceramic' in p or 'CoffeeMug' in p or 'CoffeMug' in p:
        return 'Ceramic'
    if 'MI_Film304_Prop_Paper' in p or 'Whiteboard' in p:
        return 'Whiteboard' if 'Whiteboard' in p else 'Paper'
    if 'MI_Film304_Prop_LampShade' in p or 'Lamp' in p:
        return 'LampShade'
    if 'MI_Film304_Prop_Leaf' in p or 'Plant' in p or 'Succulent' in p or 'Cactus' in p:
        return 'Plant'
    if 'MI_Film304_Prop_Screen' in p or 'ComputerMonitor' in p:
        return 'Monitor'
    if ('MI_Film304_Prop_Plastic' in p or 'Keyboard' in p or 'Phone' in p
            or 'Watercooler' in p or 'VendingMachine' in p):
        return 'Plastic'
    if 'MI_Toon_Glass' in p or 'WindowBay' in a:
        return 'Glazing'
    if 'Polypropylene' in p or 'BreakRoomTogether' in p:
        return 'Breakroom'
    if 'MI_Film304_Prop_Metal' in p:
        return 'Metal'
    if 'Chair' in a or 'Chair' in p:
        return 'Chair'
    if p.endswith('WorldGridMaterial.WorldGridMaterial'):
        if 'Housing' in a:
            return 'Metal'
        if 'WindowMullion' in a:
            return 'Frame'
    return None


counts = {}
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        label = actor.get_actor_label()
    except Exception:
        continue
    for comp in actor.get_components_by_class(unreal.MeshComponent) or []:
        try:
            mats = comp.get_materials() or []
        except Exception:
            continue
        for i, m in enumerate(mats):
            if m is None:
                continue
            key = dusk_key_for(m.get_path_name(), label)
            if key and DUSK.get(key):
                comp.set_material(i, DUSK[key])
                counts[key] = counts.get(key, 0) + 1
                report['repointed'].append({'actor': label, 'component': comp.get_name(),
                                            'slot': i, 'surface': key,
                                            'from': m.get_path_name(),
                                            'to': DUSK[key].get_path_name()})
log('repointed slots: ' + json.dumps(counts))


# ---------------------------------------------------------------------------
# Lighting: warm key, cool shadow, practicals back on
# ---------------------------------------------------------------------------
def as_color(rgb):
    return unreal.Color(r=int(rgb[0]), g=int(rgb[1]), b=int(rgb[2]), a=255)


def set_light(label, **props):
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if a.get_actor_label() != label:
                continue
        except Exception:
            continue
        comp = None
        for attr in ('light_component', 'directional_light_component', 'point_light_component',
                     'spot_light_component', 'rect_light_component'):
            try:
                comp = a.get_editor_property(attr)
                if comp:
                    break
            except Exception:
                pass
        if comp is None:
            report['errors'].append('no light component ' + label)
            return
        for k, v in props.items():
            try:
                comp.set_editor_property(k, v)
            except Exception as exc:
                report['errors'].append('%s.%s: %s' % (label, k, str(exc)[:80]))
        report['lights'].append({'label': label, 'set': list(props.keys())})
        return
    report['errors'].append('light missing ' + label)


set_light('Light_Cinematic_SunBeam', intensity=12.0, light_color=as_color((255, 214, 170)),
          volumetric_scattering_intensity=3.0)
set_light('EST_Fill_E1', intensity=1.2, light_color=as_color((150, 175, 255)))
set_light('SpotLight', intensity=80.0, light_color=as_color((255, 210, 160)),
          outer_cone_angle=45.0)
set_light('Cast_RimKicker_Light', intensity=8.0, light_color=as_color((210, 235, 255)))
set_light('Light_David_DeskLamp', intensity=60.0, light_color=as_color((255, 199, 122)),
          attenuation_radius=600.0)
set_light('Light_Workstation_Row_Troffer', intensity=25.0,
          light_color=as_color((255, 244, 226)))
set_light('Film_Troffer_6_Light', intensity=14.0)


# ---------------------------------------------------------------------------
# VFX: retire the orange UDS dust; soften the snore puffs
# ---------------------------------------------------------------------------
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        if a.get_actor_label() == 'VFX_DustMotes_WindowRays':
            a.set_actor_hidden_in_game(True)
            try:
                a.get_editor_property('niagara_component').set_visibility(False)
            except Exception:
                pass
            report['vfx'].append({'actor': 'VFX_DustMotes_WindowRays',
                                  'action': 'disabled (orange speckle defect)'})
    except Exception:
        pass

puff = unreal.load_asset('/Game/Materials/FilmIdle_20261017/M_DavidSnorePuff_v03_SoftFade')
if puff is None:
    puff = unreal.load_asset('/Game/Materials/Film304Idle_20261017/M_DavidSnorePuff_v03_SoftFade')
old_puff_names = ('M_DavidSnorePuff_v01',)
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    for comp in a.get_components_by_class(unreal.MeshComponent) or []:
        for i, m in enumerate(comp.get_materials() or []):
            if m and any(n in m.get_name() for n in old_puff_names) and puff:
                comp.set_material(i, puff)
                report['vfx'].append({'actor': a.get_actor_label(),
                                      'action': 'snore puff -> v03_SoftFade'})
log('vfx: ' + json.dumps(report['vfx']))


# ---------------------------------------------------------------------------
# Grade: the single enabled PPV gets fixed exposure + film finish
# ---------------------------------------------------------------------------
def set_ppv(label, values):
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if a.get_actor_label() != label:
                continue
        except Exception:
            continue
        s = a.get_editor_property('settings')
        applied = []
        for key, (override_key, value) in values.items():
            try:
                s.set_editor_property(key, value)
                s.set_editor_property(override_key, True)
                applied.append(key)
            except Exception as exc:
                report['errors'].append('%s.%s: %s' % (label, key, str(exc)[:80]))
        a.set_editor_property('settings', s)
        report['ppv'].append({'label': label, 'applied': applied})
        return
    report['errors'].append('ppv missing ' + label)


set_ppv('PPV_StorybookOutline', {
    'auto_exposure_method': ('override_auto_exposure_method', unreal.AutoExposureMethod.AEM_HISTOGRAM),
    'auto_exposure_bias': ('override_auto_exposure_bias', 1.3),
    'auto_exposure_min_brightness': ('override_auto_exposure_min_brightness', 0.5),
    'auto_exposure_max_brightness': ('override_auto_exposure_max_brightness', 4.0),
    'bloom_intensity': ('override_bloom_intensity', 0.35),
    'vignette_intensity': ('override_vignette_intensity', 0.28),
    'film_grain_intensity': ('override_film_grain_intensity', 0.05),
    'scene_fringe_intensity': ('override_scene_fringe_intensity', 0.10),
    'color_saturation': ('override_color_saturation', unreal.Vector4(1.06, 1.06, 1.06, 1.0)),
    'color_contrast': ('override_color_contrast', unreal.Vector4(1.03, 1.03, 1.03, 1.0)),
})


# ---------------------------------------------------------------------------
# Evidence is captured BEFORE saving: save_map can switch the editor world,
# and a concurrent level switch must not cost us the only visual proof.
# ---------------------------------------------------------------------------
prev_loc, prev_rot = unreal.EditorLevelLibrary.get_level_viewport_camera_info()
by_label = {}
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        by_label[a.get_actor_label()] = a
    except Exception:
        pass

shots = []
for label, fname in (('Film_Cam_OfficeMedium', 'dusk_office_medium.png'),
                     ('Film_Cam_OfficeWide', 'dusk_office_wide.png')):
    cam = by_label.get(label)
    if cam is None:
        report['errors'].append('camera missing ' + label)
        continue
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        cam.get_actor_location(), cam.get_actor_rotation())
    res = claireon.slate_screenshot(target='level_viewport', filename=fname, directory=str(OUT))
    shots.append({'camera': label, 'result': res})
unreal.EditorLevelLibrary.set_level_viewport_camera_info(prev_loc, prev_rot)
report['shots'] = shots

# ---------------------------------------------------------------------------
# Save a NEW level; L_Film_Office is never overwritten.
# ---------------------------------------------------------------------------
world = unreal.EditorLevelLibrary.get_editor_world()
DEST = '/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office_Dusk_20261018_v03'
saved = bool(unreal.EditorLoadingAndSavingUtils.save_map(world, DEST))
report['map'] = {'path': DEST, 'saved': saved, 'source': world.get_path_name()}
log('map saved=%s -> %s' % (saved, DEST))


(OUT / 'dusk_pass_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('DUSK_DONE instances=%d repointed=%d errors=%d saved=%s'
      % (len(report['instances']), len(report['repointed']), len(report['errors']), saved))
for e in report['errors']:
    print('  ERROR ' + e)
print('SHOTS ' + json.dumps(shots))
print('REPORT ' + str(OUT / 'dusk_pass_report.json'))

