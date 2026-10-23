from pathlib import Path
import json,shutil,subprocess
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'Showcase/Film304_Closeout_20261018'
OUT=BASE/'Delivery_Final_20261018'

def main():
    OUT.mkdir(exist_ok=True)
    stills=OUT/'Stills_4K';stills.mkdir(exist_ok=True)
    report={'stills':[],'motion':[],'limits':['Editable project archive has not been reopened on a second machine.','Sam retains the existing window-facing typing pose.','Existing stylized skyline retained; no new Houdini skyline authored.','Dana skin and shared toon graphs remain frozen.']}
    for p in (BASE/'LightingStudies_v55').glob('*/*.png'):
        with Image.open(p) as im:
            im.load();assert im.size==(3840,2160)
        target=stills/(p.parent.name+'.png');shutil.copy2(p,target)
        report['stills'].append({'shot':p.parent.name,'path':str(target),'size':[3840,2160],'viewed':True})
    assert len(report['stills'])==5
    for folder in sorted((BASE/'Motion48_v56').iterdir()):
        if not folder.is_dir():continue
        frames=sorted(folder.glob('*.png'));assert len(frames)==48,(folder,len(frames))
        raw=OUT/'Motion_Frames'/folder.name;raw.mkdir(parents=True,exist_ok=True)
        for p in frames:shutil.copy2(p,raw/p.name)
        arrays=[]
        sheet=Image.new('RGB',(960,540),(20,20,20));draw=ImageDraw.Draw(sheet)
        chosen=[0,8,16,24,40,47]
        for i,p in enumerate(frames):
            assert p.stem.endswith(f'.{i:04d}')
            with Image.open(p) as im:
                im.load();assert im.size==(1920,1080)
                arrays.append(np.asarray(im.convert('RGB').resize((480,270)),dtype=np.float32))
                if i in chosen:
                    j=chosen.index(i);sheet.paste(im.convert('RGB').resize((320,180)),((j%3)*320,(j//3)*270))
                    draw.text(((j%3)*320+8,(j//3)*270+185),f'Frame {i}',fill='white')
        adj=[float(np.abs(a-b).mean()) for a,b in zip(arrays,arrays[1:])]
        wrap=float(np.abs(arrays[0]-arrays[-1]).mean())
        sheet.save(OUT/(folder.name+'_contact.jpg'),quality=92)
        destination=OUT/(folder.name+'_48frames_24fps.mp4')
        pattern=str(folder/(frames[0].name.rsplit('.',2)[0]+'.%04d.png'))
        subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','24','-start_number','0','-i',pattern,'-frames:v','48','-c:v','libx264','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(destination)],check=True)
        report['motion'].append({'shot':folder.name,'frames':48,'fps':24,'path':str(destination),'wrap_mae_8bit':wrap,'maximum_adjacent_mae':max(adj),'mean_adjacent_mae':sum(adj)/len(adj),'seam_within_maximum_ordinary_change':wrap<=max(adj),'raw_frames':str(raw)})
    assert len(report['motion'])==2
    (OUT/'delivery_manifest.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
