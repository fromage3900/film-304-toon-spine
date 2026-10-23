"""Read-only action/pose readiness check for existing cast assets."""
import json
from pathlib import Path
import unreal

root = Path(__file__).resolve().parents[1]
out = root / 'Saved/Audit/UniversalFilm_20261016'
registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.wait_for_completion()
rows = []
for data in registry.get_assets_by_path('/Game', recursive=True):
    if str(data.asset_class_path.asset_name) != 'AnimSequence':
        continue
    path = str(data.package_name)
    clip = unreal.load_asset(path)
    skeleton = clip.get_editor_property('skeleton')
    row = {'asset': path, 'length_seconds': clip.get_play_length(),
           'skeleton': skeleton.get_path_name() if skeleton else None}
    try:
        row['sampled_keys'] = clip.get_number_of_sampled_keys()
    except Exception as error:
        row['sampled_keys_query'] = str(error)
    rows.append(row)
L = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
L.load_level('/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Studio')
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
subject = next(a for a in actors if a.get_actor_label().startswith('Film_Subject_'))
component = subject.get_component_by_class(unreal.SkeletalMeshComponent)
bones = {}
for bone in ['Head_M', 'faceHeadJoint', 'Root_M', 'Root', 'Chest_M']:
    if component.get_bone_index(bone) >= 0:
        vector = component.get_socket_location(bone)
        bones[bone] = [vector.x, vector.y, vector.z]
report = {'animations': rows, 'subject_bones_world_cm': bones,
          'bounds': str(subject.get_actor_bounds(False)),
          'action_ready_candidates': [r for r in rows if r['length_seconds'] >= .5]}
(out / 'action_inventory.json').write_text(json.dumps(report, indent=2))
print('FILM_ACTION_INVENTORY ' + json.dumps(report))
