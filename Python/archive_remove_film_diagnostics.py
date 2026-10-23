"""Archive and remove only four user-approved diagnostic sets, in two phases."""
import hashlib
import json
from pathlib import Path
import zipfile
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve(); OUT=ROOT/'Saved/Audit/EveningExecution_20261017'
MAPS=['/Game/Maps/L_CTRL_ABC_Diag','/Game/Maps/L_OfficeMaterialProbe',
    '/Game/Maps/Lookdev/L_Dana_CelRamp_Diagnostic','/Game/Maps/Lookdev/L_Dana_LashVisibility_Compare']
SEQUENCES=['/Game/Sequences/ProtoDiag/LS_R_CTRL','/Game/Sequences/ProtoDiag/LS_R_PROBE',
    '/Game/Sequences/DanaCelDiagnostic/LS_DANA_CEL_RAMP_DIAGNOSTIC_v01',
    '/Game/Sequences/DanaLashCompare/LS_DANA_LASH_VISIBILITY_COMPARE_v01']

def main():
    assert str(ROOT).replace('\\','/').lower()=='g:/film-304-toon-spine'
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name().split('.')[0]
    assert world not in MAPS and not unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering()
    registry=unreal.AssetRegistryHelpers.get_asset_registry()
    options=unreal.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,
        include_searchable_names=True,include_soft_management_references=True,include_hard_management_references=True)
    packages=set(MAPS+SEQUENCES)
    for package in MAPS:
        for prefix in ['/Game/__ExternalActors__/'+package[6:],'/Game/__ExternalObjects__/'+package[6:]]:
            packages.update(str(a.package_name) for a in registry.get_assets_by_path(prefix,True))
        for dep in registry.get_dependencies(package,options):
            dep=str(dep)
            if dep==package+'_BuiltData':packages.add(dep)
    outside={p:[str(x) for x in registry.get_referencers(p,options) if str(x) not in packages] for p in packages}
    outside={p:refs for p,refs in outside.items() if refs}
    inventory={'maps':MAPS,'sequences':SEQUENCES,'packages':sorted(packages),'outside_referencers':outside,'active_world':world}
    (OUT/'diagnostic_cleanup_inventory.json').write_text(json.dumps(inventory,indent=2))
    assert not outside,'Referenced outside approved diagnostic sets; inspect inventory'
    phase=json.loads((OUT/'diagnostic_cleanup_request.json').read_text())['phase']
    if phase=='inventory':
        print(json.dumps({'packages':len(packages),'outside_referencers':outside}));return
    assert phase=='archive_and_remove'
    archive_path=ROOT/'Saved/Recovery/Film304_Diagnostics_20261017.zip'
    assert not archive_path.exists(),'Existing recovery archive preserved; inspect receipt before rerun'
    files={}
    for package in sorted(packages):
        base=ROOT/'Content'/package[6:]
        assert base.resolve().is_relative_to(ROOT/'Content')
        for extension in ['.umap','.uasset','.uexp','.ubulk']:
            path=base.with_suffix(extension)
            if path.is_file():files[path.relative_to(ROOT).as_posix()]=path.read_bytes()
    assert all('Content/'+p[6:]+'.umap' in files for p in MAPS)
    hashes={p:hashlib.sha256(data).hexdigest() for p,data in files.items()}
    archive_path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive_path,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in files.items():archive.writestr(name,data)
        archive.writestr('RECOVERY_MANIFEST.json',json.dumps({'inventory':inventory,'sha256':hashes},indent=2))
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert all(hashlib.sha256(archive.read(p)).hexdigest()==h for p,h in hashes.items())
    receipt={'archive':str(archive_path),'archive_sha256':hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        'file_count':len(files),'backup_verified':True,'deleted':[],'failed':[],'active_world':world}
    receipt_path=OUT/'diagnostic_cleanup_receipt.json'
    receipt_path.write_text(json.dumps(receipt,indent=2))
    # Delete companion assets first, then worlds. Shared dependencies are never included.
    ordered=SEQUENCES+[p for p in sorted(packages) if p not in MAPS+SEQUENCES]+MAPS
    for package in ordered:
        if not unreal.EditorAssetLibrary.does_asset_exist(package):continue
        ok=unreal.EditorAssetLibrary.delete_asset(package)
        receipt['deleted' if ok else 'failed'].append(package)
        receipt_path.write_text(json.dumps(receipt,indent=2))
    receipt['remaining_maps']=[p for p in MAPS if unreal.EditorAssetLibrary.does_asset_exist(p)]
    receipt['cleanup_gate']=not receipt['failed'] and not receipt['remaining_maps']
    receipt_path.write_text(json.dumps(receipt,indent=2))
    print(json.dumps({'archive':str(archive_path),'files':len(files),'deleted':len(receipt['deleted']),
        'failed':receipt['failed'],'remaining_maps':receipt['remaining_maps'],'cleanup_gate':receipt['cleanup_gate']}))

if __name__=='__main__':main()
