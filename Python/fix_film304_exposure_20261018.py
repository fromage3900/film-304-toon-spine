"""Fix the Dusk grade exposure and re-capture evidence.

The first pass forced AEM_MANUAL with min=max=1.0, which crushed the frame.
This restores histogram auto-exposure at +1.3 EV while keeping the film
finish (bloom/vignette/grain/fringe) and re-saves the Dusk map.
"""
import json
from pathlib import Path

import unreal
import claireon

ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / 'Saved/Audit/Film304_Finish_20261018'
OUT.mkdir(parents=True, exist_ok=True)
report = {'applied': [], 'errors': [], 'shots': []}

ppv = None
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        if a.get_actor_label() == 'PPV_StorybookOutline':
            ppv = a
            break
    except Exception:
        pass

if ppv is None:
    report['errors'].append('PPV_StorybookOutline missing')
else:
    s = ppv.get_editor_property('settings')
    values = {
        'auto_exposure_method': ('override_auto_exposure_method',
                                 unreal.AutoExposureMethod.AEM_HISTOGRAM),
        'auto_exposure_bias': ('override_auto_exposure_bias', 1.3),
        'auto_exposure_min_brightness': ('override_auto_exposure_min_brightness', 0.5),
        'auto_exposure_max_brightness': ('override_auto_exposure_max_brightness', 4.0),
    }
    for key, (override_key, value) in values.items():
        try:
            s.set_editor_property(key, value)
            s.set_editor_property(override_key, True)
            report['applied'].append(key)
        except Exception as exc:
            report['errors'].append('%s: %s' % (key, str(exc)[:100]))
    ppv.set_editor_property('settings', s)

world = unreal.EditorLevelLibrary.get_editor_world()
DEST = '/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office_Dusk_20261018_v02'
report['map_saved'] = bool(unreal.EditorLoadingAndSavingUtils.save_map(world, DEST))

prev_loc, prev_rot = unreal.EditorLevelLibrary.get_level_viewport_camera_info()
by_label = {}
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        by_label[a.get_actor_label()] = a
    except Exception:
        pass

for label, fname in (('Film_Cam_OfficeMedium', 'dusk_medium_fixed.png'),
                     ('Film_Cam_OfficeWide', 'dusk_wide_fixed.png')):
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

(OUT / 'exposure_fix_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('EXPOSURE_FIX applied=%s saved=%s errors=%s'
      % (report['applied'], report.get('map_saved'), report['errors']))
print('SHOTS ' + json.dumps(report['shots']))
