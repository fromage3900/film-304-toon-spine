# Content conventions

Written 2026-09-30. Two things live here: where assets go, and the rule that keeps this project
regenerable. The second one is not a style preference — it is why the project can be rebuilt at
all.

## The rule: assets are generated from code, never copied

`Content/Materials/**` is produced by `Python/`. The `.uasset` files are output, the builders are
the source of truth.

This exists because of a documented failure. On 2026-09-29 a cross-project copy of the toon spine
silently dropped its graph: `M_Master_Toon_Universal` went from 751,265 to 666,458 bytes and **all
ten `MaterialFunctionCall` references disappeared**, while the verifier reported clean — it counted
zero calls, saw zero dangling references, and passed. A copied asset can be structurally fine and
semantically empty, and nothing in the editor tells you.

So:

| Do | Do not |
|---|---|
| change `Python/build_*.py`, then rebuild | hand-edit a material graph and save |
| add a parameter to the builder | add a parameter in the editor only |
| make a **material instance** for a variation | duplicate the master and tweak the copy |
| fix `Blender/surreal_arch/` upstream, then `Tools/resync_fork.py --write` | edit the vendored fork in place |
| run `Tools/verify_all.ps1` before calling it done | trust the editor's green tick |

A material instance is the supported way to vary a look. `MI_Toon_*` inherit from
`M_Master_Toon_Universal`; that is what the instances are for.

## Folder contract

```
Content/
  Materials/
    Masters/        M_*        the master materials (2)
    Functions/      MF_*       material functions (3)
    ToonProfiles/   TP_*       art-direction data assets (11)
    Instances/      MI_*       material instances (10)
  Maps/             L_*        levels
  Environment/
    Brutalist/      SM_*/BP_*  the procedural building set (desktop import step)
  Characters/                  character meshes, rigs, materials
  Props/                       set dressing
  Sequences/                   Sequencer / level sequences
  Cinematics/                  cameras, MRQ presets
```

Create folders only as they are needed. Agree in the group before adding a top-level folder under
`Content/` — a half-split taxonomy is worse than none, and `Content/` is the one thing everybody
touches.

## Naming

| Kind | Prefix | Example |
|---|---|---|
| Master material | `M_` | `M_Master_Toon_Universal` |
| Material instance | `MI_` | `MI_Toon_Stone` |
| Material function | `MF_` | `MF_RampLUT` |
| Toon profile | `TP_` | `TP_Hero` |
| Static mesh | `SM_` | `SM_Brutalist_Lot_A` |
| Blueprint | `BP_` | `BP_Brutalist_Kit` |
| Level | `L_` | `L_Toon_Lookdev` |
| Level Sequence | `LS_` | `LS_Shot010` |
| Texture | `T_` | `T_Concrete_Board` |

Suffixes for textures: `_D` diffuse, `_N` normal, `_R` roughness, `_M` mask. Suffix variants of
the same asset with a short qualifier (`_Thin`, `_Heavy`), and never with a number — `Stone2`
tells nobody anything.

## Which toon profile for what

`M_Master_Toon_Universal` reads its look from a Toon Profile. Pick by subject, not by taste:

| Profile | Use for |
|---|---|
| `TP_Hero` | the protagonist, close-ups, the shots that must hold |
| `TP_Default` | anything with no better answer |
| `TP_Environment` | the world mass |
| `TP_Foliage` | plants, trees, hedges |
| `TP_Stone` / `TP_Gold` | hero materials that need a harder or shinier band |
| `TP_SoftPainterly` / `TP_Warm` / `TP_Cool` | mood passes; keep one per shot so the palette is not fighting itself |
| `TP_Hatched` / `TP_TwoTone` | deliberate graphic styles, not defaults |

Outlines are separate from the toon shader: `M_Outline_InvertedHull` plus
`MI_Outline_Thin` / `MI_Outline_Heavy`. Use `_Thin` on characters and `_Heavy` on large
architecture, or the line weight reads as inconsistent.

## The brutalist set

`Content/Environment/Brutalist/` holds the GPU-friendly export of the Blender geometry-node
builders in `Blender/`. The full source of that set, its presets and its dial audit are in
`Docs/BRUTALIST_SET.md`.

Export rule: apply the `MI_Toon_*` instance at build time and **export only what the shot needs** —
this repo has no LFS on `.fbx` growth budget to spare, and an unmerged 25-object staging scene is
several hundred thousand verts.

## Before you commit

```powershell
powershell -File Tools/verify_all.ps1
git status --short
```

If you changed anything under `Content/Materials/**`, the only acceptable commit message is one
that also names the builder you changed. If you cannot name it, you edited generated output and
the change will be lost.
