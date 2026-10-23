"""Standard cyclic eight-frame dissolve; preserve all native 48-frame exports."""
from pathlib import Path
import json,subprocess
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Showcase/Film304_Closeout_20261018/Delivery_Final_20261018'

def main():
    report=json.loads((OUT/'delivery_manifest.json').read_text())
    for item in report['motion']:
        src=sorted(Path(item['raw_frames']).glob('*.png'));assert len(src)==48
        frames=OUT/'Loop_Frames_40'/item['shot'];frames.mkdir(parents=True,exist_ok=True)
        images=[Image.open(p).convert('RGB') for p in src]
        loop=[im.copy() for im in images[8:40]]
        loop.extend(Image.blend(images[40+i],images[i],(i+1)/8) for i in range(8))
        arrays=[]
        for i,im in enumerate(loop):
            im.save(frames/f'{i:04d}.png')
            arrays.append(np.asarray(im.resize((480,270)),dtype=np.float32))
        adj=[float(np.abs(a-b).mean()) for a,b in zip(arrays,arrays[1:])]
        wrap=float(np.abs(arrays[0]-arrays[-1]).mean())
        assert wrap<=max(adj),(item['shot'],wrap,max(adj))
        video=OUT/(item['shot']+'_Loop40_24fps.mp4')
        subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','24','-i',str(frames/'%04d.png'),'-frames:v','40','-c:v','libx264','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],check=True)
        preview=OUT/(item['shot']+'_Loop40_ThreeRepeats.mp4')
        subprocess.run(['ffmpeg','-y','-loglevel','error','-stream_loop','2','-i',str(video),'-c','copy',str(preview)],check=True)
        item['delivery_loop']={'path':str(video),'frames':40,'fps':24,'method':'Eight-frame cyclic dissolve of preserved native 48-frame export. No source animation edits.','wrap_mae_8bit':wrap,'maximum_adjacent_mae':max(adj),'seam_within_maximum_ordinary_change':True,'three_repeats':str(preview)}
        print(item['delivery_loop'])
    (OUT/'delivery_manifest.json').write_text(json.dumps(report,indent=2))

if __name__=='__main__':main()
