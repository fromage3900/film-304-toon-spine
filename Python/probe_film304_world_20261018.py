"""Report the live world and a few actor labels. Read-only."""
import json

import unreal

world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.EditorLevelLibrary.get_all_level_actors()
labels = []
for a in actors[:80]:
    try:
        labels.append(a.get_actor_label())
    except Exception:
        pass
print('WORLD ' + (world.get_path_name() if world else 'NONE'))
print('ACTORS %d' % len(actors))
print('LABELS ' + json.dumps(labels))
for p in ('/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office',
          '/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office_Dusk_20261018',
          '/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office_Dusk_20261018_v02',
          '/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_HeroTonight_20261018'):
    print('EXISTS %s %s' % (p, unreal.EditorAssetLibrary.does_asset_exist(p)))
