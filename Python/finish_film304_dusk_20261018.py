"""Finish the Dusk pass: replace test instances, neutralise ramp tint, tone lights.

The floor was left on MI_DuskTest_Floor, whose inherited toon ramp stops are
pink (0.85, 0.40, 0.62). This script:
  * rewrites every MI_Dusk_* instance so RampLow/Mid/High == BaseTint (value
    bands only, no hue from the shared shader defaults) and PaletteRamp is off;
  * repoints every remaining original / test / WorldGrid slot to MI_Dusk_*;
  * softens the warm key and practicals;
  * captures evidence BEFORE saving, then saves a new _v04 map.
"""
import json
from pathlib import Path

import unreal
import claireon

ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / 'Saved/Audit/Film304_Finish_20261018'
ME = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary

DUSK_DIR = '/Game/Materials/Instances/Film304/Scene/Dusk20261018'
report = {'instances': [], 'repointed': 0, 'errors': [], 'lights': [], 'shots': []}

world = unreal.EditorLevelLibrary.get_editor_world()
path = world.get_path_name() if world else 'NONE'
print('START_WORLD ' + path)
if not path.endswith('L_Film_Office.L_Film_Office'):
    raise RuntimeError('Refusing to build: live world is ' + path)

SURFACES = ['Wall', 'WarmWall', 'Floor', 'Desk', 'Ceiling', 'Glazing', 'Metal', 'Plastic',
            'Ceramic', 'Paper', 'LampShade', 'Frame', 'Plant', 'Chair', 'Breakroom',
            'Whiteboard', 'Monitor', 'Blinds']

# Tone-down overrides applied on top of the built instances.
TINT_OVERRIDE = {
    'WarmWall': '#8A5A48',
    'Desk': '#937450',
    'LampShade': '#D9B27A',
    'Wall': '#75604F',
    'Floor': '#6A6258',
}

for s in SURFACES:
    mi = unreal.load_asset(DUSK_DIR + '/MI_Dusk_' + s)
    if mi is None:
        report['errors'].append('missing MI_Dusk_' + s)
        continue
    tint = None
    if s in TINT_OVERRIDE:
        h = TINT_OVERRIDE[s].lstrip('#')
        def lin(c):
            c = int(c, 16) / 255.0
            return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
        tint = unreal.LinearColor(lin(h[0:2]), lin(h[2:4]), lin(h[4:6]), 1.0)
        ME.set_material_instance_vector_parameter_value(mi, 'BaseTint', tint)
    else:
        tint = ME.get_material_instance_vector_parameter_value(mi, 'BaseTint')
    for p in ('RampLow', 'RampMid', 'RampHigh',
              'PaletteRampLow', 'PaletteRampMid', 'PaletteRampHigh'):
        ME.set_material_instance_vector_parameter_value(mi, p, tint)
    ME.set_material_instance_scalar_parameter_value(mi, 'RampStrength', 0.60)
    ME.set_material_instance_scalar_parameter_value(mi, 'RampContrast', 1.0)
    ME.set_material_instance_scalar_parameter_value(mi, 'PaletteRampStrength', 0.0)
    ME.set_material_instance_scalar_parameter_value(mi, 'PaletteRampDriver', 0.0)
    ME.update_material_instance(mi)
    EAL.save_loaded_asset(mi, only_if_is_dirty=False)
    report['instances'].append({'surface': s, 'instance': mi.get_path_name()})


DUSK = {s: unreal.load_asset(DUSK_DIR + '/MI_Dusk_' + s) for s in SURFACES}

# Exact actor fixes first (these are the shots that matter), then a material map.
ACTOR_FIX = {
    'Film_Floor': 'Floor',
    'Film_BackWall': 'Wall', 'Film_BackWall2': 'Wall', 'Film_SouthWall': 'Wall',
    'Film_Wall_Seam_Infill': 'Wall', 'Film_Wall_Seam_Infill2': 'Wall',
    'Film_Wall_Header_Full': 'Wall', 'Film_Wall_Header_Full2': 'Wall',
    'Film_Breakroom_UpperHeader': 'Wall', 'Film_NorthEast_UpperHeader': 'Wall',
    'Film_WarmWallPanel': 'WarmWall', 'Film_WarmWallPanel2': 'WarmWall',
    'Film_Wall_Right': 'WarmWall', 'Film_Wall_Right2': 'WarmWall',
    'Film_ExistingOfficeDesk': 'Desk', 'Film_DeskReturn': 'Desk',
    'SM_Glass_WindowBay_01': 'Glazing', 'SM_Glass_WindowBay_02': 'Glazing',
    'SM_Glass_WindowBay_03': 'Glazing', 'SM_Glass_WindowBay_2': 'Glazing',
    'SM_Glass_WindowBay_3': 'Glazing', 'SM_Glass_WindowBay_4': 'Glazing',
    'SM_Houdini_Ceiling_HVAC_Grid': 'Metal',
    'Film_Troffer_1_Housing': 'Metal', 'Film_Troffer_2_Housing': 'Metal',
    'Film_Troffer_3_Housing': 'Metal', 'Film_Troffer_4_Housing': 'Metal',
    'Film_Troffer_5_Housing': 'Metal', 'Film_Troffer_6_Housing': 'Metal',
}


def key_for(m, actor_label):
    p = m.get_path_name() if m else ''
    a = actor_label or ''
    if a in ACTOR_FIX:
        return ACTOR_FIX[a]
    if 'MI_DuskTest_Wall' in p or ('MI_Dbg_' in p and 'Wall' in p):
        return 'Wall'
    if 'MI_DuskTest_Floor' in p or 'MI_Dbg_Floor' in p:
        return 'Floor'
    if 'MI_DuskTest_Desk' in p:
        return 'Desk'
    if 'MI_Dusk_' in p:
        return None  # already final
    if 'WarmWall' in p:
        return 'WarmWall'
    if 'Wall' in p:
        return 'Wall'
    if 'Floor' in p:
        return 'Floor'
    if ('Desk' in p or 'OfficeDesk' in p or 'DeskDrawers' in p or 'BreakroomTable' in p):
        return 'Desk'
    if 'Frame' in p or 'WindowMullion' in a:
        return 'Frame'
    if 'PowderCoat' in p or 'Prop_Metal' in p:
        return 'Metal'
    if 'Ceramic' in p or 'CoffeeMug' in p or 'CoffeMug' in p:
        return 'Ceramic'
    if 'Whiteboard' in p:
        return 'Whiteboard'
    if 'Prop_Paper' in p:
        return 'Paper'
    if 'Lamp' in p:
        return 'LampShade'
    if 'Prop_Leaf' in p or 'Plant' in p or 'Succulent' in p or 'Cactus' in p:
        return 'Plant'
    if 'Prop_Screen' in p or 'ComputerMonitor' in p:
        return 'Monitor'
    if 'Plastic' in p or 'Keyboard' in p or 'Phone' in p or 'Watercooler' in p or 'VendingMachine' in p:
        return 'Plastic'
    if 'MI_Toon_Glass' in p or 'WindowBay' in a:
        return 'Glazing'
    if 'Polypropylene' in p or 'BreakRoomTogether' in p:
        return 'Breakroom'
    if 'Chair' in a or 'Chair' in p:
        return 'Chair'
    if p.endswith('WorldGridMaterial.WorldGridMaterial'):
        if 'Housing' in a:
            return 'Metal'
        if 'WindowMullion' in a:
            return 'Frame'
        return 'Plastic'
    return None


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
            key = key_for(m, label)
            if key and DUSK.get(key):
                comp.set_material(i, DUSK[key])
                report['repointed'] += 1

# ---------------- lights ----------------
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
            report['errors'].append('no light ' + label)
            return
        for k, v in props.items():
            try:
                comp.set_editor_property(k, v)
            except Exception as exc:
                report['errors'].append('%s.%s: %s' % (label, k, str(exc)[:70]))
        report['lights'].append(label)
        return
    report['errors'].append('missing light ' + label)


set_light('Light_Cinematic_SunBeam', intensity=10.0,
          light_color=as_color((255, 225, 195)), volumetric_scattering_intensity=2.5)
set_light('EST_Fill_E1', intensity=1.2, light_color=as_color((160, 182, 255)))
set_light('SpotLight', intensity=30.0, light_color=as_color((255, 225, 190)),
          outer_cone_angle=45.0)
set_light('Cast_RimKicker_Light', intensity=8.0, light_color=as_color((210, 235, 255)))
set_light('Light_David_DeskLamp', intensity=20.0, light_color=as_color((255, 214, 160)),
          attenuation_radius=600.0)
set_light('Light_Workstation_Row_Troffer', intensity=20.0,
          light_color=as_color((255, 248, 235)))


# ---------------- grade + exposure ----------------
def set_ppv(label, values):
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if a.get_actor_label() != label:
                continue
        except Exception:
            continue
        s = a.get_editor_property('settings')
        for key, (override_key, value) in values.items():
            try:
                s.set_editor_property(key, value)
                s.set_editor_property(override_key, True)
            except Exception as exc:
                report['errors'].append('%s.%s: %s' % (label, key, str(exc)[:70]))
        a.set_editor_property('settings', s)
        return
    report['errors'].append('missing ppv ' + label)


set_ppv('PPV_StorybookOutline', {
    'auto_exposure_method': ('override_auto_exposure_method', unreal.AutoExposureMethod.AEM_HISTOGRAM),
    'auto_exposure_bias': ('override_auto_exposure_bias', 1.0),
    'auto_exposure_min_brightness': ('override_auto_exposure_min_brightness', 0.5),
    'auto_exposure_max_brightness': ('override_auto_exposure_max_brightness', 4.0),
    'bloom_intensity': ('override_bloom_intensity', 0.30),
    'vignette_intensity': ('override_vignette_intensity', 0.28),
    'film_grain_intensity': ('override_film_grain_intensity', 0.05),
    'scene_fringe_intensity': ('override_scene_fringe_intensity', 0.08),
    'color_saturation': ('override_color_saturation', unreal.Vector4(1.02, 1.02, 1.02, 1.0)),
    'color_contrast': ('override_color_contrast', unreal.Vector4(1.02, 1.02, 1.02, 1.0)),
})

# Keep exactly one grade volume active.
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        label = a.get_actor_label()
    except Exception:
        continue
    if label in ('PPV_P2_WatercolourPaper', 'PPV_P3_RisoPrint', 'PPV_P4_CleanCinematic',
                 'EST_PPV_Ink'):
        try:
            if a.get_editor_property('enabled'):
                a.set_editor_property('enabled', False)
        except Exception:
            pass

# ---------------- evidence before save ----------------
prev_loc, prev_rot = unreal.EditorLevelLibrary.get_level_viewport_camera_info()
by_label = {}
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        by_label[a.get_actor_label()] = a
    except Exception:
        pass

for label, fname in (('Film_Cam_OfficeMedium', 'dusk_v5_medium.png'),
                     ('CineCam_Hero_WindowEstablishing', 'dusk_v5_window.png'),
                     ('CineCam_Hero_DeskLineup', 'dusk_v5_desks.png')):
    cam = by_label.get(label)
    if cam is None:
        report['errors'].append('camera missing ' + label)
        continue
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        cam.get_actor_location(), cam.get_actor_rotation())
    report['shots'].append({'camera': label,
                            'result': claireon.slate_screenshot(
                                target='level_viewport', filename=fname, directory=str(OUT))})
unreal.EditorLevelLibrary.set_level_viewport_camera_info(prev_loc, prev_rot)

# ---------------- save a new map ----------------
DEST = '/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office_Dusk_20261018_v05'
saved = bool(unreal.EditorLoadingAndSavingUtils.save_map(world, DEST))
report['map'] = {'path': DEST, 'saved': saved, 'source': path}

(OUT / 'dusk_finish_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('DUSK_FINISH instances=%d repointed=%d lights=%d shots=%d errors=%d saved=%s'
      % (len(report['instances']), report['repointed'], len(report['lights']),
         len(report['shots']), len(report['errors']), saved))
for e in report['errors']:
    print('  ERROR ' + e)
print('SHOTS ' + json.dumps([s['result']['data']['file_path'] for s in report['shots']]))
print('REPORT ' + str(OUT / 'dusk_finish_report.json'))
