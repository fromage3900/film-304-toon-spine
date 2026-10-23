"""Resolve the one path conflict INSIDE the isolated migrated project, then import.

Never run this against either production project. Does not rebuild the shader.
"""
import hashlib
import json
from pathlib import Path
import unreal

REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO / 'Saved/Audit/UniversalFilm_20261016'
DELIVERY = REPO / 'Saved/UniversalFilmDelivery_20261016'
project = Path(unreal.Paths.project_dir()).resolve()
if project != DELIVERY.resolve():
    raise RuntimeError('This script only runs in the isolated delivery project')

inventory = json.loads((AUDIT / 'source_inventory.json').read_text())
# Retain the exact already-present licensed sky helpers. Native migration can
# reserialize them even when their content is unchanged; preserve source bytes
# for these two unchanged dependencies before loading the isolated graph.
for entry in inventory['files']:
    if entry['package'].startswith('/Game/UltraDynamicSky/'):
        target = DELIVERY / 'Content' / (entry['package'][6:] + '.uasset')
        original = Path(entry['file'])
        existing = REPO / 'Content' / (entry['package'][6:] + '.uasset')
        original_bytes = original.read_bytes()
        if existing.read_bytes() != original_bytes:
            raise RuntimeError('Existing Humber sky helper diverged; preserve it')
        target.write_bytes(original_bytes)
E = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
assets = [unreal.load_asset(pkg) for pkg in inventory['roots']]
if any(a is None for a in assets):
    raise RuntimeError('A migrated root asset failed to load')
old = '/Game/Materials/Textures/T_SDF_Strokes'
new_dir = '/Game/EnvSandbox/Textures/UniversalFilm'
new = new_dir + '/T_SDF_Strokes'
if not E.does_asset_exist(new):
    texture = unreal.load_asset(old)
    if not texture:
        raise RuntimeError('Source stroke texture missing')
    if not tools.rename_assets([unreal.AssetRenameData(texture, new_dir, 'T_SDF_Strokes')]):
        raise RuntimeError('Scoped delivery texture rename failed')
    # Renamed asset and loaded source graph references only; no production writes.
    for pkg in inventory['graph']:
        if pkg == old or pkg.startswith('/Game/UltraDynamicSky/'):
            continue
        obj = unreal.load_asset(pkg)
        if not obj or not E.save_loaded_asset(obj, False):
            raise RuntimeError('Delivery save failed: ' + pkg)
    if not E.save_asset(new, False):
        raise RuntimeError('Delivery stroke texture save failed')

registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.scan_paths_synchronous(['/Game'], force_rescan=True)
opts = unreal.AssetRegistryDependencyOptions(
    include_soft_package_references=True, include_hard_package_references=True,
    include_searchable_names=False, include_soft_management_references=False,
    include_hard_management_references=False)
pending = list(inventory['roots'])
graph = {}
while pending:
    pkg = pending.pop()
    if pkg in graph:
        continue
    deps = sorted(str(d) for d in registry.get_dependencies(pkg, opts))
    graph[pkg] = deps
    pending.extend(d for d in deps if d.startswith('/Game/') and d not in graph)
if old in graph or any(old in deps for deps in graph.values()):
    raise RuntimeError('The isolated graph still refers to Humber conflicting texture')
master = unreal.load_asset(inventory['master'])
expressions = unreal.MaterialEditingLibrary.get_material_expressions(master)
calls = []
for node in expressions:
    if node.get_class().get_name() == 'MaterialExpressionMaterialFunctionCall':
        function = node.get_editor_property('material_function')
        calls.append(function.get_path_name() if function else None)
if len(expressions) != inventory['expression_count'] or calls != inventory['function_calls']:
    raise RuntimeError('Migrated graph lost expressions or function references')

rows = []
for pkg in sorted(graph):
    source = DELIVERY / 'Content' / (pkg[6:] + '.uasset')
    target = REPO / 'Content' / (pkg[6:] + '.uasset')
    if not source.exists():
        raise RuntimeError('Delivery dependency missing: ' + pkg)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    exists = target.exists()
    same = exists and hashlib.sha256(target.read_bytes()).hexdigest() == digest
    if exists and not same:
        raise RuntimeError('Refusing to overwrite existing Humber package: ' + pkg)
    rows.append({'package': pkg, 'sha256': digest, 'bytes': source.stat().st_size,
                 'preexisting_identical': same})
options = unreal.MigrationOptions()
options.set_editor_property('ignore_dependencies', True)
options.set_editor_property('prompt', False)
options.set_editor_property('asset_conflict', unreal.AssetMigrationConflict.SKIP)
tools.migrate_packages([unreal.Name(p) for p in graph], str(REPO / 'Content'), options)
for row in rows:
    target = REPO / 'Content' / (row['package'][6:] + '.uasset')
    if not target.exists():
        raise RuntimeError('Humber migration readback failed: ' + row['package'])
    row['humber_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    row['migration_bytes_match'] = row['humber_sha256'] == row['sha256']
report = {'result': 'migrated_and_graph_readback_passed', 'master': inventory['master'],
          'expression_count': len(expressions), 'function_calls': calls,
          'texture_remap': {'from': old, 'to': new}, 'graph': graph, 'files': rows,
          'visual_proof': False, 'humber_graph_reopen_pending': True,
          'engine': unreal.SystemLibrary.get_engine_version()}
(AUDIT / 'humber_migration.json').write_text(json.dumps(report, indent=2))
print('FILM_HUMBER_MIGRATION_OK ' + str(len(rows)))
