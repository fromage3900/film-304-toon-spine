"""Locate loop-boundary changes in rendered masters, without editing them."""
import json
from pathlib import Path
from PIL import Image,ImageChops,ImageEnhance,ImageStat

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'Showcase/Film304_Closeout_20261018/Motion48_v01'
OUT=ROOT/'Saved/Audit/Closeout_20261018'

def error(a,b):return sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3

def main():
    report={}
    for shot in ['David','WindowHero']:
        frames={i:Image.open(BASE/shot/f'LS_Closeout_{shot}48f_v01.{i:04}.png').convert('RGB') for i in [0,1,46,47]}
        wrap=ImageChops.difference(frames[0],frames[47])
        ImageEnhance.Brightness(wrap).enhance(20).save(OUT/f'{shot}_wrap_difference_x20.png')
        regions={'top':(0,0,1920,300),'middle':(0,300,1920,750),'bottom':(0,750,1920,1080)}
        rows={}
        for name,box in regions.items():
            f={i:im.crop(box) for i,im in frames.items()}
            rows[name]={'wrap_mae':error(f[0],f[47]),'first_step_mae':error(f[0],f[1]),
                        'last_step_mae':error(f[46],f[47]),
                        'mean_rgb_start':ImageStat.Stat(f[0]).mean,'mean_rgb_end':ImageStat.Stat(f[47]).mean}
        report[shot]=rows
    (OUT/'seam_region_diagnosis.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
