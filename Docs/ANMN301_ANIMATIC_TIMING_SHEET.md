# ANMN301 Animatic — Timing Sheet & Shot List

**Project:** Office Spider (short film) — ANMN301 Animatic Story Edit (25%)
**Pipeline:** UE 5.8 Sequencer + Movie Render Pipeline (film repo: HumberToonShader.uproject)
**Storyboard source:** `Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/01_Preprod/Storyboard/SB_OfficeSpider_Page*.png` (17 pages, 36 panels)
**Brief spec:** MP4, 1920×1080, 24 fps, silent, max 3 dissolves, TITLE CARD + END CARD required
**Pacing guide:** establishing 3-5s · reaction 2-4s · action 1-2s · dialogue 3-6s · quick transitions 1-2s

---

## Timing Summary

| Section | Shots | Duration |
|---|---|---|
| Title Card | 1 | 3.0s |
| Page 1 — Establishing & Setup | 12 | 22.5s |
| Dissolve 1 (Page 1→2) | — | 0.5s |
| Page 2 — Disruption & Search | 12 | 21.5s |
| Dissolve 2 (Page 2→3) | — | 0.5s |
| Page 3 — Confrontation & Reveal | 11 | 21.5s |
| Dissolve 3 (last shot→End) | — | 0.5s |
| End Card | 1 | 2.0s |
| **Total** | **37** | **~71.5s** |

> Target: 65-75s. Adjust individual shot durations to taste. Cut 0.5s from reactions if needed.

---

## Shot List (frame-accurate at 24 fps)

### Title Card
| # | Shot | Type | Duration | Frames | Notes |
|---|---|---|---|---|---|
| 0 | Title Card — "Office Spider" | title | 3.0s | 72 | Film title + student name |

### Page 1 — Establishing & Setup (12 panels)

| # | Shot | Type | Duration | Frames | SFX/Notes |
|---|---|---|---|---|---|
| 1 | Establishing — slow zoom into office building | establishing | 3.0s | 72 | Green arrow = camera zoom |
| 2 | Interior office — worker typing at desk | action | 2.0s | 48 | SFX: TAP TAP TAP |
| 3 | Worker typing (alternate angle) | action | 1.5s | 36 | Continuation of shot 2 |
| 4 | Paper shuffle | action | 1.0s | 24 | SFX: Paper Scratch |
| 5 | Notification alert — cat photo on screen | reaction | 2.0s | 48 | SFX: BEEP BEEP BEEP |
| 6 | Worker stretches, leans back | action | 1.5s | 36 | Body language shift |
| 7 | Paper shuffle again | action | 1.0s | 24 | Repeat motif |
| 8 | Worker leans forward, focused | action | 1.5s | 36 | Body language shift |
| 9 | Desk close-up — calendar "Donut Day", cat photo, supplies | establishing | 3.0s | 72 | Key prop setup |
| 10 | Calendar extreme close-up — "Donut Day" confirmed | reaction | 2.0s | 48 | Dramatic irony setup |
| 11 | Worker face close-up — annoyed/upset | reaction | 2.0s | 48 | Red arrow = reaction shot |
| 12 | Worker face close-up — excited/happy (remembers Donut Day) | reaction | 2.0s | 48 | Emotional pivot |

### Dissolve 1 — Page 1 → Page 2 (0.5s, 12 frames)

### Page 2 — Disruption & Search (12 panels)

| # | Shot | Type | Duration | Frames | SFX/Notes |
|---|---|---|---|---|---|
| 13 | Worker at desk, shocked/surprised — sees spider | reaction | 2.0s | 48 | Red arrow = sudden action |
| 14 | Worker standing, hunched over desk searching | action | 1.5s | 36 | Body language shift |
| 15 | Worker holding object (rolled paper), glancing left | action | 1.5s | 36 | Prop introduction |
| 16 | Worker standing, searching right | action | 1.5s | 36 | Camera direction change |
| 17 | Worker walks toward break room door | action | 1.5s | 36 | Movement shot |
| 18 | Worker enters break room | action | 1.5s | 36 | Location change |
| 19 | Worker at break room counter, looking down | reaction | 2.0s | 48 | Discovery beat |
| 20 | Worker spots spider on counter | reaction | 2.0s | 48 | Discovery beat |
| 21 | Wide establishing shot of break room | establishing | 3.0s | 72 | New location establish |
| 22 | Worker bent under counter searching (BANG!) | action | 1.5s | 36 | SFX: BANG! — red arrow |
| 23 | Wide shot after bang | reaction | 2.0s | 48 | Aftermath beat |
| 24 | Worker reacting (THUMP.) | reaction | 2.0s | 48 | SFX: THUMP. — red arrow |

### Dissolve 2 — Page 2 → Page 3 (0.5s, 12 frames)

### Page 3 — Confrontation & Reveal (11 panels)

| # | Shot | Type | Duration | Frames | SFX/Notes |
|---|---|---|---|---|---|
| 25 | Worker standing, tense, alert posture | reaction | 2.0s | 48 | Tension build |
| 26 | Close-up — worker inhales (Breath in) | action | 1.5s | 36 | Micro-action |
| 27 | Close-up — worker exhales (Puffs out) | action | 1.5s | 36 | Micro-action |
| 28 | Wide shot — worker near desk, looking toward shadowed area | establishing | 3.0s | 72 | Spatial setup |
| 29 | Worker turns head toward shadow | action | 1.5s | 36 | Direction change |
| 30 | Worker steps forward into shadow | action | 1.5s | 36 | Movement into danger |
| 31 | Close-up of break room counter (coffee maker, mugs) | establishing | 2.5s | 60 | Prop setup |
| 32 | Worker at counter, leaning in toward coffee machine | action | 1.5s | 36 | Action beat |
| 33 | Close-up of hand reaching for coffee machine button | action | 1.0s | 24 | Micro-action |
| 34 | Camera pan right across break room | establishing | 3.0s | 72 | Green arrow = camera pan; SFX: Dish Clanks, Coffee Machine Buzzing |
| 35 | Wide shot — worker on left, large black spider revealed on right | establishing | 3.0s | 72 | Final reveal; SFX: Coffee Machine Buzzing |

### Dissolve 3 — Last shot → End Card (0.5s, 12 frames)

### End Card
| # | Shot | Type | Duration | Frames | Notes |
|---|---|---|---|---|---|
| 36 | End Card — credits / "The End" | end | 2.0s | 48 | Student name, course, date |

---

## UE 5.8 Sequencer Setup

### 1. Import Storyboard Panels
- Import all 17 `SB_OfficeSpider_Page*.png` files into `Content/Animatic/Storyboard/`
- Set texture compression to `UserInterface2D` (no mipmaps, no compression artifacts)
- Each panel is a full page with 12 thumbnails — you'll need to crop individual panels or use them as-is

> **Note:** The storyboard pages contain 12 panels each. For the animatic, you may want to crop individual panels. Alternatively, use the full page and zoom/pan within Sequencer.

### 2. Create Sequencer Sequence
- Create `LS_Animatic_OfficeSpider` in `Content/Animatic/Sequences/`
- Add a Camera Cut track
- Add 36+ shots (one per panel + title/end cards)

### 3. Shot Setup
For each shot:
- Add a `CineCameraActor` or use a 2D plane with the storyboard panel texture
- Set the camera to frame the panel
- Set the duration per the timing table above
- Add a dissolve/fade at the 3 designated transition points

### 4. Title Card & End Card
- Create `WBP_Animatic_TitleCard` and `WBP_Animatic_EndCard` UMG widgets
- Or use textured planes with title/end card images
- Title: "Office Spider" + your name
- End: "The End" + credits

### 5. Movie Render Pipeline
- Use existing `CFG_OS_*` configs as reference
- Create `CFG_ANIMATIC_OfficeSpider` with:
  - Resolution: 1920×1080
  - Frame rate: 24 fps
  - Output: MP4 (H.264) or PNG sequence → encode to MP4
  - Anti-aliasing: MSAA or TAA (toon edges are sensitive)
  - Samples: 1+ (animatic doesn't need 256)

### 6. Render & Export
- Render to `Saved/MovieRenders/Animatic/`
- Encode to MP4: `ShepherdBrennan_AnimaticCreation_2026-10-09.mp4`
- Verify: 1920×1080, 24 fps, silent, no corrupt frames

---

## Dissolve Placement (max 3 per brief)

| # | Location | Type |
|---|---|---|
| 1 | Title Card → Shot 1 | Fade in |
| 2 | Shot 12 → Shot 13 (Page 1→2) | Dissolve |
| 3 | Shot 35 → End Card | Fade out |

> Alternative: replace dissolve 2 with Shot 24→25 (Page 2→3) if the Page 1→2 transition reads better as a hard cut.

---

## Notes

- **Panel cropping:** The 17 storyboard PNGs are full pages with 12 thumbnails each. You'll need to crop individual panels. Use Photoshop/GIMP or UE's texture import with UV offsets.
- **SFX notes:** The storyboard has SFX annotations (TAP TAP TAP, BEEP BEEP BEEP, BANG!, THUMP., Dish Clanks, Coffee Machine Buzzing). The brief says silent export — SFX are for your reference only, not in the final.
- **Donut Day motif:** Shot 9-10 establish the "Donut Day" calendar. This creates dramatic irony for the rest of the film.
- **Spider reveal:** Shot 35 is the final reveal — worker on left, large black spider on right. This is the payoff shot.

---

*Generated 2026-11-02 · Based on Office Spider storyboard by Jeffrey Dawn (2026-10-05)*
*Pacing follows ANMN301 brief guidelines. Adjust durations to taste.*