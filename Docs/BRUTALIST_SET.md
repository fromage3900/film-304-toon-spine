# BRUTALIST set — Blender GN builders, vendored

The exterior-first building set built in Blender with Geometry Nodes, vendored into this
repo on 2026-09-30 so any group member can regenerate it instead of receiving a `.blend`
nobody can edit.

## What's here

Five builders, 24 art-direction presets:

| Builder id | Presets |
|---|---|
| `GN_BRUTALIST_CityBlock` | `BR_CITY_TIGHT`, `BR_CITY_TOWERS`, `BR_CITY_SPRAWL`, `BR_CITY_CIVIC`, `BR_CITY_TOWERS_GLASS`, `BR_CITY_PUNCHED`, `BR_CITY_COLONNADE` |
| `GN_BRUTALIST_OfficeBlock` | `BR_OFFICE_CIVIC`, `BR_OFFICE_BARBICAN`, `BR_OFFICE_BUNKER`, `BR_OFFICE_SLENDER` |
| `GN_BRUTALIST_CubicleFarm` | `BR_CUBICLE_CANON`, `BR_CUBICLE_MAZE`, `BR_CUBICLE_OPEN`, `BR_CUBICLE_SWARM` |
| `GN_BRUTALIST_Roof` | `BR_ROOF_FLAT`, `BR_ROOF_PITCH`, `BR_ROOF_SAWTOOTH`, `BR_ROOF_BARREL`, `BR_ROOF_HIP`, `BR_ROOF_PLANT` |
| `GN_OFFICE_DeskCluster` | `BR_OFFICE_OCCUPIED`, `BR_OFFICE_BARE`, `BR_OFFICE_PUSHED` |

That is 7 + 4 + 4 + 6 + 3 = **24 presets**. `Blender/surreal_arch/melodia_gn/presets.py`
is the authority — a run prints a warning if a preset a layout entry names is missing.
The `GN_OFFICE_DeskCluster` block is film-repo authored (upstream carries none yet);
the `BR_*` blocks are upstream verbatim.

The office desk cluster is the film-interior prop layer named by
`BRUTALIST_CONVERGENCE_AUDIT §5f`: one shotable tree (worktop, pedestal, monitor,
keyboard, mouse, pad, 5-star task chair), every sub-prop behind its own
`DeleteGeometry`-guarded toggle, real-world mm sizing, and one `surface` Material
socket so the per-prop split can be assigned UE-side (`TP_Office_*`).

The stager lays the set out as seven labelled collections:

| Collection | Objects |
|---|---|
| `01_CITY_PBR` | `CITY_TightEstate`, `CITY_TowerCluster`, `CITY_LowSprawl`, `CITY_CivicSuperblock` |
| `02_CITY_KOMIKAZE` | the same four massings under the Komikaze look |
| `03_OFFICE_BLOCK` | `OFFICE_CivicSlab`, `OFFICE_BarbicanScale`, `OFFICE_Bunker`, `OFFICE_SlenderTower` |
| `04_INTERIOR_CUBICLES` | `CUBICLE_Canonical`, `CUBICLE_MazeShift`, `CUBICLE_OpenPlan`, `CUBICLE_Swarm` |
| `05_FACADE_VARIATION` | `FAC_TowerRibbon`, `FAC_PunchedEstate`, `FAC_CivicColonnade` |
| `06_ROOFS` | `ROOF_FlatParapet`, `ROOF_LowPitch`, `ROOF_Sawtooth`, `ROOF_BarrelVault`, `ROOF_PyramidHip`, `ROOF_PlantDeck` |
| `07_OFFICE_PROPS` | `PROPS_OccupiedDesk`, `PROPS_BareDesk`, `PROPS_PushedChair` |

## Layout and provenance

```
Blender/
  stage_brutalist_review.py          # the entry point (vendored, see header comments)
  export_brutalist_fbx.py            # staged .blend -> one FBX per object (ships whatever the stager laid out)
  blender_utils.py                   # shared headless probes (set_param) for the two Blender entry points
  verify_brutalist_fork.py           # the fork gate: builders, presets, dials, office contract, cycle guard
  surreal_arch/
    __init__.py                      # regular package, so it wins sys.path resolution
    capabilities.py                  # library detection (Higgsas path, addon probes)
    higgsas_bridge.py                # optional third-party node bridge
    melodia_gn/
      __init__.py                    # fork: registers the brutalist family only
      core.py                        # node-graph framework + register_builder
      logging.py, time.py            # core's two intra-package deps
      paris_common.py                # shared math/node helpers the builders call
      higgsas_pipeline.py            # optional Higgsas loader (guarded)
      presets.py                     # BRUTALIST-only subset of the source preset library
      brutalist_city.py              # GN_BRUTALIST_CityBlock
      brutalist_office.py            # GN_BRUTALIST_OfficeBlock
      brutalist_cubicles.py          # GN_BRUTALIST_CubicleFarm
       brutalist_roofs.py             # GN_BRUTALIST_Roof
       brutalist_uv.py                # shared UV trimming used by all four
       brutalist_materials.py         # BR_* material library (Concrete, Asphalt, Glazing, …)
       office_props.py                # GN_OFFICE_DeskCluster (film-interior prop layer, 2026-10-04)
```

Source, for provenance: `P:/MelodiaMelusinaV2-Laptop/deploy/surreal_arch/` and
`P:/MelodiaMelusinaV2-Laptop/deploy/_melodia_stage_gn_brutalist.py`.

Adaptations made when vendoring (all in `stage_brutalist_review.py`, listed in its header):

1. the Blender-addons `sys.path.append(<AppData>/Blender Foundation/5.2/scripts/addons)` line
   was **removed** — the package beside the script is the one that must load;
2. preview tiles are written to `Saved/Previews/` instead of `RawArt/GNShowcase/` (this repo
   has no `RawArt/`);
3. the review-round label is overridable: `BRUTALIST_STAMP` (default `2026-09-25`);
4. `melodia_gn/__init__.py` and `presets.py` are **subsets** of their upstream originals
   (upstream `__init__.py` imports ~100 builder modules; upstream `presets.py` carries every
   builder in the Melodia project). Everything else is verbatim.

## How to run

Blender 5.2 for Windows, headless, no addon install required:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' `
    --background --factory-startup `
    --python 'Blender\stage_brutalist_review.py' `
    -- --skip-render          # omit --skip-render to also render the contact sheets
```

- `--skip-render` stages and saves the `.blend` only (seconds, no EEVEE pass).
- `--keep-previews` keeps the individual tile PNGs instead of only the composited sheets.
- `BRUTALIST_STAMP=2026-10-07` (env var) names the review round; default `2026-09-25`.
- Needs about a minute of CPU and no GPU. Nothing outside the repo is read.

## What a run produces

| Output | Path | Committed? |
|---|---|---|
| Review `.blend`, one live GN modifier per object | `Saved/Blend/BRUTALIST_CITY_REVIEW_<stamp>.blend` | no — `Saved/` is gitignored |
| Contact sheets (cities PBR + Komikaze, office, roofs, facade, palette) | `Saved/Audit/brutalist_sheet_*.png` | no |
| Per-object manifest: builder, preset, nodes, params, verts, bbox, materials | `Saved/Audit/brutalist_stage_manifest.json` | no |
| Preview tiles per collection | `Saved/Previews/brutalist_<stamp>/` | no |

Everything lands under the gitignored `Saved/` tree on purpose: the `.blend` is a build
artifact, and the manifest is the evidence you attach to a commit message or a review post
rather than a file to track.

## Verified run — 2026-09-30

Run from this repo on Blender 5.2 (`--skip-render`), after vendoring:

```
[br-stage] DONE objects=25 sheets=0
blend   -> Saved/Blend/BRUTALIST_CITY_REVIEW_2026-09-25.blend   (1.121 MB)
manifest-> Saved/Audit/brutalist_stage_manifest.json            (14 KB)
```

- **25 objects** staged across the **6 collections**, no `MISSING builder` and no
  `preset not found` warnings — so the vendored package and the 21 presets all resolve.
- Node counts per tree: city `194` nodes / 32 params, roofs `208` / 22, office and cubicles
  their own trees — every object carries a live modifier, which is the point of the review file.
- Palette board reports **28 swatches** from `brutalist_materials.SURFACES`.
- Import check inside Blender resolved the **vendored** package, not a Blender addons copy:
  `surreal_arch.__file__ == P:\film-304-toon-spine\Blender\surreal_arch\__init__.py`.

## Verified run — 2026-10-04 (office props + fork resync)

The fork gate found `core.py` **stale against upstream** (manifest recorded at upstream
commit `35ea2666`; upstream had moved to `b0b58bb8` with three defect fixes: interface-socket
dedup on rebuild, nested-tree `_prune_interface` protection, node-aware `link_sockets`).
`python Tools/resync_fork.py --write` re-extracted it and vendored `office_props.py`
(new VERBATIM entry), so the fork now matches upstream `b0b58bb8` byte-for-byte on all 12
verbatim files.

Blender 5.2, `--background --factory-startup`:

| Check | Result |
|---|---|
| `Blender/verify_brutalist_fork.py` | **PASS, 0 failures** — 5 builders register + build acyclic (office cluster 192 nodes), 24 presets resolve, city/roof dials still live, cycle guard negative-tests pass |
| Office contract | `surface` is a `NodeSocketMaterial` input; default build **294 verts**; all six toggles off → **24 verts** (desk remains, props GONE); `Chair` off → 182; `Chair Push` 0 → 0.35 moves the chair bounds `y [−0.355, 0.350] → [−0.350, 0.690]` |
| `stage_brutalist_review.py` (stamp `2026-10-04`, with renders) | **DONE objects=28 sheets=7** — new `07_OFFICE_PROPS` collection (`PROPS_OccupiedDesk` 294v / `PROPS_BareDesk` 56v / `PROPS_PushedChair` 294v), new `brutalist_sheet_office_props.png` (3 tiles), node-group isolation OK (28 distinct groups) |
| `export_brutalist_fbx.py --stamp 2026-10-04` | **objects=28 total_verts=29144 errors=0 ok=True**, cross-checked both directions against the stager manifest (28/28) |

Convergences made in the same pass:

- `Blender/export_brutalist_fbx.py` no longer re-lists the stager's collections by hand — it
  exports whatever the staged `.blend`'s root collection carries (minus the palette board) and
  cross-checks completeness against the stager manifest. The old `== 25` object-count assert was
  a hand-counted number that this very change would have broken.
- the identical `set_param` probe now lives once in `Blender/blender_utils.py`, imported by both
  `stage_brutalist_review.py` and `verify_brutalist_fork.py`.
- `Tools/verify_all.ps1` gained a duplicate-file drift gate: `Docs/GROUP_STAGING_GUIDE.md` and
  its `Humber_FinalYear_Prep/` copy (byte-identical handover copy) are hashed on every run. Its
  level scan now audits the `.umap` files git knows about (tracked + untracked-not-ignored)
  instead of every `.umap` on disk, so deliberately gitignored vendored content (the `Content/UDS*`
  Ultra Dynamic Sky drop) can no longer fail the gate on a level this project never ships.
- `Python/level_lib.py` now carries the one implementation of level open/create/cleanup, mesh
  spawn and light spawn, shared by `compose_shot_env_level.py` and `stage_brutalist_layout.py`.
  The layout script's copies had drifted: they still carried the positional-`Rotator`
  sun-on-the-horizon bug the shot script fixed on 2026-10-02, and they lacked the dirty-map
  guard (blocking save-changes modal, observed 2026-10-01). Both now come from the shared
  implementation.

## Optional: the Higgsas node library

`higgsas_pipeline.available()` was **False** in this repo, and the run still completed — the
builders guard the import and fall back to native nodes (that contract is deliberate: a fresh
clone must build). Four roof features and the city facade treatments use Higgsas when present.

To enable it, any one of:

1. copy the library to `RawArt/BlenderLibraries/Higgas/Blender 5.0 Higgsas Geo Node Groups v13.blend`
   (the path `capabilities.higgas_library_path()` expects, relative to this repo's root);
2. set the environment variable `MELODIA_REPO_ROOT` to the Melodia workspace
   (`P:/MelodiaMelusinaV2-Laptop`) before launching Blender;
3. install the `surreal_arch` addon and set its **Higgsas library path** preference override.

## Getting the set into this UE project

The Blender side is headless on any machine; the UE side is editor work:

1. run the stager with renders to get the contact sheets, then
   `Blender/export_brutalist_fbx.py` (ships whatever the stager laid out — 28 objects
   as of 2026-10-04, cross-checked against the stager manifest);
2. `Python/import_brutalist.py` imports the FBX set into `Content/Environment/Brutalist/`
   and `Python/stage_brutalist_layout.py` reproduces the reviewed grid as
   `L_Brutalist_Layout` — both read the manifests, no retyped lists;
3. assign `MI_Toon_*` instances from the toon spine per material family
   (the master expects material instances, see `Docs/TOON_SPINE.md`); the office desk
   cluster takes the `TP_Office_*` set (`MI_Toon_Office_*`);
4. keep the exported FBX small — this repo has no LFS yet, so a large binary will hurt the
   clone for everyone (see `Docs/AUDIT_2026-09-30.md`, finding F7).

## Not vendored (deliberately)

- the per-builder health scripts (`deploy/_melodia_health_brutalist_*.py` in the source repo) —
  ask if you want them; they assert builder contract details and would need path adaptation;
- the other ~100 GN builder modules from the Melodia catalog (Paris family, castles, music,
  garments …) — this is the building set only;
- the Higgsas library itself (third-party, ~20 MB, licensed separately);
- the preview tiles from the 2026-09-25/28 run (they live in the Melodia workspace).

## Dial audit: resolved 2026-09-30 (all three implemented, all four scripts PASS)

**Read this before trusting any vertex number below.** The audit above was correct that
`Window Bay`, `Fin Count` and `Plant Units` were inert — but it was measuring a tree that
**could not evaluate at all**, so those "dead dial" readings were partly an artifact.

### The real defect: a self-link that killed the whole group

`_build_facade` built a socket-driven bay count with a DIVIDE → ROUND → MAXIMUM chain. The z
axis was wired wrong:

```python
link_sockets(tree, n_bays_z_r.outputs[0], n_bays_z_r.inputs[0])   # node linked to ITSELF
link_sockets(tree, n_bays_x.outputs[0],   n_bays_x_r.inputs[0])   # x, correct
```

Blender **accepts a cycle without error**. So the build succeeded, `link_failures` stayed
empty, every node counted as created, and the group simply evaluated to **0 verts** with
`Cannot evaluate node group` in the log. Every city probe — including the pre-existing grid,
street-width, height and seed probes — reported 0, which reads exactly like "every dial is
dead". The dials were not dead; the group was dead.

Isolated by bisecting the real source as a module (19 variants, none of which edited the repo):
`facade=None` → 576 verts · punched block never built → 576 · punched block built → 0 ·
replacing the one self-link line → **576 verts**. Confirmed by construction, not by elimination.

| | before | after |
|---|---|---|
| city group at defaults | 0 verts, `Cannot evaluate node group` | **576 verts** |
| styles 1 / 2 / 3 | 0 / 0 / 0 | **832 / 1216 / 880** |
| `Window Bay` 0.6 → 6.0 | 0 → 0 | **2880 → 832** |
| `Fin Count` 0 → 40 | 0 → 0 | **832 → 1152** |
| `Plant Units` 0 → 30 | 48 → 48 | **48 → 264** |
| all four health scripts | exit 1 (city) / exit 1 (roofs) | **exit 0, PASS, 0 problems** |

### What was implemented

- **Punched (style 2)** — discrete windows on a socket-driven bay grid; count is
  `max(1, round(span / Window Bay))`, so `Window Bay` changes the real window count.
- **Colonnade (style 3)** — slot windows **plus** fins, instanced along a `Fin Count` line at
  `Window Bay` pitch. Previously style 3 gated the *same* band stack as style 1, which is why
  the two read as identical and `Fin Count` had nothing to read.
- **`Plant Units`** — three hero boxes plus `(Plant Units − 3)` instanced along the width,
  clamped at 0 so a smaller count keeps the hero three. Pitch is `w_span / Plant Units`, so the
  deck stays on the roof at any count.

### Guards added, so this cannot recur silently

- `core.link_sockets` now **refuses a self-link** and records it as a link failure.
  Blender will not raise on a cycle, so nothing else caught it.
- `core.find_link_cycles(tree)` reports longer `a -> b -> a` cycles by name.
- All four health scripts assert the graph is **acyclic before trusting any geometry number**,
  so a dead group can no longer be misread as dead dials.
- New probe coverage: styles 1/2/3 pairwise-distinct, `Window Bay`, `Fin Count`, `Plant Units`.
- Negative test for the guard itself: `deploy/_melodia_test_cycle_guard.py`
  (5/5 PASS, evidence `Saved/Audit/_test_cycle_guard_2026-09-30.txt`) — including the trap that
  the first version of the guard fell into: `socket.node` returns a **new wrapper object on
  every access**, so `out.node is in.node` is False even for the same node. It must be `==`.

### Still true (unchanged by this work)

- `Geometry` group input is unread on all four builders — by design, the builders generate
  rather than consume.
- Deferred upstream, per the builders' own comments: per-lot office massing and street-furniture
  reuse are **P4b**; `brutalist_roofs.py` refers to a deferred `gn_common` shim.
- The facade ring is instanced on a zero-offset MeshLine, so bands stack at the origin rather
  than following each building's island. Pre-existing behaviour, not touched here, and the
  reason the three facade objects still read as one style at three scales in the contact sheets.

<details>
<summary>Superseded 2026-09-25/28 audit — kept for provenance, do not act on it</summary>

The four builders build cleanly and pass their own health suite. What the suite does **not**
cover is three inert dials and two unimplemented facade styles. Runtime evidence (Blender 5.2,
`--background --factory-startup`, evaluated vertex counts):

| Finding | Evidence | Where |
|---|---|---|
| `Facade Style` 1 / 2 / 3 produce **identical** geometry — Punched and Colonnade are not implemented | style 1 = style 2 = style 3 = **864 verts** (style 0 = 576) | `brutalist_city.py::_build_facade` gates on `style > 0` only |
| `Window Bay` is a **no-op dial** | 0.6 → 864 verts, 6.0 → 864 verts; source never reads `p["bay"]` | city |
| `Fin Count` is a **no-op dial** — fins are hardcoded to 4 | 0 → 864, 40 → 864; loop is `for i in range(4)`, `p["fin_count"]` written but never read | city |
| `Plant Units` is a **no-op dial** | 0 → 48 verts, 30 → 48 verts; `DECKN` is created and never referenced again | `brutalist_roofs.py:150` |
| Controls prove the measurement is sensitive | `Window Floors` 2→30: 672→1568 verts; `Roof Plant` off→on: 24→48 verts | — |
| `Geometry` group input is unread on all four builders | probe: 4 builders, 7 unread inputs total (`Geometry` ×4 plus the three above) | all |

The `864` figure is the tell: those runs used a **stale vendored copy** that predated the facade
work, which is also why the numbers disagree with the table above. The "styles are identical"
finding was real but measured on the wrong code.

</details>


- do not hand-edit the `.blend` and commit it — regenerate from the builders, the same rule the
  toon spine follows for `.uasset` files;
- do not rename the builder ids or the `BR_*` preset ids — the stager's `LAYOUT` table and the
  manifest both key on them.

