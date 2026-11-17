# Office Spider — Layout Shots 62–66 (execution note)

**Date:** 2026-11-04
**Task:** blocking/layout pass for storyboard Page 16, shots 62–66
**Owner slot:** #09 Toon Shader & Surfacing Technical Artist / layout assist
**Scene:** `Saved/Scenes/L_Scene62-66_BS.mb`

## Handoff (v09)

- Group filename: `L_Scene62-66_BS.mb`; matching playblast: `L_Scene62-66_BS.mp4` (12.0 s, 960×540, 24 fps).
- Local handoff folder: `Saved/Layout/Playblast/` (the group’s `Layout > Playblast` upload by 12 PM tomorrow).
- v09 changes: real `P_OfficeDesk_AC` + `P_Box_EF`; 62 swatter centred; 64A crouch/wide stance + hero swatter scaled into the hand; 66A small black wall arrow with shadow casting off; 66B low-angle slam with handheld jolt; desk dressing hidden for the board match.
- Remaining before upload: the **eyes/angry face** on 63A/63B, and swapping in the updated OneDrive props when they arrive.
- Reference overlay: `Saved/Scenes/L_Scene62-66_BS_REF.mb` has one top-left storyboard image plane per shot camera (`DL_STORYBOARD_REFS`); panels are in `Saved/StoryboardRefs/`; proof render `Saved/StoryboardRefs/ref_overlay_check.png`. This REF file is for checking only — the handoff `L_Scene62-66_BS.mb` has no image planes.

## What was built

The **v03** scene references both characters: David (`DavidRN` →
`Saved/OfflineIntake/Source/David_Rig_v1.51.mb`) and Spider (`SpiderRN` →
`Saved/OfflineIntake/Source/C_Spider.ma`). Both references are loaded, with
namespaces `David` and `Spider`. The earlier `_v02` (reference build) and `_v01`
(native David) scenes are retained as fallbacks. Both source files were left
untouched (mtimes still 2026-10-16 19:41).

> **Reference caveat:** the reference file paths are currently absolute
> (`G:/…`). Keep the G: drive mounted, or convert them to relative paths before
> handing the scene to someone on another workstation.

- David scaled to **180 cm**; spider scaled to a readable giant-spider size.
- Office set: desk, shelf, spray can, fly swatter, silk thread, back wall.
- Door set: posts + lintel + hinged door panel, corridor floor/wall, arrow card.
- Exterminator proxy (primitive blockout — no exterminator rig exists in `Saved/OfflineIntake/Source`).
- Eight cameras, one per storyboard beat, 24 fps, 1920×1080 gate (1.417 in = 36 mm).
- Per-shot poses keyed on the main FK controls (30 keys each), plus root motion, spider
  descent, visibility cuts, door slam, exterminator step-in and the title card.

### v03 polish pass (2026-11-04)

All 20 staged improvements are in the v03 scene:

- Scene README/metadata, exact camera names (`Cam_Shot62`), camera switcher,
  `LayoutCameras` set, display layers, playback defaults, per-shot selection sets,
  one-click playblast script, master/camera grouping.
- Face/eye material split + brow keys; hand/finger grip; hero swatter and mug
  props; 64B IK leg cycle; spider settle/thread sway.
- Red grid swatter; desk monitor/keyboard/papers/mug/chair; door trim, handle,
  threshold and corridor; exterminator belt/collar/boots/tank; key/fill/rim lights,
  gradient backdrop, shadows; 62 push-in, 63B push, 66A truck, 66B jolt; new
  hand-lettered title card.

**v03 caveats for the GUI pass:** the eyelid-open control is still unresolved,
the hero swatter/mug need final hand alignment, the new lighting is moodier and
needs a look decision, the timeline-marker command is absent in Maya 2027 batch
(fallback locators are in `Layout_ShotMarkers`), and reference paths remain
absolute `G:/…` (the `relativePath` flag is not exposed on these reference nodes).

| Shot | Frames | Camera | Beat |
|---|---|---|---|
| 62 | 1–48 | `Cam_Shot62` | spider descends on silk to the swatter |
| 63A | 49–72 | `Cam_Shot63A1` | worker annoyed / gritted |
| 63B | 73–120 | `Cam_Shot63B1` | worker shouts (jaw open) |
| 64A | 121–144 | `Cam_Shot64A1` | ready stance facing the spray can |
| 64B | 145–192 | `Cam_Shot64B1` | run / lunge |
| 65 | 193–216 | `Cam_Shot65` | “15 mins later” card |
| 66A | 217–240 | `Cam_Shot66A1` | closed door + arrow cue |
| 66B | 241–288 | `Cam_Shot66B1` | door slams, exterminator enters |

Total: **288 frames / 12.0 s**.

## Evidence

- Final scene: `Saved/Scenes/Shepherd_Brennan_LayoutScene(62-66)_BS_v03.mb`
- Reference/pose proof: `Saved/Scenes/v03_verify.json`
- Machine-readable report: `Saved/Scenes/layout_62_66_v03_report.json`
- Stills: `Saved/Playblasts/Layout_62-66/stills/` (`v03_shot62`, `v03_shot63a`,
  `v03_shot64a`, `v03_shot64b`, `v03_shot65`, `v03_shot66a`, `v03_shot66b`;
  earlier `v02_shot63a` and `v9_*`/`final_*` stills are the v02 pass)
- Per-shot MP4s and the full cut: the **v02** files remain the last encoded
  review proxies (`…_v02.mp4`, `…_full_v02.mp4`); v03 playblasts are the next
  render after the GUI look pass.
- Build scripts: `Tools/build_layout_62_66_ref_v02.py`, `Tools/run_ref_v02.py`,
  `Tools/post_layout_ref_v02.py`, `Tools/build_layout_v03_polish.py`,
  `Tools/run_v03.py`, `Tools/fix_layout_materials.py`; the earlier native
  `Tools/build_layout_62_66_v2.py` remains as the v01 fallback.
- Renders were produced through the live **dcc-mcp-maya 0.9.45** session
  (`execute_python` + `render_sequence`), not hand-keyed in a Maya GUI.

## Known limitations / next pass

1. **Facial expression.** The David face renders with closed/neutral eyes in the close-ups;
   the eyelid/blendshape controls were not resolved in the headless session. 63B reads
   through the open jaw and body; 63A reads as a scowl/squint. A GUI pass should drive the
   eyelid controls and brows.
2. **Exterminator.** Primitive proxy only; replace with the real rig if one is supplied.
3. **Legs.** 64B now has an IK-leg cycle staged on `IKLegHandle_L/R`; tune contact
   and weight in the GUI before final animation.
4. **Materials.** Flat lambert layout materials were used for readability. Final beauty
   passes should use the film’s toon masters.
5. **Discord.** The desktop app is running, but this session had no computer-use tool and
   the window was occluded. The specs used here are the captured #layout findings from the
   prior Hermes session (naming convention `Lastname_Firstname_LayoutScene(#-#)_Initials`,
   playblasts to the group OneDrive folder, examples: Scenes 19–24 Emilio, 38–42 Pearl) plus
   storyboard Page 16. **Verify the #layout upload folder and naming in Discord before
   submitting.**

## Upload

Use the naming convention above. The v03 scene and v03 stills are ready under
`Saved/Scenes/` and `Saved/Playblasts/Layout_62-66/`. If the group wants
1920×1080, re-render the same cameras with `render_sequence` after the GUI look
pass (the 640×360 v02 MP4s are review proxies).
