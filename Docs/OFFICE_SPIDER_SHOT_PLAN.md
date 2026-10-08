# Office Spider — full render shot plan (materials-realized)

**Written 2026-10-06, branch `feat/office-spider-toon`.**
Boards: `Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/01_Preprod/Storyboard/`
`SB_OfficeSpider_Page{1-17}.png` + `SB_OfficeSpider_notes.md` (Jeffrey Dawn,
2026-10-05, shots 1–73). Sequences on disk (owner in-progress, untracked):
`Content/Sequences/OfficeSpider_Master` + `SH010`–`SH120`.
Material release: commit `94dc94e` — 41 instances / 31 profiles / 27 textures /
19 pattern cells, all built and read-back verified (see `Docs/TOON_SPINE.md`).

## How to read this plan

- **Seq** = owner's `SH*` sequence where one exists; `—` means unassigned,
  proposed in brackets.
- **Materials** name the exact realized `MI_*` / `TP_*` / `T_SDF_*` / cell.
  Anything with **(GAP)** has no realized asset — it is an owner decision,
  not a placeholder I invented.
- **DP dials** ride `Python/build_pattern_overrides.py` (instance-level,
  applied after instances, read-back verified). New dial rows follow the
  same file — never hand-edit an instance.
- Render stack is global (§1). Per-shot rows only list what CHANGES.

## 1. Global render stack (every shot)

| Layer | Asset | Notes |
|---|---|---|
| Grade | `MI_Toon_PostComposite` on `M_Master_Toon_PostComposite` | the one shared writer (grain 0.08, vignette 0.35). No second grade. |
| Outlines | `MI_Outline_Thin` characters/props, `MI_Outline_Heavy` architecture | inverted hull; line-weight rule in `CONTENT_CONVENTIONS.md`. |
| Troffer buzz | `MI_Toon_Office_Troffer`: FlickerRate 9.0 / Depth 0.06 | fluorescent hum under every interior (SFX-motivated, barely visible). |
| Screens | `MI_Toon_Office_Screen`: FlickerRate 3.0 / Depth 0.08 | monitor idle throb (beeps, p1-3). |
| Spider corner push | `MI_OfficeSpider_SpiderBody`: Rim 0.85, Lift 0.04; `MI_OfficeSpider_SpiderEyes`: FlickerDepth 0.45 | p12-2 dark-corner + thump-panel reads. |
| Coffee lamp | `MI_OfficeSpider_CoffeeMachine`: Emissive 1.5, Flicker 11.0/0.12 | amber buzz lamp ON for pour shots. |
| Levels | `L_Toon_Shot_Env` (shot composer) + `L_Brutalist_Layout` (review grid) | new set builds go through `compose_shot_env_level.py`, not hand-dressed maps. |
| MRQ presets | **(GAP)** | `ASSETLIST.md` "not yet started" — final-render gating item. |

## 2. Act I — Mundane routine (shots 1–12)

| Shot | Seq | Set / camera | Hero materials | Status |
|---|---|---|---|---|
| 1 establish, slow zoom | SH010 | brutalist exterior, 24mm wide | `MI_Toon_Environment`, `MI_Toon_Stone`/`CrackedStone` (`T_SDF_Cracks`), `MI_Toon_Sky`, Heavy outlines | READY (kit in `Content/Environment/Brutalist/`). |
| 2–3 typing TAP | SH020 | Canonical cubicle, OTS desk | partitions `MI_Toon_Office_Polypropylene`, desk `MI_Toon_Office_Laminate`, frames `MI_Toon_Office_PowderCoat` (`T_SDF_Cross`), carpet `MI_Toon_Office_Carpet` (`T_SDF_CarpetLoop`), ceiling `MI_Toon_Office_DropCeiling` (`T_SDF_CeilingTile`); worker shirt `MI_OfficeSpider_WorkerShirt` + Face/Hair/Glass masters; laptop screen `MI_Toon_Office_Screen` | READY except worker/spider rigs (owner staged 2 rigs — bind pending). |
| 3 paper/scratch/beep/stretch | SH030–SH050 | same, insert Papers | papers `MI_OfficeSpider_Paper` (`T_SDF_PaperGrain`, bMatteFinish) | READY (paper prop: staged `SM_Paper_PMB` — assign on import). |
| 4 desk + calendar ECU | SH060 | macro 85mm: calendar, cat photo, supplies | calendar/poster = Paper; donut-box note = `MI_OfficeSpider_DonutBox` (`T_SDF_Cardboard`) | READY. |
| 5 faces annoyed→excited | (SH060) | face macro, lifted specular | `TP_Face` + `MI_Toon_Face` (terminator holds on turns by design) | READY on rig bind. |
| 5–6 chair/stand/carry/walk | SH050–SH080 | cubicle→hallway, track | chair/bins polypropylene; hallway carpet, walls Environment, doors + `MI_OfficeSpider_FrostedGlass` (door glazing) | READY; hallway build-out queued (§5). |
| 7 hallway/kitchen BANG/THUMP | SH090 | break room wide | counters laminate, appliances `MI_OfficeSpider_CoffeeMachine` (`T_SDF_Brushed`), VCT floor (`T_SDF_VCT`), backsplash CellIndex 13 SubwayTile, steel dark | READY; kitchen build-out queued. |
| 9 breath in/out | (SH090) | face macro | Face master + shadow-lift via key light (no new asset) | READY on rig bind. |
| 10 hallway shadow step | (SH080) | practical dark corner | SpiderBody rim+lift carry the corner (see §1) | READY. |
| 11 counter/lean/button | SH100 | coffee machine hero, hand ECU | CoffeeMachine (lamp ON) + `T_SDF_Brushed`; mug **(GAP — ceramic instance, 1 row in `build_instances.py`)** | READY except mug. |
| 12 pan + spider reveal | SH110 | wide, worker L / spider R dark | SpiderBody + SpiderEyes (throb), buzz lamp flicker as motivated light | READY on spider rig. **Money shot — rim 0.85 is sized for it.** |

## 3. Act II — Coffee and consequences (shots 13–23)

| Shot | Seq | Set / camera | Hero materials | Status |
|---|---|---|---|---|
| 13 pour + TING | (SH100) | machine + mug ECU | CoffeeMachine lamp + SteelDark hatch; mug (GAP, same as above) | READY except mug. |
| 14 carry + TINK | — | hallway track | mug in hand; floor carpet | READY except mug. |
| 15 happy→sad faces | — | face ECU pair | Face master | READY on rig bind. |
| 16 empty box + "OUT FOR MORE!" | — | box macro, note insert | DonutBox + Cardboard map; note = Paper (bMatteFinish) | READY (box prop: staged `conteiner_box` — verify scale on import). |
| 17 angry + pour + place | — | kitchen, harder key | same as 13 + `TP_SteelDark` extinction does the mood work (no new light rig) | READY. |
| 18 carry/turn/return | — | hallway reverse track | same kit as 5–6 | READY. |
| 19 desk + laptop + spider looming | — | OTS wide, spider bokeh behind | Screen flicker up (DP row: Depth 0.12 for this beat); SpiderBody rim separates from dark | READY on rigs. |
| 20 typing + sip | — | desk medium | mug (GAP); Screen; Paper stack | READY except mug. |
| 21 floor corner zoom + spider ECU | — | floor macro → face macro | VCT grout (CellIndex 1 Checker pairs it); SpiderEyes throb 0.45 for the cute-eyes beat (throb reads as blink-curious at macro) | READY on spider rig. |
| 22 mug + shoulder spider + recoil | — | handheld shake | mug (GAP); WorkerShirt rim 0.30 holds him against the dark | READY on rigs. |
| 23 stand CLANK + exit | — | chair + floor | PowderCoat chair legs (Cross map); VCT | READY. |

## 4. Act III — The hunt (shots 24–30, 33–46)

> **Boards 31–32 have no panels** (page 8 ends at 30, page 9 opens at 33).
> Assumed: worker retrieves the swatter between 30 and 33 (drawer beat is
> shot 28 — the plan treats 31–32 as the drawer walk, to be boarded).

| Shot | Set / camera | Hero materials | Status |
|---|---|---|---|
| 24 kitchen + flex | kitchen medium | CoffeeMachine, SteelDark, VCT | READY. |
| 25 mug shelf (red marks) | shelf insert | mug (GAP); shelf laminate | READY except mug. |
| 26 crash/clank/smash struggle | kitchen handheld | SpiderBody gloss (Rough 0.35) + Eyes throb; EmissiveFX available for impact glints (unlit, Time/Sine pulse) | READY on rigs. |
| 27 counter slam | counter top | laminate mid-sheen | READY. |
| 28 drawer + swatter SHUCK | drawer macro | drawer PowderCoat; swatter **(GAP — gridded red plastic: 1 instance row, kraft-red tint on Universal + CellIndex 9 Grid)** | Swatter instance queued (§5). |
| 29 under-desk hide + approach + grab | under-desk low | carpet dark + ShadowLift 0.02 keeps pile off black; spider rim | READY on rigs. |
| 30 confident swatter | medium, low key | swatter (GAP, same row); WorkerShirt | READY on rig bind. |
| 33 floor corner marks | floor insert, red marks | VCT + EmissiveFX red tick marks (unlit pulse, Depth 0 — steady) | READY. |
| 34 stalk → scare → panic | handheld | Face + Eyes | READY on rigs. |
| 35 floor chase ×4 | top-down track | VCT grout grid tracks the spider path (grout reads at top-down) | READY on spider rig. |
| 36 under-desk + spider enters | low | carpet + rim | READY. |
| 37 look-down + spot | tilt-down | Face; floor cornerPractical dark | READY. |
| 38 spider closeup | macro, grazing key | SpiderBody gloss + hatch (Diagonal) + Eyes 2.0 | READY on spider rig. **Second money shot.** |
| 39 crawl + grab + shoes/swatter drop | floor level | shoes **(GAP — dark leather: 1 instance row or reuse SteelDark)**; swatter (GAP) | READY except shoes/swatter rows. |
| 40 raise ×2 | low angle | swatter grid backlit (EmissiveIntensity 0.3 test — DP call) | READY on swatter row. |
| 41 door + coworker ×3 + click | door medium, frosted glass | FrostedGlass (bands + blur-free toon transparency); coworker shirt = `MI_Toon_Character` (secondary, recedes) | READY; coworker = second rig or background cast (owner call). |
| 42 swing → shock → lower | medium | swatter + Face | READY on rows/rigs. |
| 43 coworker exits CLICK | door | FrostedGlass + PowderCoat handle | READY. |
| 44 deflate ×4 | slow push-in | Face specular does the acting (lifted close-up sheen) | READY. |
| 45 floor corner + mug | insert | VCT + mug (GAP) | READY except mug. |
| 46 sad turn | profile track | WorkerShirt + rim | READY. |

## 5. Act IV — Donuts and doom (shots 47–62)

| Shot | Set / camera | Hero materials | Status |
|---|---|---|---|
| 47 door SLAM + entry | door wide | FrostedGlass shake (no new asset — camera impulse) | READY. |
| 48 donut entry + wall spider + ECU | kitchen track → macro | DonutBox FULL (same instance, closed-lid staging); wall spider small (SpiderBody, throb low); spider ECU = §38 setup reused | READY on rigs. |
| 49 point GASP | medium | Face + Shirt | READY. |
| 50 coworker smile/confusion | two-shot | Character secondary (no hero contrast steal — by design) | READY. |
| 51 explain/shrug/facepalm | three-shot + ECU | Face + hands (rig) | READY on rig bind. |
| 52 facepalm + rage | ECU pair | Face terminator holds shape on turns (profile authored for it) | READY. |
| 53 swatter pickup | floor insert | swatter (GAP row) + VCT | READY on row. |
| 54 ceiling corner stalk | tilt-up | ceiling tile (`T_SDF_CeilingTile`) + SpiderBody rim against white | READY. **White-ceiling rim test — watch for halo, DP call.** |
| 55 spider face ECU | macro | Eyes + Body + hatch | READY. |
| 56 rage ECU (fire eyes) | ECU, hot key | Eyes EmissiveIntensity 3.0 + FlickerDepth 0.6 (DP row — the fire read) + EmissiveFX glow card | READY (DP row queued §6). |
| 57 wall swats ×3 | wall medium | wall Environment + impact dust (Particles master exists: `MI_Toon_Particles`) | READY. |
| 58 miss + self-bonk | medium | Face + Shirt | READY. |
| 59 CRACK (swatter breaks) | insert | swatter halves (same row, two stagings) | READY on row. |
| 60 shock + stance | medium ×2 | — | READY. |
| 61 charge + slow-mo slice | track → ramp | speed feel via shutter/post (no material) | READY. |
| 62 spider leap + swatter (speed lines) | wide, speed-line bg | Rings cell (CellIndex 7) on an EmissiveFX card behind the leap | READY. |

## 6. Act V — Exterminator (shots 63–73)

| Shot | Set / camera | Hero materials | Status |
|---|---|---|---|
| 63 rage ×2 | ECU | Eyes 3.0/0.6 (same DP row as 56) | READY. |
| 64 spray grab + run | kitchen | spray can **(GAP — SteelDark variant row + red cap: 1–2 rows)** | Can row queued. |
| 65 "15 MINS LATER" card | full-frame card | Paper + bMatteFinish (dead matte by design) | READY. |
| 66 door + SLAM entry | door low angle | FrostedGlass + PowderCoat; exterminator stance (rig) | READY. |
| 67 sprinkler chaos BEEP + panting | wide, water FX | water spray: `M_Master_Toon_Particles` streak instances **(GAP — 1–2 rows: white-blue streak, gravity stretch)** + wet roughness push (DP: Wetness 0.6 on floor instances for the soaked look) | Particles rows + wet DP queued. |
| 68 broom raise ×2 | medium | broom (staged `cane_mop001`+`mop_head` — bind + woodgrain instance row? handle = `T_SDF_Woodgrain` look via new row, or reuse laminate) | Broom row queued (1 row). |
| 69 chaos wide (fire, people) | wide | fire = EmissiveFX (PulseRate/Depth rows exist on the master) + extinguisher red (SteelDark red variant — fold into can rows) | Fire rows queued (EmissiveFX instances, 1–2 rows). |
| 70 boss + coworker | medium | boss suit dark (Character secondary dark variant — 1 row) vs white panic | Boss row queued (1 row). |
| 71 sad + broom | medium | — | READY. |
| 72 boss rage + spider ON BACK + zoom | punchline zoom | SpiderBody rim + Eyes throb ON the shirt (contact gag — spider staged on worker rig) | READY on rigs. **Button of the film.** |
| 73 "Uh..." + exit | medium → door | — | READY. |

## 7. Open material gaps (all small, all owned)

| # | Gap | Cost | Owner |
|---|---|---|---|
| 1 | Mug ceramic instance (11/13/20/22/24/45) | 1 row | toon lane |
| 2 | Flyswatter grid red (28–30/39–40/53/57–62) | 1 row (Universal + CellIndex 9 Grid) | toon lane |
| 3 | Blinds instance (window walls, cubicle) | 1 row (`T_SDF_Blinds` or CellIndex 14) | toon lane |
| 4 | Shoes dark leather (39) | 1 row (or SteelDark reuse — DP call) | toon lane |
| 5 | Spray can + cap (64/67/69) | 1–2 rows | toon lane |
| 6 | Broom handle (68/71, staged mop meshes) | 1 row | toon lane |
| 7 | Water streak particles (67) | 1–2 EmissiveFX/Particles rows | toon lane |
| 8 | Fire glow cards (69) | 1–2 EmissiveFX rows | toon lane |
| 9 | Boss suit dark (70/72) | 1 row on Character master | toon lane |
| 10 | Rage-eyes DP row (56/63: Eyes 3.0/0.6) + soaked-floor Wetness row (67) | 2 override rows | toon lane |
| 11 | Worker + spider + coworker rig binds | staged 2 rigs + rest | owner |
| 12 | Kitchen/hallway set build-outs in `L_Toon_Shot_Env` | compose script ext. | owner + toon lane |
| 13 | Boards 31–32 (drawer walk, assumed) | 2 panels | Jeffrey |
| 14 | MRQ presets (final render gate) | — | owner |

Gaps 1–10 are ~12 instance/override rows total — one more `build_instances.py`
+ DP-table pass, then a live build exactly like tonight's. No new masters,
no new functions, no new profiles required. Gap 11 is the critical path:
every READY above still needs the bodies.

## 8. Build order (next)

1. Gaps 1–10 in one builder pass (12 rows), live-build + verify as tonight.
2. Kitchen + hallway set build-out (compose script), Canonical review pass.
3. Rig binds (owner) → Act I–II porcelain pass (porcelain = correct surfaces,
  ikan shakeout, not performance).
4. Shots 21/38/55/72 spider macros (rim/halo tuning on white ceiling vs dark corner).
5. MRQ presets → final-render gate per act.
