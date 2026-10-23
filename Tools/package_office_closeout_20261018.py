"""Package the saved project, without caches, credentials or historical render studies."""
from pathlib import Path
import zipfile, json, hashlib, datetime

ROOT=Path(__file__).resolve().parents[1]
DELIVERY=ROOT/'Showcase/Film304_Closeout_20261018/Delivery_Final_20261018'
START='''FILM 304 OFFICE — REUSABLE UNREAL PROJECT
Open HumberToonShader.uproject with Unreal Engine 5.8 and the project plugins enabled.
Open /Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office.
Window > Cinematics > Movie Render Queue. Load Q_Office_ReadyToRender from
/Game/MoviePipelines/Film304Closeout_20261018 if the queue is empty.
Enable the desired job and choose Render (Local). Neutral ensemble is enabled by default.
Change the output folder to a location on your computer before rendering.
CFG_Office_Motion48_1080_v01 renders 48 frames at 24 fps.
CFG_Office_Still20_1080_v01 renders one frame for material staging.
Neutral, Warm and Cool lighting sequences are under /Game/Sequences/Film304Closeout_20261018.
Dana's current skin and the shared toon graphs are intentionally preserved.
Native Houdini source assets are under Tools/houdini/Published/Film304Closeout_20261018.
This is an editable project archive, not a cooked standalone application.
External plugin installation/license requirements still apply. See delivery manifest for proof limits.
Delivery_Final_20261018 contains five 4K stills, original 48-frame motion exports,
and separate 40-frame Loop40 movies with an eight-frame cyclic dissolve.
The native 48-frame renders have a brightness discontinuity; use Loop40 for looping playback.
'''

def main():
    DELIVERY.mkdir(parents=True,exist_ok=True)
    archive=DELIVERY/'Film304_Reusable_Office_20261018.zip'
    assert not archive.exists(), archive
    excluded={'Intermediate','DerivedDataCache','__pycache__','.git','.claude','node_modules'}
    files=[ROOT/'HumberToonShader.uproject']
    for folder in ('Config','Content','Plugins','Python','Tools','Docs'):
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and not excluded.intersection(p.relative_to(ROOT).parts) and p.suffix.lower() not in ('.pyc','.zip','.pdb') and p.name not in ('.env','.mcp.json'):
                files.append(p)
    files += [p for p in DELIVERY.rglob('*') if p.is_file() and p != archive]
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
        for p in files:
            member=p.relative_to(ROOT).as_posix()
            if member=='Config/DefaultEngine.ini':
                text=p.read_text(encoding='utf-8-sig')
                import re
                text=re.sub(r'^SecurityToken=.*$', 'SecurityToken=',text,flags=re.MULTILINE)
                text+='\n[/Script/EngineSettings.GameMapsSettings]\nEditorStartupMap=/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office.L_Film_Office\n'
                z.writestr(member,text)
            else:z.write(p,member)
        z.writestr('START_HERE.txt',START)
    with zipfile.ZipFile(archive) as z:
        bad=z.testzip()
        assert bad is None,bad
        names=set(z.namelist())
        for member in ('HumberToonShader.uproject','Content/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office.umap','Content/MoviePipelines/Film304Closeout_20261018/Q_Office_ReadyToRender.uasset'):
            assert member in names,member
    digest=hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()
    report={'archive':str(archive),'bytes':archive.stat().st_size,'sha256':digest,'crc_verified':True,'files':len(files)+1,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'proof_limit':'Saved editable project and archive CRC verified; archive has not been extracted and opened on a second machine.'}
    (DELIVERY/'archive_verification.json').write_text(json.dumps(report,indent=2))
    (DELIVERY/'START_HERE.txt').write_text(START)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
