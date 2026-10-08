# Melodia → UE repo: universal toon master convergence — 2026-10-06/07

**Status: film material core landed (the six utilities + the static deep-night sky
preset), rebuilt headless 2026-10-07, spine `OVERALL: PASS`, master compile verified
clean at load; a machine-local texture fresh-load decay is documented in §6 and does
NOT gate the material core.**

Companion to `Docs/TOON_SPINE.md` (repo spine), `Docs/TOON_MASTERS_PLAN_2026-10-04.md`
(forward plan) and `specs/humber_toon_spine/melodia_intake_manifest.v1.json` (why raw
`.uasset` copy is not an intake channel).

The goal, in the owner's words: *"bring over the universal toon master from Melodia and
trim it for the UE repo"*, *"mainly just converging some of the MFs from the original
project."* The 2026-10-07 brief then bounded it further: **make the film-focused core
reliable first** — audit all eight unfinished source functions, converge the six selected
utilities plus a single static deep-night sky preset, keep iridescence / sparkle /
vein-glow / radial-rings out, and only then grow the set.

## 1. Source, recovered (read-only, not copied)

Static package-path scan of the source master, done 2026-10-06:

| | |
|---|---|
| Source project | `D:\EnvironmentPortfolio\BS_GodFile` (`BS_GodFile.uproject`, UE 5.8) — read-only from here |
| Source master | `Content\EnvSandbox\Materials\Masters\M_Master_Toon_Universal.uasset` (754,331 bytes) |
| Raw evidence | `Saved/Audit/melodia_toon_master_scan_2026-10-06.json` |

The Melodia universal master is a **super-master**: one graph carrying ~25 feature lanes
(celestial/space, weather/UDS, triplanar, layer stacks, sparkle/glitter, Chladni/cymatics,
audio-reactive, gemstone, ...). The repo's master is the deliberately **trimmed**
reconstruction of it (built by `Python/build_master_toon.py`).

## 2. The eight unfinished source functions — 2026-10-07 audit result

The 2026-10-06 §2 list named nine project MFs + one MeshBlend utility. Eight of those were
"MISSING as builder" / "pending (node graph)" — the audit's eight. Their state today:

| # | Source MF | Film deliverable | Builder | Master routing | Gate state 2026-10-07 |
|---|---|---|---|---|---|
| 1 | `MF_ColorRamp3` | (already present) | `build_mf_colorramp3.py` | Universal + spine | kept (tracked, rebuilt each run) |
| 2 | `MF_SpaceParallax` | same name, verbatim HLSL | `build_mf_spaceparallax.py` (2026-10-06) | Universal → additive emissive | built + wired + rebuilt 10-07 |
| 3 | `MF_ClothWindDrape` | same name, verbatim HLSL | `build_mf_clothwinddrape.py` (2026-10-06, **stabilized 10-07**: internal `Time` read — see §4) | Universal → additive WPO | built + wired + rebuilt 10-07 |
| 4 | `MF_NormalAdjust` | `MF_NormalAdjust` (rebased in world space, identity at strength 1) | `build_mf_normaladjust.py` (2026-10-07) | Universal → Toon BSDF Normal staging | built + wired + compiled |
| 5 | `MF_Itto` (Truchet cracks + wear) | `MF_SurfaceWear` (film-named successor) | `build_mf_surfacewear.py` (2026-10-07) | Universal + Landscape → colour ink + roughness, gated at 0 | built + wired + compiled |
| 6 | `MF_DF_ContactBlend` | `MF_DF_ContactBlend` (package rebuilt in place over the drop binary) | `build_mf_contactblend.py` (2026-10-07) | Universal + Landscape → contact tint/roughness, gated at 0 | built + wired + compiled |
| 7 | `MF_Impressionist_Impasto` | `MF_Impasto` (film-named successor; Unparked BrushScale/StrokeStrength) | `build_mf_impasto.py` (2026-10-07) | Universal → additive WPO, gated at 0 | built + wired + compiled |
| 8 | `MF_NikkiDreamGrade` | `MF_FilmGrade` — **re-scoped by the owner brief** to a NEUTRAL film grade | `build_mf_filmgrade.py` (2026-10-07) | M_Master_Toon_PostComposite → staged before GradeTint | built + wired + compiled |
| — | `MF_Madoka` (Voronoi vein glow + rings) | **NOT selected — stays out** (owner: vein glow + radial rings out of Humber) | — | — | drop binary untouched, not counted, never called |

Note on the "non-resolving drop": the 132-file 2026-10-04 intake drop sits in
`Content/Materials/` (now mostly tracked); its internal `/Game/...` paths still point at
Melodia, so **0 of the dropped packages resolve here**. Route A (regenerate in Python) is
the repo-canonical channel. Where the film function's NAME exactly matches a dropped
package (`MF_DF_ContactBlend`, `MF_FilmGrade`), the builder wipes that drop binary in
place and regenerates it — object identity preserved, the unusable bytes replaced by
generated ones. Where it does not (`MF_SurfaceWear`, `MF_Impasto`, `MF_NormalAdjust`),
it is a new generated asset and the drop binaries stay out of the spine, unused and
uncounted.

## 3. Keep-out list (owner brief, 2026-10-07)

**Iridescence** (`MF_MelodiaIridescenceSheen` / gemstone family), **sparkle**
(`MF_MeluSparkle` / glitter lanes), **vein glow + radial rings** (`MF_Madoka`) stay out of
Humber. They are not referenced by any master, not built by any builder, and
`build_spine.py`'s expected-call lists cannot be satisfied by them. A NEW film-specific
function is allowed only after this core passes its stability gate AND answers an
observed need in a Humber material or shot.

## 4. Film-material-core contract (2026-10-07) — controls, ranges, default stability

Every lane obeys the repo's default-OFF law: at the shipped defaults each lane's
contribution is exactly zero (or exactly the pre-existing value), so every existing
instance is pixel-identical until it opts in.

- **MF_NormalAdjust** — *identity gate*: `NormalStrength` 1.0 (0 would flatten the
  normal, a pixel change). Reads the caller normal + base (vertex) normal; renormalized
  output. <1 softens band response over curves, >1 snaps bands to edges.
- **MF_SurfaceWear** — *gates*: `WearStrength` 0 (colour wear) + `CrackStrength` 0 (crack
  ink); roughness lerp toward `WearRoughness` rides the same gates. Controls: `WearScale`
  (cells/cm, 0.02 = ~50 cm tile), `CrackWidth` (tile units, 0.01..0.08 useful),
  `WearThreshold` (patch onset). Dominant-axis world projection so cracks follow walls
  and floors.
- **MF_DF_ContactBlend** — *gate*: `DFContactStrength` 0 → tint toward `DFContactTint`
  and roughness toward `DFContactRoughness` are inert. Recovered node-for-node from the
  source builder math (`saved/Audit` trace of `build_distance_field_material_spike.py`):
  DF proximity × power sharpness × noise breakup × ground-height envelope × strength.
- **MF_Impasto** — *gate*: `ImpastoStrength` 0. `BrushScale` (0.02..0.09 useful, 0.045 ≈
  140 cm strokes) + `StrokeStrength` + `StrokeAngle` shape the field — the two dials that
  were previously Parked/UNWIRED on Universal are now genuinely wired, still inert until
  the gate opens. Output adds to WPO along the vertex normal.
- **MF_ClothWindDrape** — *stabilized, not changed*: the control contract now documents
  ranges (WindStrength in cm: drift 0.05..0.15, walk breeze 0.2..0.35, gale 0.5..1.0;
  WindSpeed 0.2..1.5 cycles/sec; FoldingAmount 0..1 stage-cloth flap; DrapeMask per-surface)
  and the identity gate is WindStrength 0 AND FoldingAmount 0. **One real fix**: the
  verbatim HLSL referenced `Time`, which a Custom node has no identifier for in the vertex
  context — the first real shader compile of the graph failed
  (`use of undeclared identifier 'Time'`, run-2 log 2026-10-07). The function now reads an
  internal `MaterialExpressionTime` (the same read the source graph itself had), so
  Universal — and everything that takes WPO from it — compiles clean.
- **MF_FilmGrade** — *identity gate*: Contrast 1.0 about the 0.18 film pivot, Warmth 0
  (luma-neutral blue..amber shift), Saturation 1 (Rec.709 luma lerp), Lift (0,0,0). Routed
  into `M_Master_Toon_PostComposite` BEFORE the per-shot `GradeTint` multiply, so shot
  tint semantics are unchanged.
- **Static deep-night sky preset** — `MI_Toon_Sky_DeepNight` on
  `M_Master_Toon_Sky` (deep indigo-black zenith `0.02,0.032,0.075`, city-glow horizon
  `0.115,0.150,0.235`, moonlit cloud bands `0.28,0.31,0.40`, 4 posterization bands, sparse
  stars at scale 120 / intensity 2.4, `bStarsOn` True). DELIBERATELY not a time-of-day
  system — one fixed parameter set on the sky master's existing controls (the master's own
  builder asserts no Toon BSDF and no profile). Spot-asserted by
  `Python/verify_expansion.py` from a fresh process.

## 5. The stability gate evidence (2026-10-07)

| Gate | Result |
|---|---|
| `Python/build_spine.py` headless (run 4, 2026-10-07) | **`OVERALL: PASS`** — `errors: []`; 11/11 functions (incl. the five new), 14/14 masters, 31/31 profiles, 51/51 instances (incl. the deep-night preset), 17/17 pattern overrides, office set assigned, textures ok |
| Fresh-process load compile (`Python/check_master_compile.py`, load-only gate, 2026-10-07 final) | **compile-at-load CLEAN — zero "Failed to compile" / "Missing input" / "undeclared identifier" emissions** for 15/15 masters + 12/12 functions. The in-process `Missing A input` warnings that appear DURING a spine run are a rebuild transient (the same bytes load clean in a fresh process — bisect probes `Saved/Audit/switch_diagnostic*`, and the load-only gate writes `Saved/Audit/loadonly_gate_20261007.json`); a fresh load, not a same-session recompile, is the compile authority this repo treats as truth |
| No Melodia or game-only dependencies | new MFs are pure Custom-HLSL or engine shading nodes (DistanceToNearestSurface etc.); no MeshBlend, UDS, MPC or Melodia text/art reference — the five keep-out binaries stay unused |
| `Tools/dogfood_toon_spine.py --all` + `Tools/verify_all.ps1` | run results in `Saved/Audit/verify_all_2026-10-07.txt` |
| Visual review of the preset in SH010/SH020 | **still owed** — lookdev on this laptop is driver-blocked (SM5 vs Substrate SM6, documented in `Docs/TOON_SPINE.md`), so the owner reviews the preset from the desktop before the function set grows |

## 6. Machine-local texture fresh-load decay (found 2026-10-07, environment-level)

Minimal reproduction (`Saved/Audit/import_probe_20261007.json`,
`import_keep_freshread_20261007.json`, `reimport_probe_20261007.json`): an
`AssetImportTask` import of a 256×256 PNG reads back 256×256 in-process, but the SAME
saved package loads as the 32×32 default texture in a fresh editor process — for every
texture, including ones this session never touched. The Oct-3/5/6 fresh reads on this
machine reported real sizes, so something in the environment changed outside the repo.
Actions taken in-repo, with evidence:

- `build_textures._import_png` no longer saves inside the import task (`task.save =
  False`); the single explicit save after settings is the one writer, and a size-vs-source
  HARD GATE now fails the texture stage if a saved texture is smaller than generated —
  the run-3 texture stage is the deterministic spawner of the 32×32 stub class
  (`Saved/Audit/size_only_20261007.json`, `tag_probe_20261007.json`).
- `build_pattern_overrides` merged the duplicate `MI_Toon_Office_Carpet` keys — the late
  Wetness row was silently replacing the baked-loop SDF row (the same kill-class the
  coffee-machine merge note records). One row now carries PatternIndex 12 +
  `T_SDF_CarpetLoop` + PatternScale 30 + Wetness 0.5.
- `Python/verify_expansion.py` expectations updated to the table's CURRENT intent
  (carpet → `T_SDF_CarpetLoop`; SpiderEyes `EmissiveIntensity` 3.0 post-override).

Until the fresh-load decay is understood (owner decision: interactive editor session first
/ desktop machine / driver upgrade), texture sizes may read 32×32 in fresh processes on
this laptop even when the spine's texture stage is green. The material core's compile and
wiring gates do not depend on it.

## 7. Deviations recorded (rather than silent)

- `MF_ClothWindDrape` — the source wired a `Constant3Vector` into its graph; this
  reconstruction exposes `WindDirection` as a function input (2026-10-06), and as of
  2026-10-07 an internal `Time` read (see §4). Same maths, artist-controllable.
- `MF_SpaceParallax` — function output named `Color` (the source output name is not
  conclusively recoverable from the binary).
- `MF_NormalAdjust` — world-space film contract (identity at strength 1) instead of the
  packed-map conditioner; the source's own job is preserved (normal-response shaping).
- `MF_Itto → MF_SurfaceWear`, `MF_Impressionist_Impasto → MF_Impasto`,
  `MF_NikkiDreamGrade → MF_FilmGrade` — film-named successors per the owner brief's
  utility language; mapped explicitly in §2.

To build: `UnrealEditor-Cmd.exe <project>.uproject -ExecutePythonScript="Python/build_spine.py" -stdout -unattended`
then assert on `%TEMP%/spine_build_report.json`; fresh-process read-backs via
`Python/verify_expansion.py`; per-master compile status via `Python/check_master_compile.py`.
