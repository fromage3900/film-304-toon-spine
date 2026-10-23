# Shot composition & scenery plan — Office Spider (2026-10-17)

Focus: mesh placement and scenery first, before rig/animation/camera polish.
This document converts the storyboard groups (`SB_OfficeSpider_notes.md`) and
`Docs/OFFICE_SPIDER_SHOT_PLAN.md` into a set-by-set staging plan. Every set
below has (or will have) a JSON spec + builder following the
`specs/office_spider/*_stage.v1.json` + `Python/build_*_scene.py` pattern.

## Set inventory

| Set / level | Status | Shots | Builder |
|---|---|---|---|
| Exterior vista — `L_Toon_Shot_Env` | READY | SH010 | `Python/compose_shot_env_level.py` |
| Office interior — `L_Toon_Shot_Office` | READY (SH020–SH060) | SH020–SH060 | `Python/build_shot_stage.py` |
| Break room — `L_Toon_Shot_BreakRoom` | READY (SH090/100/110) | SH090, SH100, SH110 | `Python/build_breakroom_scene.py` |
| Hallway connector — `L_Toon_Shot_Hallway` | NEW (this pass) | SH050, SH080, SH041, SH046, SH047 (+14, 18 reuse) | `Python/build_hallway_scene.py` |
| Kitchen build-out | FOLDED INTO BREAK ROOM | SH090, SH100, SH110, 13, 17, 24–27, 48, 64, 69 | `build_breakroom_scene.py` |

## Storyboard group → set → scenery

### Page 1 — Establishing & setup
| Board shot | Expanded shot | Set | Key scenery / meshes | Notes |
|---|---|---|---|---|
| 1 establish zoom | SH010 | Exterior | brutalist office block, stone, sky | already staged |
| 2–3 typing TAP | SH020 | Office | Canonical cubicle, desk, partitions, lamp, papers, chair | worker rig pending |
| 3 paper/scratch/beep/stretch | SH030–SH050 | Office → Hallway | paper piles, sticky notes, calendar | papers already placed |
| 4 desk + calendar ECU | SH060 | Office | partition supplies region, sticky notes | 85mm macro |
| 5 faces annoyed→excited | SH060 (face) | Office | face macro, no new scenery | rig bind |
| 6 chair/stand/carry/walk | SH050–SH080 | Office → Hallway | chair, bins, doors, frosted glass | hallway set new |
| 7 hallway/kitchen BANG/THUMP | SH090 | Break room | counter, cabinets, fridge, espresso machine | break room ready |

### Page 2 — Disruption & search
| Board shot | Expanded shot | Set | Key scenery / meshes | Notes |
|---|---|---|---|---|
| 8 wide break room | SH090 | Break room | full counter run, shelf, pastry dome | camera placed |
| 8 under counter BANG | SH090 | Break room | counter underside, floor | rig |
| 8 wide after bang | SH090 | Break room | same | camera impulse |
| 8 react THUMP | SH090 | Break room | same | Eyes throb |
| (carry tracks) | SH014, SH018 | Hallway | mug in hand, floor carpet | mug material gap |
| (mug shelf) | SH025 | Break room | shelf, mug | mug gap |

### Page 3 — Confrontation & reveal
| Board shot | Expanded shot | Set | Key scenery / meshes | Notes |
|---|---|---|---|---|
| 9 breath in/out | SH090 (face) | Break room | face macro, no new scenery | rig |
| 10 hallway shadow step | SH080 | Hallway | dark corner, spider rim | lighting |
| 11 counter/lean/button | SH100 | Break room | espresso machine hero, mug, hand ECU | mug gap |
| 12 pan + spider reveal | SH110 | Break room | counter run, spider R, worker L | money shot, rig |

## Mesh placement rules (scenery-first)

1. **One set per level.** Do not dress a map by hand; every placement lives in a
   `*_stage.v1.json` spec and is applied by its builder. Re-running a builder
   removes only its owned actors (by prefix), so iteration is safe.
2. **Grounding.** Floor top face at z=0; every sits-on prop has `sits_on` and a
   measured base offset (see break room spec for the pattern). `ground_correction`
   is auto for props, skip for slabs.
3. **Overlap declarations.** Any prop whose AABB intersects a wall or cubicle
   carries `overlap_ok_with` so the verifier does not flag it.
4. **Bounds verification.** Builders read back world AABBs against `room_bounds`;
   a prop outside the room fails the report.
5. **Camera aim.** Every camera declares `aim_at`; the verifier asserts
   `forward · aim >= 0.9`. Transposed pitch/yaw is the failure mode this
   guards against.
6. **Materials are assigned in the builder** (slot 0) from the spec's `material`
   field, not hand-painted in the editor.

## Hallway set (new this pass)

Level: `/Game/Maps/L_Toon_Shot_Hallway`  
Spec: `specs/office_spider/hallway_stage.v1.json`  
Builder: `Python/build_hallway_scene.py`

Scenery placed:
- Floor (VCT) + centre carpet runner
- Left/right walls + baseboards
- Drop ceiling (gall)
- Office door + break-room door (frosted glass)
- Two troffer emissive slabs
- Wall sign (whiteboard)

Cameras: `Cam_HW_SH050`, `Cam_HW_SH080`, `Cam_HW_SH046`, `Cam_HW_SH041`,
`Cam_HW_SH047`. Aim verified against their declared targets.

## Still-open scenery gaps

| Gap | Owner | Notes |
|---|---|---|
| Mug ceramic instance | toon lane | 1 builder row; blocks SH010? no — SH013/14/20/22/25/45 |
| Flyswatter grid red | toon lane | 1 row; blocks Act III |
| Blinds instance | toon lane | window walls |
| Shoes dark leather | toon lane | SH039 |
| Spray can + cap | toon lane | Act V |
| Broom handle | toon lane | Act V |
| Water streak particles | toon lane | SH067 |
| Fire glow cards | toon lane | SH069 |
| Boss suit dark | toon lane | SH070/72 |
| Kitchen/hallway build-outs | owner + toon | hallway now staged; kitchen folded into break room |
| Boards 31–32 | Jeffrey Dawn | drawer walk between SH030/33 |
| Rig binds (worker/spider/coworker) | owner | critical path; scenery is ready ahead of it |
| MRQ presets | owner | final-render gate |

## Recommended execution order (scenery first)

1. Run `build_hallway_scene.py` to create `L_Toon_Shot_Hallway` and verify the report.
2. Re-run `build_breakroom_scene.py` and `build_shot_stage.py` to confirm all three
   sets are green (no dirty-map modal; save first).
3. Close material gaps 1–10 in one `build_instances.py` pass, then re-verify.
4. Only after scenery + materials are green, bind rigs and place cameras for the
   deferred shots (SH070–SH120).
5. MRQ presets last.