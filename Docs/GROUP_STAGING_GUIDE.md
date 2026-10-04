# Humber Capstone Pipeline — 14-Person Group Staging Guide

This guide establishes the hardened git workflow, asset naming, camera framing, and dogfooding standards for our 14-person Humber AN311 Capstone & Toon Spine project.

---

## 1. Golden Rules for Collaborators

1. **Always Pull Before You Stage:**
   Run git verification before and after pulling to ensure your local working copy matches upstream.
2. **Never Directly Push to `main`:**
   All work must be authored on a feature branch (`feature/<slot-or-role>-<task>`) and pushed through a reviewed Pull Request.
3. **Strict LFS Tracking:**
   All binaries (`.blend`, `.fbx`, `.png`, `.exr`, `.uasset`, `.umap`, `.mp4`, `.wav`) MUST be tracked with Git LFS. The pre-commit hook will reject commits containing un-tracked large files (>50MB) or forbidden temp files (`.blend1`, `.blend2`, `.zip`, `.tmp`, `0-byte` files).
4. **Naming Discipline:**
   Every asset staged into `02_Assets/` or scene into `03_Scenes/` must have a proper prefix (`CH_`, `PR_`, `EN_`, `RIG_`, `MI_`, `TP_`, `SC_`), version number (`_v01`, never `final_final`), and no spaces.

---

## 2. The 14 Team Roles & Staging Slots

| Slot # | Team Member Role | Dedicated Directory | File Prefix | Allowed Formats |
|---|---|---|---|---|
| **01** | Director & Script/Beat Lead | `01_Preprod/Story/` | `DOC_`, `STORY_`, `BEAT_` | `.md`, `.txt`, `.pdf` |
| **02** | Storyboard & Animatic Artist | `01_Preprod/Storyboard/` | `SB_`, `PNL_` | `.png`, `.blend`, `.mp4` |
| **03** | Concept Art & Visual Reference Lead | `01_Preprod/References/` | `REF_`, `CON_` | `.png`, `.jpg`, `.pdf` |
| **04** | Hero Character Modeler | `02_Assets/Models/Characters/` | `CH_` | `.blend`, `.fbx` |
| **05** | Environment & Architecture Modeler | `02_Assets/Models/Environments/` | `EN_` | `.blend`, `.fbx` |
| **06** | Key Props Modeler | `02_Assets/Models/Props/` | `PR_` | `.blend`, `.fbx` |
| **07** | Character Rigger (Body & Face) | `02_Assets/Rigs/Character/` | `RIG_CH_` | `.blend`, `.fbx` |
| **08** | Prop & Mechanical Rigger | `02_Assets/Rigs/Props/` | `RIG_PR_` | `.blend`, `.fbx` |
| **09** | Toon Shader & Surfacing Tech Artist | `02_Assets/Materials/` | `M_`, `MI_`, `TP_`, `T_` | `.uasset`, `.blend`, `.png` |
| **10** | Lead Character Animator (Acting/Dialogue) | `03_Scenes/Animation/Acting/` | `SC_ACT_` | `.blend` |
| **11** | Action & Camera Layout Animator | `03_Scenes/Animation/Action/` | `SC_ACTN_` | `.blend` |
| **12** | Lighting & Lookdev Artist | `03_Scenes/Lighting/` | `LGT_` | `.blend`, `.uasset` |
| **13** | VFX & Compositing Artist | `04_Renders/Compositing/` | `FX_`, `COMP_` | `.blend`, `.png`, `.exr` |
| **14** | Editor & Soundtrack Coordinator | `05_Edit/Sequences/` | `ED_`, `VSE_`, `AUD_` | `.blend`, `.mp4`, `.wav` |

---

## 3. Camera Framing & Toon Spine Specifications

All shot staging in Blender and Unreal Engine must conform to the project's canonical camera framing:

- **Format:** 1920x1080 (16:9), 24.0 fps. (Portfolio sheet cards use 1600x2000).
- **Safe Zones:** Keep critical acting within Action Safe (93%) and typography/dialogue within Title Safe (90%).
- **Rule of Thirds / Eye Line:** Melusina / character eye lines should anchor at $y \approx 0.618$ (the upper third horizontal guide).
- **Floor Grounding:** Feet/boots must remain grounded against `Studio_FloorCard` ($Z = -0.2935$ in staging blends). Never move the floor card to fit the model.
- **Toon Shading Ramp:** Shading must reference `TP_Melusina` with the anime shadow warm-violet ramp (`#352D40`), preserving halftone transitions without banding.

### Shot Deck Reference (60-90s Animatic & Sequence Spine)

| Shot ID | Shot Name | Camera Name | Focal Length | Framing Intent |
|---|---|---|---|---|
| `SH010` | `establish_world` | `Cam_Turntable.001` | 24mm | Extreme wide world vista, silhouette against sky |
| `SH020` | `reveal_profile` | `Cam_Back` | 35mm | Wide follow profile, atmosphere depth |
| `SH030` | `water_rise` | `Cam_Low` | 28mm | Low angle hero vista, ground contact and wave flow |
| `SH040` | `dialogue_medium` | `Cam_Beauty` | 50mm | Medium shot (waist up), clear hands & expressions |
| `SH050` | `macro_emotion` | `Cam_Macro` | 85mm | Close-up on face/eyes, toon halftone ramp readability |
| `SH060` | `hero_rig_action` | `Cam_Front` | 50mm | Dynamic performance with matched AE/music beats |
| `SH070` | `song_release` | `Cam_Turntable` | 40mm | Orbiting camera, cymatic fabric flow & audio sync |
| `SH080` | `bow_finale` | `Cam_Beauty` | 50mm | Medium full shot resolving to title card (≤3 dissolves) |

---

## 4. How to Verify Your Assets (Dogfood Testing)

Before submitting a Pull Request, run the automated verification suite:

```bash
# Run Git & Repository Consistency Check
python Tools/verify_git_consistency.py

# Run Dogfood Tests on Staged Assets and Shot Deck
python Tools/dogfood_toon_spine.py --verbose

# Run Everything Together (Full Suite)
python Tools/dogfood_toon_spine.py --all
```

If any check reports **FAIL**, resolve the issues (e.g. rename asset to follow conventions, track large files with LFS, or remove 0-byte files) before committing.
