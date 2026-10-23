"""Bring one existing matching Sparrow mesh/action pair into Humber for blocking.

Runs in Melodia; native migration only, no source asset edits.
"""
import hashlib
import json
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Saved/Audit/UniversalFilm_20261016'
mesh_path = '/Game/ParagonSparrow/Characters/Heroes/Sparrow/Meshes/Sparrow'
clip_path = '/Game/ParagonSparrow/Characters/Heroes/Sparrow/Animations/Jog_Fwd'
mesh = unreal.load_asset(mesh_path)
clip = unreal.load_asset(clip_path)
if not mesh or not clip:
    raise RuntimeError('Existing Sparrow motion specimen is unavailable')
mesh_skeleton = mesh.get_editor_property('skeleton')
clip_skeleton = clip.get_editor_property('skeleton')
if mesh_skeleton != clip_skeleton or clip.get_play_length() < .5:
    raise RuntimeError('The existing mesh/clip pair does not match')
registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.wait_for_completion()
options = unreal.AssetRegistryDependencyOptions(
    include_soft_package_references=False, include_hard_package_references=True,
    include_searchable_names=False, include_soft_management_references=False,
    include_hard_management_references=False)
pending = [mesh_path, clip_path]
graph = {}
while pending:
    pkg = pending.pop()
    if pkg in graph:
        continue
    deps = sorted(str(x) for x in registry.get_dependencies(pkg, options))
    graph[pkg] = deps
    pending.extend(p for p in deps if p.startswith('/Game/') and p not in graph)
content = Path(unreal.Paths.project_content_dir()).resolve()
rows = []
for pkg in sorted(graph):
    file = content / (pkg[6:] + '.uasset')
    if not file.exists() or file.stat().st_size < 256:
        raise RuntimeError('Missing/unhydrated motion dependency: ' + pkg)
    target = ROOT / 'Content' / file.relative_to(content)
    if target.exists() and target.read_bytes() != file.read_bytes():
        raise RuntimeError('Preserve conflicting Humber asset: ' + pkg)
    rows.append({'package': pkg, 'bytes': file.stat().st_size})
total = sum(r['bytes'] for r in rows)
report = {'mesh': mesh_path, 'clip': clip_path, 'duration': clip.get_play_length(),
          'skeleton': mesh_skeleton.get_path_name(), 'files': rows, 'bytes': total,
          'purpose': 'explicit Sparrow motion stand-in, not Dana rig approval'}
(OUT / 'motion_source.json').write_text(json.dumps(report, indent=2))
if total > 1024 * 1024 * 1024:
    raise RuntimeError('Specimen exceeds bounded 1 GiB migration; inspect report')
migration = unreal.MigrationOptions()
migration.set_editor_property('ignore_dependencies', True)
migration.set_editor_property('prompt', False)
migration.set_editor_property('asset_conflict', unreal.AssetMigrationConflict.SKIP)
unreal.AssetToolsHelpers.get_asset_tools().migrate_packages(
    [unreal.Name(pkg) for pkg in graph], str(ROOT / 'Content'), migration)
missing = [r['package'] for r in rows
           if not (ROOT / 'Content' / (r['package'][6:] + '.uasset')).exists()]
report['result'] = 'migrated' if not missing else 'missing_dependencies'
report['missing'] = missing
legacy_rig = '/Game/ParagonSparrow/Characters/Heroes/Sparrow/Meshes/Orion_Proto_Retarget'
if missing == [legacy_rig]:
    report['result'] = 'migrated_with_unsupported_legacy_editor_rig_omitted'
    report['qualification'] = 'UE 5.8 cannot load the deprecated Rig class; mesh/skeleton/animation require target readback'
(OUT / 'motion_source.json').write_text(json.dumps(report, indent=2))
if missing and report['result'] == 'missing_dependencies':
    raise RuntimeError('Motion migration omitted dependencies: ' + str(missing))
print('FILM_MOTION_SOURCE_READY')
