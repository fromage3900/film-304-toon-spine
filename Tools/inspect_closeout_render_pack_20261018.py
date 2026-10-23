"""Inspect actual exports and assemble review contact sheets, without altering masters."""
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat
import statistics

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'Showcase/Film304_Closeout_20261018'
OUT=ROOT/'Saved/Audit/Closeout_20261018'
FONT=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',24)

def sheet(items,destination,columns,width=640):
    height=width*9//16
    canvas=Image.new('RGB',(width*columns,(height+36)*((len(items)+columns-1)//columns)),(18,21,27))
    draw=ImageDraw.Draw(canvas)
    for index,(label,path) in enumerate(items):
        image=Image.open(path).convert('RGB');assert image.size==(1920,1080),(str(path),image.size)
        image=image.resize((width,height),Image.Resampling.LANCZOS)
        x=(index%columns)*width;y=(index//columns)*(height+36)
        draw.text((x+10,y+3),label,font=FONT,fill=(235,236,240));canvas.paste(image,(x,y+36))
    canvas.save(destination)

def main(version='v01',shots=None):
    studies=[]
    for letter,name in zip('ABCD',['Original dusk','Neutral office','Warm desk','Late office']):
        path=BASE/f'LightingStudies_v02/Lighting_{letter}/LS_Closeout_Lighting_{letter}48f_v01.0010.png'
        assert path.exists(),path;studies.append((letter+' — '+name,path))
    sheet(studies,BASE/'Lighting_Comparison_v02.jpg',2,800)
    report={'lighting_studies':4,'motion':{}}
    for shot in (shots or ['David','WindowHero']):
        folder=BASE/('Motion48_'+version)/shot
        files=sorted(folder.glob('*.png'))
        if len(files)!=48:
            report['motion'][shot]={'count':len(files),'complete':False};continue
        indices=[int(p.stem.rsplit('.',1)[1]) for p in files]
        assert indices==list(range(48)),indices
        for p in files:
            with Image.open(p) as im:assert im.size==(1920,1080);im.verify()
        selected=[0,8,16,24,40,47]
        suffix='' if version=='v01' else '_'+version
        sheet([(f'{shot} — frame {i}',files[i]) for i in selected],BASE/f'{shot}_Motion_ContactSheet{suffix}.jpg',3)
        report['motion'][shot]={'count':48,'complete':True,'fps':24,'duration_seconds':2,
                                'resolution':[1920,1080],'image_decode_gate':True}
        frames=[Image.open(p).convert('RGB').resize((480,270)) for p in files]
        error=lambda a,b:sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3
        adjacent=[error(a,b) for a,b in zip(frames,frames[1:])]
        report['motion'][shot]['sampled_pixel_seam_measurement']={
            'wrap_mean_abs_8bit':error(frames[-1],frames[0]),
            'adjacent_mean_abs_median':statistics.median(adjacent),
            'adjacent_mean_abs_max':max(adjacent),
            'scope':'480x270 full-frame comparison; supports pop detection, not artistic approval'}
    report_name='render_export_inspection.json' if version=='v01' else 'render_export_inspection_'+version+'.json'
    (OUT/report_name).write_text(json.dumps(report,indent=2))
    print(json.dumps(report))

if __name__=='__main__':
    import sys
    main(sys.argv[1] if len(sys.argv)>1 else 'v01',sys.argv[2:] or None)
