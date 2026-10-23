"""Create a small shader-only UE project archive from verified migrated packages."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'Saved/Audit/UniversalFilm_20261016'
DELIVERY = ROOT / 'Saved/UniversalFilmDelivery_20261016'
OUT = ROOT / 'Showcase/UniversalFilm_20261016'


def main():
    report = json.loads((AUDIT / 'humber_migration.json').read_text())
    if report['expression_count'] != 1303 or not all(report['function_calls']):
        raise RuntimeError('Missing verified graph; inspect migration evidence')
    files = [(DELIVERY / 'UniversalFilm.uproject', 'UniversalFilm.uproject'),
             (DELIVERY / 'Config/DefaultEngine.ini', 'Config/DefaultEngine.ini')]
    manifest = []
    for entry in report['files']:
        relative = 'Content/' + entry['package'][6:] + '.uasset'
        source = DELIVERY / relative
        if not source.exists():
            raise RuntimeError('Missing archived dependency ' + entry['package'])
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        manifest.append({'package': entry['package'], 'file': relative,
                         'sha256': digest, 'bytes': source.stat().st_size})
        files.append((source, relative))
    readme = '''# Melodia Universal Toon — film project bundle

Open UniversalFilm.uproject in Unreal Engine 5.8. Substrate is enabled in
Config/DefaultEngine.ini. Wait for first-open shader compilation.

Parent: /Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal
Examples: /Game/Staging/DanaProfessor_20261016/WarmCourtyard/MI_Dana_*
Make a material instance for each character's look. Keep package paths intact.

This is the existing working graph: 1,303 expressions and 16 function-call
nodes. The graph was opened and compared in this isolated project before
migration into Humber. Humber scene assets and rig/eye verification are
separate from this shader-only bundle. No Maya rig or gameplay code is included.

One stroke texture is remapped to
/Game/EnvSandbox/Textures/UniversalFilm/T_SDF_Strokes to avoid replacing
Humber's existing texture. Required sky/weather helpers and third-party
textures retain their original licenses. This local project archive is not
permission to publish those dependencies as a public asset library.

Start with BaseTint, Roughness and Metallic on an instance. Keep optional
wind, boil, sparkle and layered effects disabled for the first cast review.
The included example instances contain the restrained Dana look settings.

The archive excludes caches, Saved/, engine plugins and character sources.
See MANIFEST.json for every included package and its hash. Another machine
has not yet been tested; engine 5.8 compatibility is the supported target.
'''
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / 'UniversalToonShader_UE58_20261016.zip'
    manifest_doc = {'engine': '5.8', 'master': report['master'],
                    'expression_count': report['expression_count'],
                    'function_calls': report['function_calls'], 'files': manifest}
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for source, relative in files:
            archive.write(source, 'UniversalToonShader_UE58/' + relative)
        archive.writestr('UniversalToonShader_UE58/README.md', readme)
        archive.writestr('UniversalToonShader_UE58/MANIFEST.json', json.dumps(manifest_doc, indent=2))
    with zipfile.ZipFile(target) as archive:
        corrupt = archive.testzip()
        if corrupt:
            raise RuntimeError('Archive CRC failure ' + corrupt)
        for entry in manifest:
            archived = archive.read('UniversalToonShader_UE58/' + entry['file'])
            if hashlib.sha256(archived).hexdigest() != entry['sha256']:
                raise RuntimeError('Archive hash mismatch ' + entry['file'])
    receipt = {'result': 'archive_crc_and_all_package_hashes_passed',
               'archive': str(target), 'bytes': target.stat().st_size,
               'package_count': len(manifest),
               'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
    (AUDIT / 'archive.json').write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
