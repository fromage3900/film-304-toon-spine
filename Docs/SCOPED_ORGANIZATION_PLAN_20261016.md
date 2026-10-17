# Scoped organization plan — Film 304 toon pipeline (2026-10-16)

This plan supersedes ad-hoc lane notes for day-to-day execution. It keeps the
project scoped to **one accepted Dana action shot first**, then Act I–II
porcelain, then full-act renders. It reviews the existing storyboard and shot
criteria and converts them into an executable, gated plan.

## 1. Scope decision

Primary production: **Office Spider** (73 boarded shots, 3-act comedic short).

Secondary track: **Universal Film / Dana lookdev** — lighting templates and
rig validation only. It must not expand into a second film until the Dana gate
passes.

Out of scope until the Dana gate passes:

- adding new material masters or profiles
- new environment families
- final renders for Acts III–V
- any change that requires a new rig contract

## 2. Storyboard review

Source: `Humber_FinalYear_Prep/.../Storyboard/SB_OfficeSpider_notes.md`
(Artist: Jeffrey Dawn, 2026-10-05, 3 pages, hand-drawn pencil thumbnails)

Findings:

- The storyboard is **three pages, three acts**, with a clear comedic arc:
  mundane routine → disruption → confrontation.
- The "Donut Day" calendar is the central dramatic-irony motif and is correctly
  carried into the shot plan (shot 4/6 ECU).
- Sound design is part of the boards (TAP, BEEP, BANG, THUMP, Dish Clanks,
  Coffee Machine Buzzing). The shot plan maps several of these to material
  dials (troffer buzz, screen throb, coffee lamp).
- The notes use **sequence-group shot numbers** (1–12 per page), not unique
  shot IDs. The expanded 73-shot plan in `Docs/OFFICE_SPIDER_SHOT_PLAN.md`
  is the authoritative shot list; the storyboard is the creative source, not
  the shot database.
- Boards 31–32 are missing (page 8 ends at 30, page 9 opens at 33). The plan
  assumes a drawer walk between shots 30 and 33. This is an open creative gap
  owned by Jeffrey Dawn.
- No storyboard panel exists for the 15-minute-later card (shot 65) beyond a
  full-frame card; that is acceptable as a title card.

Conclusion: the storyboard is strong and sufficient for production. The main
risk is **shot-count inflation** (12 board groups → 73 shots). Keep the 73-shot
plan as the working list, but do not add shots without a board or a documented
narrative reason.

## 3. Shot criteria review

Source: `Docs/OFFICE_SPIDER_SHOT_PLAN.md` + `Docs/MRQ_RENDER_GATE.md`

Existing criteria are good and should be enforced as written:

- Every shot maps to exact `MI_*` / `TP_*` / `T_SDF_*` assets.
- `(GAP)` marks are owner decisions, not placeholders invented by the planner.
- Global render stack is single-writer (one post-composite, one outline rule,
  one troffer buzz, one screen throb).
- Per-shot rows only list what changes.
- MRQ presets are the final-render gate (currently not started).

Reviewed gaps and their current status:

| # | Gap | Status |
|---|---|---|
| 1 | Mug ceramic | Instance exists (`MI_OfficeSpider_Mug`) |
| 2 | Flyswatter grid red | Instance exists (`MI_OfficeSpider_Swatter`) |
| 3 | Blinds | Instance exists (`MI_OfficeSpider_Blinds`) |
| 4 | Shoes dark leather | Instance exists (`MI_OfficeSpider_Shoes`) |
| 5 | Spray can + cap | Instances exist (`MI_OfficeSpider_SprayCan`, `SprayCap`) |
| 6 | Broom handle | Instance exists (`MI_OfficeSpider_BroomWood`) |
| 7 | Water streak particles | Instance exists (`MI_OfficeSpider_Sprinkler`) |
| 8 | Fire glow cards | Instance exists (`MI_OfficeSpider_FireGlow`) |
| 9 | Boss suit dark | Instance exists (`MI_OfficeSpider_BossSuit`) |
| 10 | Rage-eyes + soaked-floor Wetness | Override rows exist in `build_pattern_overrides.py` |
| 11 | Worker + spider + coworker rig binds | **Open — critical path** |
| 12 | Kitchen/hallway set build-outs | **Open** |
| 13 | Boards 31–32 | **Open — creative** |
| 14 | MRQ presets | **Open — now specified in `Docs/MRQ_PRESETS_BY_ACT.md`** |

Conclusion: material definitions are ahead of geometry/rig assignment. The next
bottleneck is rig bind and set build-out, not materials.

## 4. Organization (owners and lanes)

| Lane | Owner | Scope |
|---|---|---|
| Unreal editor / materials | Luna | Material masters, instances, lookdev levels, MRQ |
| Maya/Houdini export | This chat | Dana v08, future rig exports |
| Blender set / brutalist | Set owner | Building kit, dials, drift checks |
| Storyboards | Jeffrey Dawn | Boards 31–32, shot additions |
| Source control | SCM (this agent) | Commits, tags, branch hygiene, gate runs |

Rules:

- One editor per file.
- Generated assets are never hand-edited.
- No `Save All` without checking dirty maps.
- No commit/push of rig source or candidate FBXs (single-user licensing).

## 5. Phases and gates

### Phase 0 — Checkpoint (done)

- Tag: `dana-runbook-20261016`
- Runbook: `Docs/DANA_ACTION_SHOT_RUNBOOK.md`
- MRQ gate: `Docs/MRQ_RENDER_GATE.md`

### Phase 1 — Dana gate (critical path)

Deliverable: one accepted, grounded, UDS-lit Dana action shot.

Gate: all items in `Docs/DANA_ACTION_SHOT_RUNBOOK.md` §7.

Abort conditions: missing render meshes, missing morph channels, T-pose
fallback, body/lash loss, sliding, clipping, darkness, Sparrow contamination.

### Phase 2 — Act I–II porcelain pass

Deliverable: shots 1–23 rendered through proto MRQ presets with correct
surfaces and shakeout (not performance).

Gate: `Docs/MRQ_RENDER_GATE.md` proto-level checks for each shot.

### Phase 3 — Priority tuning

Targets: shots 21, 38, 55, 72 (spider macros, rim/halo tuning on white
ceiling vs dark corner).

### Phase 4 — Full acts

Deliverable: Acts III–V proto passes, then final passes after all gaps close.

Gate: no final preset until proto pass and gap closure.

## 6. Immediate next actions (in order)

1. Refresh quota and coordinate editor lease with Luna.
2. Verify v08 hash and read the three Dana reports.
3. Import v08 into `/Game/Staging/DanaFilmRuntime_20261016` (single import).
4. Run Unreal deformation checks.
5. Retarget one Sparrow clip onto Dana.
6. Assign materials and compose one grounded shot.
7. Render through a proto MRQ preset and fill `Docs/SHOT_EVIDENCE_TEMPLATE.json`.

## 7. Risks to watch

- Scope creep across two productions (Office Spider vs Universal Film).
- Shot-count inflation beyond boarded groups.
- Experimental Substrate parameter drift.
- Repository hygiene under multi-user binary assets.
- Treating preview/intake assets as final shaders.

## 8. Success definition

This project is "on track" when:

1. The Dana gate passes with evidence files.
2. Act I–II has proto renders for every shot.
3. No shot is marked final without an MRQ preset and a passing checklist.
4. The repo gate (`Tools/verify_all.ps1`) is green on the working branch.
