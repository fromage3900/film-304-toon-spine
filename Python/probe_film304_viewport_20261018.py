"""Baseline viewport capture from Film_Cam_OfficeMedium (read-only).

Stores the previous viewport camera transform so later passes can restore it.
"""
import json
from pathlib import Path

import unreal
import claireon

OUT = Path(unreal.Paths.project_dir()) / 'Saved/Audit/Film304_Finish_20261018'
OUT.mkdir(parents=True, exist_ok=True)

world = unreal.EditorLevelLibrary.get_editor_world()
print('WORLD ' + world.get_path_name())

loc, rot = unreal.EditorLevelLibrary.get_level_viewport_camera_info()
state = {'location': [round(v, 3) for v in loc.to_tuple()],
         'rotation': [round(v, 3) for v in rot.to_tuple()]}
(OUT / 'viewport_before.json').write_text(json.dumps(state, indent=2), encoding='utf-8')
print('VIEWPORT_BEFORE %s' % state)

cam = None
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        if a.get_actor_label() == 'Film_Cam_OfficeMedium':
            cam = a
            break
    except Exception:
        pass

if cam is None:
    print('CAMERA_MISSING Film_Cam_OfficeMedium')
else:
    cloc = cam.get_actor_location()
    crot = cam.get_actor_rotation()
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(cloc, crot)
    print('VIEWPORT_SET %s %s' % ([round(v, 2) for v in cloc.to_tuple()],
                                  [round(v, 2) for v in crot.to_tuple()]))

res = claireon.slate_screenshot(target='level_viewport', filename='dusk_baseline.png',
                                directory=str(OUT))
print('SHOT ' + json.dumps(res))
