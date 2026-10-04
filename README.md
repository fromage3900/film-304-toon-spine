# Humber 304 UE Toon Shading Pipeline 

Standalone UE 5.8 toon shading spine and brutalist building set for the Animation Art 5
group film. Content-only project: no C++ module, no compiler, no third-party plugin
dependency — clone it and open it.

## Hello friends ~ 

This is a base UE project that includes the shader pipeline we will be using for our indie film. I'll update with video tutorials on how to install asap; do not stress if you don't have git experience.

## Start here

```powershell
git clone <this-repo>
cd film-304-toon-spine
git config core.hooksPath .githooks      # ONCE per clone - enables the safety gate
powershell -File Tools/verify_all.ps1    # is this checkout healthy?
```

Then read, in this order:

| Doc | What it is |
|---|---|
| `Docs/GROUP_WORKFLOW.md` | who owns what, the one-editor-per-file rule, branch/tag cadence |
| `Docs/CONTENT_CONVENTIONS.md` | where assets live, naming, and the generated-not-copied rule |
| `Docs/TOON_SPINE.md` | the material system: what exists and how it is wired |
| `Docs/BRUTALIST_SET.md` | the procedural building set and its dial audit |
| `Docs/ASSETLIST.md` | the asset list (this is the `assetlist-v0` deliverable) |
| `Docs/AUDIT_2026-09-30.md` | open findings, with the exact fix for each |

## Structure

```
Content/
  Materials/
    Masters/          M_Master_Toon_Universal (the spine), M_Outline_InvertedHull
    Functions/        MF_ColorRamp3, MF_RampLUT, MF_ProceduralPatterns
    ToonProfiles/     TP_* art-direction assets (11)
    Instances/        MI_Toon_* / MI_Outline_* instances (10)
  Maps/               L_Toon_Lookdev (look development level)
Blender/              vendored brutalist GN builders + stage/verify entry points
Python/               the code that GENERATES the materials in Content/
Tools/                verify_all.ps1, resync_fork.py, test_precommit.ps1
Docs/                 this documentation
Saved/                render output + evidence reports (mostly gitignored)
```

## Regenerating the materials

Assets in `Content/Materials/` are **generated from code**, not hand-authored and not
copied between projects. `Python/` is the source of truth; the `.uasset` files are its
output. Editing a material in the editor without changing the builder is the defect
pattern this repo exists to avoid — see `Docs/CONTENT_CONVENTIONS.md`.

```powershell
# Full spine rebuild + verification (writes a report; asserts on the report, not the log)
UnrealEditor-Cmd.exe MelodiaToonFilm.uproject -ExecutePythonScript="Python/build_spine.py" -stdout -unattended
```

`build_spine.py` runs the modules in dependency order:

```
build_mf_colorramp3 -> build_mf_ramplut -> build_mf_patterns
        -> build_master_toon (M_Master_Toon_Universal) + build_m_outline
        -> build_toon_profiles -> build_instances
```

Other scripts:

| Script | Purpose |
|---|---|
| `Python/extract_dependencies.py` | traces the material-function dependency graph, writes `Saved/DependencyMap.json` |
| `Python/build_test_level.py` | rebuilds `L_Toon_Lookdev` |
| `Python/migrate_spine.py` | one-way migration helper, run deliberately |
| `Python/build_master.py` | **deprecated** — cannot run; points at `build_spine.py` |

## Blender side

```powershell
# Regenerate the .blend + labelled contact sheets
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --factory-startup `
  --python Blender\stage_brutalist_review.py

# Assert the builders, presets, dials and the cycle guard
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --factory-startup `
  --python Blender\verify_brutalist_fork.py
```

`Blender/surreal_arch/` is a **one-way vendored copy** of part of the Melodia geometry-node
library. It is checked for drift, not trusted: `python Tools/resync_fork.py`.

## Engine requirements

- Unreal Engine **5.8+** (Substrate Toon BSDF is experimental in 5.8)
- No external plugins required (the MeshBlend dependency was stripped)
- Blender 5.2+ for the building set only

## Research

`Docs/FILM_PIPELINE.md` — the indie short-film workflow for UE 5.8's Substrate Toon pipeline,
including the budget/schedule shape.

