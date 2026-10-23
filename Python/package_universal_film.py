"""Inspect/package the existing Melodia toon shader without editing its graph.

Run in the SOURCE project with FILM_SHADER_PHASE=inspect first.
All reports live in Humber Saved/Audit/UniversalFilm_20261016.
"""
import json
import os
import hashlib
from pathlib import Path
import unreal

HUMBER = Path(__file__).resolve().parents[1]
OUT = HUMBER / 'Saved/Audit/UniversalFilm_20261016'
MASTER = '/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal'
PREVIEW = '/Game/Staging/DanaProfessor_20261016/WarmCourtyard'
OUT.mkdir(parents=True, exist_ok=True)


def inspect():
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    registry.wait_for_completion()
    master = unreal.load_asset(MASTER)
    if not master:
        raise RuntimeError('Working source master not found: ' + MASTER)
    lib = unreal.MaterialEditingLibrary
    expressions = lib.get_material_expressions(master)
    calls = []
    for node in expressions:
        if node.get_class().get_name() == 'MaterialExpressionMaterialFunctionCall':
            mf = node.get_editor_property('material_function')
            calls.append(mf.get_path_name() if mf else None)
    roots = [MASTER]
    for part in ['Skin', 'Hair', 'Shirt', 'Skirt', 'Shoes', 'Button', 'EyeWhite',
                 'Iris', 'EyeInterior', 'Stage', 'Stone', 'Bronze', 'Leaves']:
        path = PREVIEW + '/MI_Dana_' + part
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            roots.append(path)
    opts = unreal.AssetRegistryDependencyOptions(
        include_soft_package_references=True, include_hard_package_references=True,
        include_searchable_names=False, include_soft_management_references=False,
        include_hard_management_references=False)
    pending = list(roots)
    graph = {}
    while pending:
        pkg = pending.pop()
        if pkg in graph:
            continue
        deps = sorted(str(x) for x in registry.get_dependencies(pkg, opts))
        graph[pkg] = deps
        pending.extend(d for d in deps if d.startswith('/Game/') and d not in graph)
    content = Path(unreal.Paths.project_content_dir()).resolve()
    files = []
    for pkg in sorted(graph):
        path = content / (pkg[len('/Game/'):] + '.uasset')
        files.append({'package': pkg, 'file': str(path),
                      'bytes': path.stat().st_size if path.exists() else None,
                      'destination_exists': (HUMBER / 'Content' / path.relative_to(content)).exists()})
    external = sorted({dep for deps in graph.values() for dep in deps
                       if not dep.startswith(('/Game/', '/Engine/', '/Script/'))})
    report = {'phase': 'inspect', 'project': unreal.Paths.project_dir(),
              'engine': unreal.SystemLibrary.get_engine_version(),
              'master': MASTER, 'expression_count': len(expressions),
              'function_calls': calls, 'roots': roots, 'graph': graph,
              'files': files, 'external_packages': external,
              'total_bytes': sum(x['bytes'] or 0 for x in files),
              'migrate_api': unreal.AssetTools.migrate_packages.__doc__,
              'migration_options': unreal.MigrationOptions.__doc__ if hasattr(unreal, 'MigrationOptions') else None}
    (OUT / 'source_inventory.json').write_text(json.dumps(report, indent=2))
    print('FILM_SOURCE_INVENTORY ' + json.dumps({k: report[k] for k in
          ['expression_count', 'function_calls', 'total_bytes', 'external_packages']}))
    return report


if __name__ == '__main__':
    phase = os.environ.get('FILM_SHADER_PHASE', 'inspect')
    if phase == 'inspect':
        inspect()
    elif phase == 'migrate':
        inventory = json.loads((OUT / 'source_inventory.json').read_text())
        destination = HUMBER / 'Saved/UniversalFilmDelivery_20261016/Content'
        destination.mkdir(parents=True, exist_ok=True)
        options = unreal.MigrationOptions()
        options.set_editor_property('prompt', False)
        options.set_editor_property('ignore_dependencies', True)
        options.set_editor_property('asset_conflict', unreal.AssetMigrationConflict.SKIP)
        unreal.AssetToolsHelpers.get_asset_tools().migrate_packages(
            [unreal.Name(p) for p in inventory['graph']], str(destination), options)
        rows = []
        for entry in inventory['files']:
            target = destination / (entry['package'][6:] + '.uasset')
            source = Path(entry['file'])
            if not target.exists():
                raise RuntimeError('Migration omitted ' + entry['package'])
            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            target_hash = hashlib.sha256(target.read_bytes()).hexdigest()
            rows.append({'package': entry['package'], 'sha256': target_hash,
                         'source_matches': source_hash == target_hash})
        report = {'phase': 'engine_migration', 'destination': str(destination),
                  'files': rows, 'all_match': all(r['source_matches'] for r in rows)}
        (OUT / 'migration.json').write_text(json.dumps(report, indent=2))
        # Native migration may reserialize assets. The isolated-project phase
        # compares the actual graph; a different byte hash alone is not failure.
        report['requires_graph_readback'] = True
        (OUT / 'migration.json').write_text(json.dumps(report, indent=2))
        print('FILM_MIGRATION_OK ' + str(len(rows)))
    else:
        raise RuntimeError('Unknown phase ' + phase)
