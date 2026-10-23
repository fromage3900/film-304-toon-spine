"""Package only the verified film shader closure, never whole Content folders."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/'Saved/Audit/EveningExecution_20261017'
OUT=ROOT/'Showcase/Film304_20261017'
TARGET=OUT/'Film304_ToonShader_UE58_DRAFT_v02.zip'
PREFIX='Film304_ToonShader/'

def main():
    closure=json.loads((AUDIT/'film_delivery_closure.json').read_text())
    assert closure['dependency_gate_passed'] and not closure['denied'] and not closure['outside_allowlist']
    assert closure['root_master']=='/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v06'
    if TARGET.exists():raise RuntimeError('Existing draft preserved; use a new revision after further edits')
    files={}
    for package in closure['packages']:
        assert package.startswith('/Game/')
        relative=Path('Content')/(package[6:]+'.uasset')
        source=ROOT/relative;assert source.is_file(),str(source)
        files[relative.as_posix()]=source.read_bytes()
    for source in sorted((ROOT/'specs/film304_shader').glob('*.json')):
        data=source.read_bytes(); text=data.decode('utf-8').lower()
        assert not any(word in text for word in ['/game/melodia/','/game/envsandbox/','mf_madoka','mf_itto','mf_nikkidreamgrade'])
        files['Authoring/Graphs/'+source.name]=data
    files['Authoring/film304_print_surface.hlsl']=(ROOT/'Python/film304_print_surface.hlsl').read_bytes()
    project={'FileVersion':3,'EngineAssociation':'5.8','Category':'Film',
        'Description':'Film 304 toon look development shader draft','Plugins':[]}
    files['Film304ToonShader.uproject']=json.dumps(project,indent=2).encode()
    files['Config/DefaultEngine.ini']=b'[/Script/Engine.RendererSettings]\nr.Substrate=True\nr.Substrate.ProjectGBufferFormat=0\nr.DefaultFeature.AutoExposure=False\n\n[/Script/EngineSettings.GameMapsSettings]\nEditorStartupMap=/Engine/Maps/Entry\nGameDefaultMap=/Engine/Maps/Entry\n'
    files['README.md']=('''# Film 304 shader draft

Open Film304ToonShader.uproject in Unreal Engine 5.8.
Keep the supplied Content package paths intact.

Master: /Game/Materials/Masters/Film304/M_UniversalToon_Film304_v06
Look presets: /Game/Materials/Instances/Film304/
Toon, Smooth, Watercolour, Gouache, Halftone, OrderedDither and NoiseDither.
Transparent cornea master: /Game/Materials/Masters/Film304/M_Film304_CorneaClear

Create a child material instance for an asset. Bind Albedo and enable TextureWeight
for a single texture. For three-tile skin, enable bFilmUseUDIM, bind sRGB virtual
textures to BaseColorTile1001/1002/1003, and set TextureWeight to 1.
UV0 must occupy one row, U in [0,3); tile selection uses floor(U).

Print controls and pigment treatments are under Film Print and Watercolour.
Their masks and scale limits are enforced in shader code. Base effects are off.
Use bFilmSmoothShading for the smooth Substrate surface.

This is a DRAFT: editor compilation and dependency checks passed. Visual parity,
motion sampling and fresh-project opening remain to be approved. Character rigs,
cast textures, maps, caches and editor plugins are outside this shader bundle.
Authoring contains clean graph snapshots and the print-surface HLSL; the snapshots
have not yet passed a full rebuild from zero and are not certified rebuild scripts.
See MANIFEST.json for file hashes and the precise package list.
''').encode()
    entries=[{'file':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
             for name,data in sorted(files.items())]
    manifest={'status':'DRAFT_PENDING_VISUAL_MOTION_REBUILD_FRESH_OPEN_PROOF',
        'engine':'5.8','master':closure['root_master'],'package_count':len(closure['packages']),
        'dependency_closure_sha256':hashlib.sha256((AUDIT/'film_delivery_closure.json').read_bytes()).hexdigest(),
        'files':entries}
    files['MANIFEST.json']=json.dumps(manifest,indent=2).encode()
    OUT.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(TARGET,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(files.items()):archive.writestr(PREFIX+name,data)
    with zipfile.ZipFile(TARGET) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist())=={PREFIX+name for name in files}
        for row in entries:
            assert hashlib.sha256(archive.read(PREFIX+row['file'])).hexdigest()==row['sha256']
    receipt={'status':manifest['status'],'archive':str(TARGET),'package_count':len(closure['packages']),
        'bytes':TARGET.stat().st_size,'sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest(),
        'archive_crc_passed':True,'all_file_hashes_passed':True,'final_delivery_approved':False}
    (AUDIT/'film_shader_draft_archive.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
