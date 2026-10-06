# Toon masters plan — 2026-10-04

**What this is.** The forward plan for this project's master-material set: what exists, what
gets built next, and why the count is what it is. Written at the owner's request on
2026-10-04 23:48 EDT, after a search of `Docs/`, `specs/`, and the full git history
(`git log -S"10 masters" --all`, `-S"ten master"`) found **no document that ever stated the
planned master count** — the number lived only in conversation, which is the defect this file
closes.

**Division of labour with existing docs.** Live inventory and architecture belong to
`Docs/TOON_SPINE.md` (counts frozen 2026-10-04, `5f51b59`). This file is the forward plan and
the owner decision recorded.

**Owner decision (2026-10-04): Option 2, bounded.** One master per shading family whose
**band structure** must differ; tint/pattern/detail variation stays in material instances.
This closes the "Open decision: per-family Toon Profiles" in
`Docs/TOON_EXPANSION_2026-10-02.md` and supersedes the informal *"two masters" convention*
referenced there. Target set: **15 masters** (5 built, 2 code-ready, 8 new).

---

## 1. Most recent ANMN 304 class context (git + logs)

### Course state (from `Humber_FinalYear_Prep/`, live as of 2026-10-04 23:43)

| Fact | Value |
|---|---|
| Course | ANMN 304 Animation Art 5 (Jason Par), Fridays 8:30 AM, J117 |
| Weighting | Production Bible 30% · Production Meetings 30% · Final Project 40% |
| Gradebook | 80% as of the 10-01 sweep (Pitch 9/18 = 80/100 late; In Class 1 9/25 = 4/5 late) |
| **Production Bible** | **Due Thu 2026-10-09 — attempt 1 of 2.** 30% of the grade. Scaffold ready: `Submission_Set_2026-10-03/304_production_bible_SCAFFOLD.md` |
| In Class 2 (10/02) | **Past due, submission point unconfirmed** |
| In Class 3–7 | 10/16, 11/06, 11/20, 12/04, 12/11 |
| Final film | 2026-12-18 |
| Group | 14-person capstone, "Humber 3D Film" Discord; manifest name *Melodia Humber Toon Spine Capstone* |
| Same-week clash | ANMN 301 animatic also due **Fri 2026-10-09 17:00** (25%) — title/end card text fix pending (`ANMN301_Animatic/ANIMATIC_TEXT_FIX_2026-10-04.md`) |

**This plan is a graded input, not side work.** The owner is staging slot **09 — Toon Shader &
Surfacing Technical Artist** (`Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/02_Assets/Materials/M_slot09_manifest.txt`),
and Production Bible **§5 Pipeline and Workflow** is the owner's own section. Sections 5 and 6
of this document (build order, per-stage mechanics) are written to be pasted or linked from
that submission.

### Repo git context (40 commits, 2026-09-29 → 2026-10-04)

- **09-29** scaffold `5d09976` (master + 15 MF + 18 TP) → spine-from-code `3de66c6` →
  `MF_RampLUT` + `M_Outline_InvertedHull` `ef15225` → profiles+lookdev `3df13b2`.
- **10-01/02** canon 14-person pipeline `8c291be`; shadow-driven hatch `e1ef17e`;
  generated texture library `4748a6b`; office toon materials `8e15e1d`;
  brutalist import + **8-shot prototype render** `701c3b6`.
- **10-03** SDF stroke map, six wiring fixes, gouache rebuild + lookdev fixture, two domain
  masters + showcase instances, LFS art staging, **TP_Melusina/TP_Character authored**.
- **10-04** spine expansion `3e1ef1b` (unlit master builder, rim offset, office set),
  UDS gitignored `1c07db6`, merge union of D:/P: copies `0c58be4`, **character master binds
  TP_Melusina (code)** `220f084`, **verify_all 9/9** `dc8c874`, inventory counts corrected
  `5f51b59` (HEAD).

### Hermes logs

`.hermes/plans/` in BS_GodFile was searched: **0 hits** for `304 | toon spine | film-304`.
There has never been a hermes plan for this lane. The current class context lives in
`Humber_FinalYear_Prep/WEEKLY_LOG.md` (daily briefs) and `Submission_Set_2026-10-03/`.
This document is the first written plan for the film lane.

---

## 2. Verified inventory (2026-10-04, `git ls-files` + `verify_all`)

| Kind | Count | Names |
|---|---|---|
| Master materials | **5** | `M_Master_Toon_Universal`, `_Foliage`, `_Water`, `M_Outline_InvertedHull`, `M_PainterlyGouache` (+ `M_PainterlyGouache_Inst`) |
| Material functions | 5 | `MF_ColorRamp3`, `MF_RampLUT`, `MF_ProceduralPatterns`, `MF_PBRDetail`, `MF_RimOffset` |
| Toon profiles | 22 | incl. `TP_Melusina`, `TP_Default`, `TP_Water`, `TP_Foliage`, 9× `TP_Office_*` |
| Instances | 26 | `MI_Toon_*`, `MI_Foliage_*`, `MI_Water_*`, `MI_Outline_*` |
| Textures | 19 | ramps, hatch, SDF set, Gouache set |
| Gate | **9/9 PASS** | `Saved/Audit/verify_all_2026-10-04.txt`, run 23:18:11 |

**Code exists, asset does not (the two pending masters):**

1. `M_Master_Toon_Character` — `Python/build_master_toon_character.py` committed and
   registered in `build_spine.py`; binds the canonical `TP_Melusina` (`#352D40`), adds
   `MF_RimOffset`. **The headless run never happened**, so `Masters/M_Master_Toon_Character.uasset`
   does not exist and the `MI_Toon_*` character instances report a failure instead of picking
   up their profile (`Docs/TOON_SPINE.md` line 56 ff.).
2. `M_Toon_Unlit_Character` — `Python/build_m_toon_unlit.py` written (shadowless graphic
   route, no Substrate Toon BSDF, no TP by design) but **not registered in `build_spine.py`**
   and no `.uasset` anywhere on disk.

**Correction recorded on owner authority (2026-10-04): `M_Master_Nikki` is LIVE, not retired.**
`Docs/T3D_Baseline/material_catalog.json` in BS_GodFile carries a stale `note_retired`
(2026-09-05); the asset is present on disk
(`Content/EnvSandbox/Materials/M_Master_Nikki.uasset`) and "Nikki SHIP" landed 2026-09-23
(`c4d92bbb1`). It is a **live reference master** for this plan — as research input only (§6).

**Open gates** (from `specs/humber_toon_spine/melodia_intake_manifest.v1.json`, partially
resolved since it was written):

- ✅ mid-merge gate closed — merge landed in `0c58be4`, no unmerged paths remain, verify 9/9.
- ⏳ **intake route decision** still open: the 132-file raw Melodia drop under
  `Content/Materials/{Masters,Functions}` resolves 0/132 and is **not counted anywhere in this
  doc**. Owners chose A (vendor 218-pkg closure) / B (regenerate via builders) / C (defer).
  **This plan assumes route B for every master below**, which is already the established
  channel (`Docs/CONTENT_CONVENTIONS.md`).
- ✅ **editor** gate clear as of writing: no `UnrealEditor` process, port 9316 free — a
  headless build can run now. Single-editor rule still applies.

---

## 3. What actually sets the count

1. **A material instance cannot carry its own Toon Profile on this engine build** — measured
   (`TOON_EXPANSION_2026-10-02.md` §Open decision; `override_toon_profile` false everywhere).
   Every instance inherits the profile **its master** binds. Consequence: a family that needs
   different *band structure* needs its **own master**. That is why `M_Master_Toon_Character`
   exists as a second master rather than an instance (`build_master_toon_character.py` header:
   the whole 26-instance profile library was inert until a master bound `TP_Melusina`).
2. **Variation that is only tint / pattern / detail does NOT need a master** — that is what
   the 26 `MI_Toon_*` are for. A new master is justified only by a different light response.
3. **Assets are generated, never copied** — every master below is a `Python/build_*.py`
   registered in `build_spine.py` with a `verify()`, rebuilt headless, gated by
   `Tools/verify_all.ps1`. The 2026-09-29 cross-project copy that silently dropped all ten
   `MaterialFunctionCall` references is why this rule exists.
4. **Not one master per profile.** 22 `TP_*` do not imply 22 masters. `TP_Office_*` (9),
   `TP_Stone`, `TP_Gold`, `TP_Hatched`, `TP_TwoTone`, `TP_Cool`, `TP_Warm` differ mainly in
   tint/detail and stay inside their family's master until lookdev proves otherwise (§6).

**Test for adding a master:** *does this surface need a different response to light than the
masters that already exist?* If yes → new master. If no → an instance.

---

## 4. The recommended 15 masters for an indie film

Fifteen is the ceiling that keeps the set hand-buildable by one tech artist while covering
every shot and set in `specs/humber_toon_spine/humber_toon_spine_manifest.v1.json`
(SH010–SH080) and the brutalist exterior + office interior sets.

### Tier A — built and tracked (5)

| # | Master | Binds | Why it exists / shot evidence |
|---|---|---|---|
| 1 | `M_Master_Toon_Universal` | `TP_Default` | The spine: every opaque environment/prop surface with no better answer. 1,201-node reference implementation. |
| 2 | `M_Master_Toon_Foliage` | `TP_Foliage` | Masked two-sided cards + sway WPO — exteriors SH010–SH030. |
| 3 | `M_Master_Toon_Water` | `TP_Water` | Scrolling ripple normal; **SH030 water_rise** is a named shot. |
| 4 | `M_Outline_InvertedHull` | — (unlit) | Inverted-hull edge pass; the outline half of the style guide. |
| 5 | `M_PainterlyGouache` | — (no TP) | Opaque matte washes: granulation, edge bleed, paper tooth. Painted backdrops / lookdev family. |

### Tier B — code ready, generate next (2)

| # | Master | Binds | Why |
|---|---|---|---|
| 6 | `M_Master_Toon_Character` | `TP_Melusina` | Hero/NPC bodies; SH040 dialogue, SH050 macro, SH060 action. **Builder registered — one headless run away.** Unblocks the whole `MI_Toon_*` character family. |
| 7 | `M_Toon_Unlit_Character` | none, deliberately | Shadowless graphic route (Spice Frontier / `FILM_PIPELINE.md` §A7): no bands, no Lumen noise, no shadow acne — the cheapest insurance against cel-lighting failure modes. Needs registration in `build_spine.py` first. |

### Tier C — new, shot-critical (5)

| # | Master | Why it is its own master |
|---|---|---|
| 8 | `M_Master_Toon_Sky` | **SH010 opens on a silhouette against sky** and SH020 is atmospheric depth. A sky needs banded gradient + painted cloud bands + night/star field and must *not* inherit the key-light ramp an environment master gets. Vendored UDS (`Content/UDS*`) is the reference lighting, not the shading. |
| 9 | `M_Master_Toon_Landscape` | Ground planes, terrain, city ground for the brutalist exterior (SH010, SH030 ground contact). Height-blend/macro-variation response differs from a wall. Live Melodia references to research and regenerate: `M_Master_Toon_Landscape_HeightBlend`, `M_Master_Nikki_Landscape`, `M_Master_Nikki`. |
| 10 | `M_Master_Toon_Face` | SH050 grades on "eyes, warm-violet halftone shadow ramp, micro-expressions". Skin wants a terminator-independent ramp (the anime trick: the face shadow does not pop as the head turns) while the body stays banded. Only possible as its own master — instances cannot carry a profile. |
| 11 | `M_Master_Toon_Hair` | Translucent gradient + wind response + depth fade; hair is the most common toon artifact (shadow terminator across strands). References: `MF_ClothWindDrape`, `MF_AnimeSkinWrap` (Melodia, live). |
| 12 | `M_Master_Toon_Glass` | `BR_CITY_TOWERS_GLASS`, office glazing, facades. Must preserve band structure through refraction + its own specular ramp; default glass in a cel frame reads as Lumen mush. |

### Tier D — new, VFX and finish (3)

| # | Master | Why |
|---|---|---|
| 13 | `M_Master_Toon_EmissiveFX` | SH070 **song_release / cymatic fabric flow**, night windows, rhythm pulses. Absorbs the Melodia audio-reactive idea (`M_AudioReactive_BaseMaster`, live) as a parameter-driven pulse — glow that rides a beat, not a second combat system. |
| 14 | `M_Master_Toon_Particles` | Niagara sprites/flipbooks need a toon response too: sparkle, stardust, rain. SH010 atmosphere and SH070 both need them; flat unlit sprites break the frame. |
| 15 | `M_Master_Toon_PostComposite` | MRQ finishing only: grade, halftone/grain, vignette. **Explicitly not banding** — bands stay material-side because post-process cel shading quantizes finished pixels and fights fog/bloom (`FILM_PIPELINE.md` §Why UE 5.8 Toon, point 5). Build only if the compositing lane wants it in-engine; Blender VSE is the fallback. |

**Deferred, deliberately:** an Office/Interior master (the 9 `TP_Office_*` ride on instance
tints until lookdev shows the shared band structure is wrong — there is still *no lookdev
capture* of the office surfaces per `TOON_EXPANSION_2026-10-02.md`); a Props/Metallic master
(`MF_PBRDetail` is instance-reachable); per-profile masters for `TP_Stone/Gold/Hatched/TwoTone`.

---

## 5. Build order and mechanics

### Phase A — clear the debt first (editor is free now)

1. Run `Python/build_master_toon_character.py` headless (registered, has its own `verify()`).
2. Register `build_m_toon_unlit` in `build_spine.py`'s materials loop with its own expected
   calls / `min_expressions` (its `verify()` already asserts **no** TP is bound — keep that).
3. Full `build_spine.py` rebuild → expect **7 masters** verified (5 tracked + character +
   unlit). `Docs/TOON_SPINE.md` still reports the last build as 4/4 masters — reconcile that
   line in the same change.
4. `Tools/dogfood_toon_spine.py --all` and `Tools/verify_all.ps1` (must stay 9/9), then commit.

### Phase B — shot-critical new masters (SH010, SH030, SH050)

`M_Master_Toon_Sky` → `M_Master_Toon_Landscape` → `M_Master_Toon_Face` → `M_Master_Toon_Glass`.
Sky first: shot 1 is the film's first image.

### Phase C — character polish and finish

`M_Master_Toon_Hair` → `M_Master_Toon_EmissiveFX` → `M_Master_Toon_Particles` →
`M_Master_Toon_PostComposite` (last, optional).

### Per-master checklist (from repo convention — do not shortcut)

1. New `Python/build_master_toon_<family>.py` on `spine_lib.py` helpers, with its own
   `verify()`; bind its `TP_*` at the **end** of the build (the character/water pattern).
2. Register in `build_spine.py` materials loop with expected `MaterialFunctionCall`s and a
   realistic `min_expressions` (see the outline entry: thresholds are matched to what the
   builder actually produces, not to wishful numbers).
3. Add the family's `MI_*` rows in `build_instances.py` (instances inherit the master's
   profile — that is the whole point of the master).
4. Regenerate `Docs/ASSETLIST.md` — **it is stale today**: `M_PainterlyGouache` reports
   "UNKNOWN — not generated by any builder" although `build_gouache_material.py` exists, and
   the three `M__Probe_*` entries are leftovers.
5. Run `Tools/dogfood_toon_spine.py --all` + `Tools/verify_all.ps1`; commit builder + asset +
   audit together.

### Known defects to clear while in here

- **Outline line-weight fix is not in the spine** — `build_spine.py` notes the
  screen-space distance-compensation chain was dropped when `build_m_outline.py` was
  rewritten and "needs re-applying" (`FILM_PIPELINE.md`).
- `M_PainterlyGouache` and `M_Toon_Unlit_Character` are built outside the `build_spine.py`
  stage list — fold them in so one command rebuilds the whole spine.
- Office surfaces have never been looked at (structure verified by read-back only).
- The 132-file Melodia drop sits untracked; leave it there until the intake route is chosen
  (§2).

---

## 6. Non-goals

- **No raw `.uasset` intake from Melodia.** Binary copies keep their `/Game/...` paths —
  0/132 resolve; the dependency closure is 218 packages / 89 MB. Research the live Melodia
  masters (Nikki, Landscape, audio-reactive, anime-wrap) and **rebuild through Python**.
- **No hand-edited graphs.** `CONTENT_CONVENTIONS.md`: change the builder, rebuild.
- **No second master just to hold a profile** whose only difference is tint/pattern.
- **No parallel master system in Blender/Houdini** — masters are UE materials; the Blender
  fork owns geometry only (`Docs/BRUTALIST_SET.md`).
- **No claim of lookdev.** Structure and bindings are read-back verified; nothing in Tier C/D
  has been *seen* until a capture exists.

---

## 7. Evidence

| Claim | Source |
|---|---|
| 5 / 5 / 22 / 26 / 19 inventory | `git ls-files Content/Materials/*`, `Docs/TOON_SPINE.md` (`5f51b59`) |
| verify_all 9/9 at 23:18 | `Saved/Audit/verify_all_2026-10-04.txt` (`dc8c874`) |
| character master = code only | `Docs/TOON_SPINE.md` §pending; `Masters/` directory listing |
| unlit builder unregistered | `rg "unlit" Python/build_spine.py` → 0; no `*Unlit*` file under `Content/` |
| instance cannot carry a profile | `Docs/TOON_EXPANSION_2026-10-02.md` §Open decision |
| Nikki is live | `Content/EnvSandbox/Materials/Masters/M_Master_Nikki.uasset` on disk; BS_GodFile `c4d92bbb1` "Nikki SHIP" |
| no prior 10-master plan anywhere | `git log -S"10 masters" --all` (0), `rg` over `Docs/ specs/ .hermes/` (0) |
| class dates | `Humber_FinalYear_Prep/WEEKLY_LOG.md` (2026-10-04), `304_production_bible_SCAFFOLD.md` |
| owner role | `Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/02_Assets/Materials/M_slot09_manifest.txt` |
| shot deck SH010–SH080 | `specs/humber_toon_spine/humber_toon_spine_manifest.v1.json` |
