"""Build the Office Spider animatic: frame-exact, piped to ffmpeg.

Same spec as the VSE version (37 shots, 24 fps, 1920x1080, silent, title + end
card, max 3 dissolves). Blender's VSE hangs in background mode on this build, so
frames are composited here and streamed raw into ffmpeg.

Run:
    python Tools/build_animatic.py
"""
import os, sys, json, subprocess, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = r"G:\film-304-toon-spine"
PANELS = os.path.join(ROOT, "Saved", "Animatic", "Panels")
CARDS = os.path.join(ROOT, "Saved", "Animatic", "Cards")
OUT = os.path.join(ROOT, "Saved", "Animatic")
FRAMES = os.path.join(OUT, "Frames")
os.makedirs(CARDS, exist_ok=True)
os.makedirs(FRAMES, exist_ok=True)

FPS, W, H = 24, 1920, 1080
DISSOLVE = 12  # frames (0.5s)

P1 = [3.0, 2.0, 1.5, 1.0, 2.0, 1.5, 1.0, 1.5, 3.0, 2.0, 2.0, 2.0]
P2 = [2.0, 1.5, 1.5, 1.5, 1.5, 1.5, 2.0, 2.0, 3.0, 1.5, 2.0, 2.0]
P3 = [2.0, 1.5, 1.5, 3.0, 1.5, 1.5, 2.5, 1.5, 1.0, 3.0, 3.0, 1.5]


def font(sz, bold=True):
    for p in ((r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"),
              r"C:\Windows\Fonts\segoeui.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def cards():
    t = Image.new("RGB", (W, H), (10, 11, 14))
    d = ImageDraw.Draw(t)
    d.text((W // 2, H // 2 - 70), "OFFICE  SPIDER", font=font(96), fill=(232, 234, 240), anchor="mm")
    d.text((W // 2, H // 2 + 40), "a short film", font=font(34, False), fill=(150, 156, 168), anchor="mm")
    d.text((W // 2, H // 2 + 110), "Brennan Shepherd   -   Film 304 / ANMN301",
           font=font(28, False), fill=(120, 126, 138), anchor="mm")
    t.save(os.path.join(CARDS, "CARD_title.png"))

    e = Image.new("RGB", (W, H), (10, 11, 14))
    d = ImageDraw.Draw(e)
    d.text((W // 2, H // 2 - 40), "THE  END", font=font(88), fill=(232, 234, 240), anchor="mm")
    d.text((W // 2, H // 2 + 60), "storyboard   Jeffrey Dawn", font=font(30, False),
           fill=(150, 156, 168), anchor="mm")
    d.text((W // 2, H // 2 + 110), "Brennan Shepherd   -   2026", font=font(26, False),
           fill=(120, 126, 138), anchor="mm")
    e.save(os.path.join(CARDS, "CARD_end.png"))


def plate(path):
    """Scale a panel to fill the 1080p frame (upscaling is intended: the source
    panels are only ~407x300 each), letterboxed on a dark ground."""
    im = Image.open(path).convert("RGB")
    scale = min((W - 40) / float(im.width), (H - 40) / float(im.height))
    nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
    if (nw, nh) != im.size:
        im = im.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGB", (W, H), (14, 15, 18))
    canvas.paste(im, ((W - im.width) // 2, (H - im.height) // 2))
    return np.asarray(canvas, dtype=np.uint8)


def find_ffmpeg():
    for c in (r"C:\Users\froma\AppData\Local\Microsoft\WinGet\Packages"
              r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
              r"\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe", "ffmpeg"):
        p = shutil.which(c) or (c if os.path.exists(c) else None)
        if p:
            return p
    return "ffmpeg"


def main():
    cards()
    title = plate(os.path.join(CARDS, "CARD_title.png"))
    end = plate(os.path.join(CARDS, "CARD_end.png"))

    shots = [("title", title, 72)]
    for page, durs in ((1, P1), (2, P2), (3, P3)):
        for i, d in enumerate(durs, start=1):
            p = os.path.join(PANELS, "SB_p%02d_%02d.png" % (page, i))
            if os.path.exists(p):
                shots.append(("p%02d_%02d" % (page, i), plate(p), int(round(d * FPS))))
    shots.append(("end", end, 48))

    ff = find_ffmpeg()
    out_mp4 = os.path.join(OUT, "OfficeSpider_Animatic_v01.mp4")
    cmd = [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
           "-r", str(FPS), "-i", "-", "-an",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    timeline, frame_no = [], 0
    for idx, (label, img, dur) in enumerate(shots):
        start = frame_no
        for k in range(dur):
            a = img
            # dissolve in from the previous shot
            if idx > 0 and k < DISSOLVE and idx - 1 < len(shots):
                prev = shots[idx - 1][1]
                t = (k + 1) / float(DISSOLVE + 1)
                a = (prev.astype(np.float32) * (1 - t) + img.astype(np.float32) * t).astype(np.uint8)
            proc.stdin.write(np.ascontiguousarray(a).tobytes())
            frame_no += 1
        timeline.append({"shot": idx, "label": label, "start_frame": start,
                         "frames": dur, "seconds": round(dur / FPS, 2)})

    proc.stdin.close()
    rc = proc.wait()

    report = {"fps": FPS, "resolution": [W, H], "frames": frame_no,
              "seconds": round(frame_no / FPS, 2), "shots": len(shots),
              "ffmpeg_rc": rc, "out": out_mp4, "timeline": timeline}
    json.dump(report, open(os.path.join(OUT, "animatic_report.json"), "w"), indent=2)
    print("ANIMATIC shots=%d frames=%d sec=%.1f rc=%d -> %s"
          % (len(shots), frame_no, frame_no / FPS, rc, out_mp4))


main()
