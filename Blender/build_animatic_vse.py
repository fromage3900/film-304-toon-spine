"""Build the Office Spider animatic in Blender's VSE.

37 shots, 24 fps, 1920x1080, silent, title + end card, max 3 dissolves.
Shot durations come from Docs/ANMN301_ANIMATIC_TIMING_SHEET.md.

Run:
    blender.exe -b --python Blender/build_animatic_vse.py
"""
import bpy, os, json

ROOT = r"G:\film-304-toon-spine"
PANELS = os.path.join(ROOT, "Saved", "Animatic", "Panels")
CARDS = os.path.join(ROOT, "Saved", "Animatic", "Cards")
OUT = os.path.join(ROOT, "Saved", "Animatic")
os.makedirs(CARDS, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

FPS = 24
W, H = 1920, 1080

# ---------------------------------------------------------------- cards
def make_cards():
    from PIL import Image, ImageDraw, ImageFont
    def font(sz, bold=True):
        for p in ((r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"),
                  r"C:\Windows\Fonts\segoeui.ttf"):
            if os.path.exists(p):
                return ImageFont.truetype(p, sz)
        return ImageFont.load_default()

    t = Image.new("RGB", (W, H), (10, 11, 14))
    d = ImageDraw.Draw(t)
    d.text((W // 2, H // 2 - 70), "OFFICE  SPIDER", font=font(96), fill=(232, 234, 240), anchor="mm")
    d.text((W // 2, H // 2 + 40), "a short film", font=font(34, False), fill=(150, 156, 168), anchor="mm")
    d.text((W // 2, H // 2 + 110), "Brennan Shepherd  -  Film 304 / ANMN301", font=font(28, False),
           fill=(120, 126, 138), anchor="mm")
    tp = os.path.join(CARDS, "CARD_title.png")
    t.save(tp)

    e = Image.new("RGB", (W, H), (10, 11, 14))
    d = ImageDraw.Draw(e)
    d.text((W // 2, H // 2 - 40), "THE  END", font=font(88), fill=(232, 234, 240), anchor="mm")
    d.text((W // 2, H // 2 + 60), "storyboard  Jeffrey Dawn", font=font(30, False), fill=(150, 156, 168), anchor="mm")
    d.text((W // 2, H // 2 + 110), "Brennan Shepherd  -  2026", font=font(26, False), fill=(120, 126, 138), anchor="mm")
    ep = os.path.join(CARDS, "CARD_end.png")
    e.save(ep)
    return tp, ep


# ---------------------------------------------------------------- timing
TITLE_D = 3.0
END_D = 2.0
DISSOLVE_D = 0.5
P1 = [3.0, 2.0, 1.5, 1.0, 2.0, 1.5, 1.0, 1.5, 3.0, 2.0, 2.0, 2.0]
P2 = [2.0, 1.5, 1.5, 1.5, 1.5, 1.5, 2.0, 2.0, 3.0, 1.5, 2.0, 2.0]
P3 = [2.0, 1.5, 1.5, 3.0, 1.5, 1.5, 2.5, 1.5, 1.0, 3.0, 3.0, 1.5]


def panel(page, n):
    p = os.path.join(PANELS, "SB_p%02d_%02d.png" % (page, n))
    return p if os.path.exists(p) else None


def build():
    tp, ep = make_cards()

    scn = bpy.context.scene
    scn.render.resolution_x = W
    scn.render.resolution_y = H
    scn.render.resolution_percentage = 100
    scn.render.fps = FPS
    scn.render.fps_base = 1.0
    scn.render.image_settings.file_format = "FFMPEG"
    scn.render.ffmpeg.format = "MPEG4"
    scn.render.ffmpeg.codec = "H264"
    scn.render.ffmpeg.constant_rate_factor = "HIGH"
    scn.render.ffmpeg.ffmpeg_preset = "GOOD"
    scn.render.filepath = os.path.join(OUT, "OfficeSpider_Animatic_v01.mp4")
    scn.render.audio_codec = "NONE"
    try:
        scn.render.ffmpeg.audio_codec = "NONE"
    except Exception:
        pass
    scn.render.use_seq_seam = False

    se = scn.sequence_editor_create()
    # wipe any default strips
    strips = getattr(se, "strips", None) or getattr(se, "sequences", None)
    for s in list(strips):
        try:
            strips.remove(s)
        except Exception:
            pass

    def add_image(path, dur_frames, channel, frame):
        seqs = getattr(se, "strips", None)
        if seqs is None:
            seqs = se.sequences
        try:
            s = seqs.new_image(name=os.path.basename(path), filepath=path,
                               channel=channel, frame_start=frame)
        except TypeError:
            s = seqs.new_image(name=os.path.basename(path), filepath=path,
                               channel=channel, frame_start=frame, fit_method="ORIGINAL")
        s.frame_final_duration = int(dur_frames)
        return s

    def add_cross(s1, s2, dur, channel, frame):
        seqs = getattr(se, "strips", None) or se.sequences
        try:
            return seqs.new_effect(name="Cross", type="CROSS", channel=channel,
                                   frame_start=frame, length=dur,
                                   input1=s1, input2=s2)
        except TypeError:
            try:
                return seqs.new_effect(name="Cross", type="CROSS", channel=channel,
                                       frame_start=frame, frame_end=frame + dur,
                                       seq1=s1, seq2=s2)
            except Exception:
                return None
        except Exception:
            return None

    ch_img, ch_fx = 1, 2
    frame = 1
    timeline = []

    title = add_image(tp, int(TITLE_D * FPS), ch_img, frame)
    timeline.append({"shot": 0, "label": "title", "start": frame, "dur": TITLE_D})
    frame += title.frame_final_duration

    def run_page(page, durs):
        nonlocal frame
        for i, d in enumerate(durs, start=1):
            p = panel(page, i)
            if not p:
                continue
            f = int(round(d * FPS))
            s = add_image(p, f, ch_img, frame)
            timeline.append({"shot": len(timeline), "label": "p%02d_%02d" % (page, i),
                             "start": frame, "dur": d})
            frame += f
            return None
        return None

    def page_blocks(page, durs):
        """Return list of (path, frames) so we can overlap the dissolve."""
        out = []
        for i, d in enumerate(durs, start=1):
            p = panel(page, i)
            if p:
                out.append((p, int(round(d * FPS))))
        return out

    # page 1
    blocks = page_blocks(1, P1)
    first = None
    prev = None
    for idx, (p, f) in enumerate(blocks):
        s = add_image(p, f, ch_img, frame)
        if idx == 0:
            first = s
        timeline.append({"shot": len(timeline), "label": "p01_%02d" % (idx + 1),
                         "start": frame, "dur": f / FPS})
        frame += f
        prev = s

    # dissolve 1 -> page 2
    b2 = page_blocks(2, P2)
    if b2:
        s = add_image(b2[0][0], b2[0][1], ch_img, frame)
        add_cross(prev, s, int(DISSOLVE_D * FPS), ch_fx, frame)
        timeline.append({"shot": len(timeline), "label": "p02_01", "start": frame,
                         "dur": b2[0][1] / FPS, "dissolve_in": DISSOLVE_D})
        frame += b2[0][1]
        prev = s
        for idx, (p, f) in enumerate(b2[1:], start=1):
            s = add_image(p, f, ch_img, frame)
            timeline.append({"shot": len(timeline), "label": "p02_%02d" % (idx + 1),
                             "start": frame, "dur": f / FPS})
            frame += f
            prev = s

    # dissolve 2 -> page 3
    b3 = page_blocks(3, P3)
    if b3:
        s = add_image(b3[0][0], b3[0][1], ch_img, frame)
        add_cross(prev, s, int(DISSOLVE_D * FPS), ch_fx, frame)
        timeline.append({"shot": len(timeline), "label": "p03_01", "start": frame,
                         "dur": b3[0][1] / FPS, "dissolve_in": DISSOLVE_D})
        frame += b3[0][1]
        prev = s
        for idx, (p, f) in enumerate(b3[1:], start=1):
            s = add_image(p, f, ch_img, frame)
            timeline.append({"shot": len(timeline), "label": "p03_%02d" % (idx + 1),
                             "start": frame, "dur": f / FPS})
            frame += f
            prev = s

    # dissolve 3 -> end card
    end = add_image(ep, int(END_D * FPS), ch_img, frame)
    add_cross(prev, end, int(DISSOLVE_D * FPS), ch_fx, frame)
    timeline.append({"shot": len(timeline), "label": "end", "start": frame,
                     "dur": END_D, "dissolve_in": DISSOLVE_D})
    frame += end.frame_final_duration

    scn.frame_start = 1
    scn.frame_end = frame
    total = sum(t["dur"] for t in timeline)
    json.dump({"fps": FPS, "resolution": [W, H], "total_frames": frame - 1,
               "total_seconds": round(total, 2), "shots": len(timeline),
               "timeline": timeline},
              open(os.path.join(OUT, "animatic_report.json"), "w"), indent=2)
    print("BUILT shots=%d frames=%d seconds=%.1f" % (len(timeline), frame - 1, total), flush=True)


build()
