# Art staging to LFS — plan, blockers, and the contradictions to resolve

**Written 2026-10-03. Status: PLAN ONLY. Nothing staged, committed, or pushed.**

Goal stated by the owner: *"stage the art assets to LFS so they pull and each clone is the same
for each project user."* The goal is correct. This document records why it cannot be executed as
a git operation today, and exactly what has to be decided first.

Every claim below names the probe that produced it.

---

## 1. The blocker: all the art lives in `Saved/`, which is ignored *and* hook-blocked

Measured inventory of every LFS-eligible file on disk (`find Saved -type f \( -iname '*.png' -o
-iname '*.blend' -o -iname '*.fbx' \)`):

| Location | Files | Size | What it is |
|---|---|---|---|
| `Saved/Screenshots/` | 11 | 10.6 MB | editor screenshots |
| `Saved/Lookdev/` | 11 | 7.9 MB | lookdev grids, versioned by hand (`_v2`, `_v3`, `_v4`) |
| `Saved/Audit/` | 6 | 7.6 MB | brutalist contact sheets |
| `Saved/Renders/` | 5 | 3.4 MB | prototype stills |
| `Saved/Blend/` | 2 | 2.3 MB | brutalist review `.blend` |
| `Saved/Export/` | 25 | 1.3 MB | brutalist `.fbx` |
| `Saved/PBR/` | 70 | 31.0 MB | **baked PBR maps — on D: only, 0 on P:** |
| **total** | **130** | **64 MB** | |

Two independent mechanisms block every one of those from being committed:

**`.gitignore:16`** — `/Saved/*`, with allowlists only for `Saved/Audit/*.{json,md,txt}` and
`Saved/Reports/*.{json,md,txt}`. The comment at lines 7–15 is explicit that render output is not
versioned and the PNGs are regenerable in minutes. Note the deliberate `/Saved/*` rather than
`/Saved/` — the comment explains the gitignore parent-directory trap.

**`.githooks/pre-commit` check #5** (lines 113–122) — stages matching
`^(Intermediate|Saved|Binaries|DerivedDataCache)/` are a hard error, except
`^Saved/(Audit|Reports)/.*\.(json|md|txt)$`. So even `git add -f` cannot bypass it: the comment
on line 114 says so outright. **The hook is enabled** (`core.hooksPath = .githooks`).

So "stage the art to LFS" is not a `git lfs track` problem. The files are in the one directory the
repo has decided, twice and on purpose, not to version.

---

## 2. The team asset location already exists — and it is empty

`Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/` is tracked (29 files) and is the designated
per-slot home for exactly this art:

```
02_Assets/Models/Characters/    CH_    (slot 04)
02_Assets/Models/Environments/  EN_    (slot 05)
02_Assets/Models/Props/         PR_    (slot 06)
02_Assets/Rigs/Character/       RIG_CH_(slot 07)
02_Assets/Rigs/Props/           RIG_PR_(slot 08)
02_Assets/Materials/            M_ MI_ TP_ T_  (slot 09)
02_Assets/Textures/                    (slot 09)
01_Preprod/References/          REF_   (slot 03)
01_Preprod/Storyboard/          SB_    (slot 02)
03_Scenes/Animation/Acting/     SC_ACT_(slot 10)
...
```

Measured contents: **every one of those directories holds only `.gitkeep` and a `*_manifest.txt`.
Zero art files.** (`find Humber_FinalYear_Prep -type f ! -name '*.md' ! -name '*.txt'` → only
`.gitkeep` entries.)

This is the right destination. It is tracked, it is not gitignored, the hook does not touch it, and
`*.png` / `*.blend` / `*.fbx` in it are already LFS-routed by the existing `.gitattributes`. The
slot prefixes (`CH_`, `EN_`, `T_`) are already enforced by `Tools/dogfood_toon_spine.py` slot
checks.

---

## 3. Three policy contradictions to resolve first

These are not new; they were already inconsistent. Staging art will hit all three.

### C1 — `.uasset`/`.umap`: three documents, two positions

| Source | Says |
|---|---|
| `.gitattributes:43` | `*.uasset -text -diff` — **binary, deliberately NOT LFS** (the header comment explains: ~0.4 MB total, LFS would force every teammate to install it to open a material) |
| `Docs/GROUP_WORKFLOW.md:140` | "Big art (`.blend`, `.fbx`, `.exr`, `.mov`, `.psd`, `.spp`) is LFS-tracked; text and `.uasset`/`.umap` are **not**." |
| `Humber_FinalYear_Prep/GROUP_STAGING_GUIDE.md:14` | "All binaries (`.blend`, `.fbx`, `.png`, `.exr`, **`.uasset`, `.umap`**, `.mp4`, `.wav`) **MUST** be tracked with Git LFS." |

The staging guide — the document handed to the 14-person team — contradicts the repo's own
attributes file and the workflow doc.

### C2 — the hook is a latent landmine on C1

`.githooks/pre-commit` check #2 (lines 60–88) **errors** on any staged `.uasset`/`.umap` larger
than 5 MB that is not an LFS pointer, with the fix text "`git lfs track "*.uasset"`".

But `.gitattributes` says those files must *not* be LFS. So the moment one engine package grows
past 5 MB, the hook fires and its own suggested fix contradicts the repo policy. Nothing has hit
it yet because the largest tracked package is 728 KB (`Content/__ExternalActors__/...`), but
`Content/__ExternalActors__/` churns on every level save and the audit already flags it as large.

### C3 — is the art regenerable, or is it source?

`.gitignore:8-9` justifies ignoring `Saved/` with *"they are regenerated by
Blender/stage_brutalist_review.py in minutes."* That is true for the contact sheets. It is **not**
true for the baked PBR maps:

- `Blender/bake_brutalist_pbr.py` is **not tracked on P:** (`git ls-files Blender/ | grep -i
  'pbr\|bake'` → empty; the file exists on D: only, untracked).
- `Blender/export_brutalist_fbx.py` **is** tracked on P: — so the 25 `.fbx` are genuinely
  regenerable, and they are additionally redundant: their `.uasset` counterparts are already
  tracked in `Content/Environment/Brutalist/` (25 meshes).

So the 31 MB of baked maps are **art with no tracked producer**. That is the real gap, and it is a
decision about which side to version: the builder, or the output.

---

## 4. What is actually worth staging

Ranked by whether it serves the stated goal (*every clone is the same*).

| Candidate | Size | Verdict |
|---|---|---|
| Baked PBR maps (70 png) | 31.0 MB | **The real candidate.** Generated art, no tracked producer, needed by every teammate for the material work. |
| Brutalist `.fbx` (25) | 1.3 MB | **Skip.** Regenerable from a tracked builder, and redundant with the tracked `.uasset`. |
| Brutalist review `.blend` (2) | 2.3 MB | **Skip.** `Saved/Blend/` is ignored as cache; these are dated review snapshots (`_2026-09-25`, `_2026-09-30`). If the `.blend` is a source, it belongs in `02_Assets/Models/Environments/` under a proper name, not in `Saved/`. |
| Lookdev grids, screenshots, contact sheets, prototype stills (33) | 29.5 MB | **Skip.** Review artifacts, regenerable, and `Saved/Lookdev/` already shows the anti-pattern — `_v2`, `_v3`, `_v4` of the same grid. |
| Character / rig / prop / storyboard / concept art | 0 | **Does not exist yet.** Slots 02, 03, 04, 06, 07, 08 are empty. This is the art that will actually need LFS, and it is the reason to get the policy right now. |

**Net: the only thing worth staging today is 31 MB of baked PBR maps**, and only if the owner
chooses to version output rather than the builder.

---

## 5. Budget — the constraint that shapes the decision

`Docs/GROUP_WORKFLOW.md:140-145` states the numbers and the standing policy:

> GitHub's free LFS tier is **1 GB storage / 1 GB bandwidth per month**, and bandwidth is consumed
> on every clone and pull by every member.
>
> If repeated clones start exhausting it, the answer is the one the source project already uses:
> **keep bulk art out of git and share it from a drive.** Ask before adding art above ~100 MB.

Arithmetic for a 14-person team:

| | |
|---|---|
| LFS storage (one-time, 31 MB of maps) | 3.1 % of the 1 GB tier |
| LFS bandwidth, one full clone by each of 14 members | 434 MB = **43 % of the monthly tier** |
| Same, if two members re-clone in a month | **86 % of the tier** |

Storage is a non-issue. **Bandwidth is the binding constraint, and it is per-member, per-clone.**
The maps are 1024×1024 PNGs averaging ~440 KB (concrete 3.0 MB for five; `concrete_N.png` alone
is 1.19 MB) — PNG is a poor container for data maps, and that is what makes the bandwidth math
tight.

Also relevant: the repo is **public** (`Docs/AUDIT_2026-09-30.md` F7 refers to "a token in a
public repo"). Anything staged to LFS is publicly fetchable.

---

## 6. Executable plan, once the decisions are made

Assumes: destination is the Capstone scaffold, and the choice is to version the **builder** for
the maps rather than the maps themselves (recommended — see §7).

```
# 0. Owner approves: which repo, which files, and the commit. Per the pipeline law this
#    is a per-operation approval, not a standing one.

# 1. Land the 5 unpushed commits on the authoring repo FIRST (see MATERIAL_WIRING_PLAN.md
#    Part 1). Do not stack new binary history on an unpushed base.

# 2. Copy the bake builder from D: to the authoring repo and TRACK it:
#      Blender/bake_brutalist_pbr.py
#      Blender/bake_brutalist_pbr_supplement.py
#    Without these, the maps cannot be regenerated and §3-C3 stays open.

# 3. If maps are staged (rather than regenerated), put them where the conventions expect:
#      Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/02_Assets/Textures/PBR/<surface>/
#    Naming per CONTENT_CONVENTIONS.md: T_<Surface>_<D|N|R|M|AO>.png
#    NOT Saved/PBR/ — that path is ignored and hook-blocked.

# 4. Confirm the LFS routing before adding anything:
git check-attr filter -- <path>          # must print: filter: lfs
git lfs status                            # must show the object as "to be committed"

# 5. Verify the pointer landed, not the blob:
git show :<path> | head -n 1              # must be the git-lfs spec URL

# 6. Run the gate:
powershell -File Tools/verify_all.ps1
python Tools/dogfood_toon_spine.py

# 7. Commit with a message naming the builder, per CONTENT_CONVENTIONS.md.
```

Environment is ready for this: **git-lfs 3.7.1** installed, endpoint configured
(`https://github.com/fromage3900/film-304-toon-spine.git/info/lfs`, `auth=basic`),
`filter.lfs.process/smudge` set. **0 LFS objects tracked today.**

---

## 7. Recommendation

1. **Do not bulk-stage `Saved/`.** 64 MB of it is review output, regenerable, and three directories
   are already showing version-by-hand drift. Staging it would consume 64 % of the monthly LFS
   bandwidth on every full clone, permanently, for artifacts nobody needs to build the film.
2. **Track the producers, not the output.** Copy the two bake builders to the authoring repo and
   commit those. A tracked builder plus a documented bake command makes the maps reproducible on
   any clone at zero LFS cost — which satisfies "every clone is the same" more cheaply and more
   robustly than versioning 31 MB of PNG.
3. **Fix C1 and C2 before the team adds art.** Decide the `.uasset`/`.umap` position once, make
   `.gitattributes`, `GROUP_WORKFLOW.md`, `GROUP_STAGING_GUIDE.md` and the hook agree, and say so
   in one place. Otherwise the first teammate to commit a large package gets a hook error whose
   suggested fix breaks repo policy.
4. **Reserve LFS for what will genuinely need it**: character meshes, rigs, and animation
   (slots 04, 07, 10, 11). None exist yet. Deciding the policy now is the point.

---

## Decisions needed

1. Version the **maps** (31 MB to LFS) or the **builder** (0 bytes, reproducible)? *(recommend
   builder)*
2. If maps: which repo authors it, and do the 5 unpushed commits land first?
3. `.uasset`/`.umap` — LFS or plain binary? One answer, applied to `.gitattributes`,
   `GROUP_WORKFLOW.md`, `GROUP_STAGING_GUIDE.md` and `.githooks/pre-commit` together.
4. Where does team-shared art live — the Capstone scaffold (recommended), or somewhere else?
5. Do the review artifacts (lookdev grids, contact sheets, screenshots) need to be identical on
   every clone at all, or are they yours alone?
