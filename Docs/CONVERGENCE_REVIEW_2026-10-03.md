# Convergence review — 2026-10-03

Deep review of what changed and what remains to converge across origin, P: (editor
authority) and D: (portable SSD). Read-only; no pushes performed.

---

## 1. Where the three copies stand

| | HEAD | dirty | LFS | notes |
|---|---|---|---|---|
| `origin/feature/canon-pipeline-scaffold` | `e1ef17e` | — | 0 | **9 commits behind P:** |
| `origin/main` | `ae153e6` | — | — | untouched all session |
| P: (live editor, PID 16068) | `8277231` | 12 | 138 | **9 commits ahead of origin** |
| D: (portable SSD) | `8277231` | 1 | 138 | now identical to P: |

P: and D: are **identical** at `8277231`. The only divergence left is against origin.

`origin/feature` has not moved all session — everything is local.

---

## 2. What changed this session

### Committed on P:, not pushed (9 commits, 305 files, +13,374 / −151)

```
8277231 chore(repo): land remaining toon/office working-tree changes and evidence
2954dbf feat(art): stage project art to LFS and close the toon character profiles
94936c3 feat(toon): baked SDF stroke map as CellIndex 12 + spine regeneration
1eb8e57 fix(toon): six graph wiring defects + rebuild tooling
2fc9899 fix(gate): exempt a level's own package path from the mis-named-package check
701c3b6 feat(shots): brutalist import, shot-env composition, and 8-shot prototype render
8e15e1d feat(office): generate office toon materials and assign them to the meshes
4748a6b feat(textures): generate the toon texture library from code
c10fa71 feat(toon): generated graph rebuild safety + 4 new SDF patterns
```

Only two of these are mine (`2954dbf`, `8277231`). The other seven landed from parallel
work during the session — I did not author them and have not reviewed their content.

### My changes

- **Art staged to LFS** — 138 files, 58 MB, into the tracked Capstone scaffold (not
  `Saved/`, which is gitignored and hook-blocked). All LFS pointers.
- **TP_Melusina + TP_Character** authored — the manifest's declared canonical character
  profile, which existed in neither repo.
- **RampStrength set** on the character instances (the trap that made every profile inert).
- **Two plan docs**: `Docs/MATERIAL_WIRING_PLAN.md`, `Docs/ART_STAGING_LFS_PLAN.md`.
- **UDS un-staged** on D: (848 files). The gitignore rule already existed at line 69; the
  index was overriding it.

### D: rescue

D:'s working tree was **newer** than P:'s commits (12:37–13:00 vs 10:59) and held work P:
does not have. I recommended fast-forwarding D: to P: — that was wrong and would have
destroyed it. Git refused on 68 conflicting paths, which is the only reason nothing was
lost. D:'s state is preserved on branch `salvage/d-working-20261003` (`b697d6a`) and at
`D:\film304-sync-backup-20261003` (130 files).

---

## 3. What remains to converge

### C-1 — Push P:'s 9 commits to origin (BLOCKING the desktop handoff)

`origin/feature/canon-pipeline-scaffold` is at `e1ef17e`. The desktop cannot pull any of
this work until it moves. Push payload: 305 files, 13,374 insertions, plus **138 LFS
objects / 58 MB**.

**LFS bandwidth warning.** `Docs/GROUP_WORKFLOW.md` sets the free tier at 1 GB storage /
1 GB bandwidth per month, consumed on every clone by every member. 58 MB stored is fine;
14 teammates cloning once is ~812 MB — most of the tier. Uploading is cheap; the *next*
person's clone is not.

### C-2 — The salvage branch holds 13 files P: does not have

`git diff --name-status refs/remotes/laptop/fps salvage/d-working-20261003`:

```
A  Content/Materials/Functions/MF_SurfaceBlend.uasset     9,970 bytes
A  Blender/bake_brutalist_pbr.py                          the bake producer
A  Blender/bake_brutalist_pbr_supplement.py               "
A  Python/build_mf_pbrdetail.py                           "
A  Python/build_mf_surfaceblend.py                        "
A  Python/import_pbr_textures.py                          "
A  Python/apply_outline_overlay.py
A  Python/probe_toon_bsdf.py
A  Docs/TOON_PIPELINE_REFERENCE.md
A  PLAN_UNIVERSAL_INDIE_FILM.md
A  LICENSE
A  Saved/Audit/pbr_bake_manifest.json
A  Saved/Audit/toon_bsdf_probe.json
```

**This directly answers the wiring plan's open item.** `MF_SurfaceBlend` was listed as
"exists nowhere / never built" — it exists, on D:, and its builder
(`Python/build_mf_surfaceblend.py`) exists too. So do both bake builders, which the
staging plan flagged as untracked-on-both-drives. Recovering these 13 files closes two
open items at once.

Also in the salvage diff: 77 modified and 175 deleted files. The 175 deletions are mostly
the LFS art, which salvage does not carry — **do not merge salvage wholesale.**

### C-3 — The two gates have diverged

| | P: | salvage (D:) |
|---|---|---|
| checks | **8** | **11** |
| script size | 11,309 bytes | 17,797 bytes |

Salvage's gate has three checks P:'s lacks:
`material functions are referenced`, `all enabled plugins are engine built-ins`,
`no hardcoded absolute plugin paths`.

P:'s gate passes 8/8. But the check that catches an orphaned material function — the exact
failure class that hit `MF_ProceduralPatterns` (audit F6) and then `MF_PBRDetail` — is
**only in the salvage version**. Whichever gate is authoritative needs deciding, and the
three missing checks are worth having.

Note: `powershell -File Tools/verify_all.ps1` fails on this machine with
`running scripts is disabled`. Needs `-ExecutionPolicy Bypass`. That is an environment
issue, not a repo one, but it will bite a teammate.

### C-4 — Uncommitted work on P: (12 files)

Staged (10): the gouache lane — `M_PainterlyGouache.uasset` (38,653 → 42,449 bytes), four
`T_Gouache_*` textures, `build_gouache_material.py`, `build_gouache_textures.py`, new
`build_gouache_lookdev.py` (412 lines), and two reports.

Unstaged (3): `Blender/FORK_SYNC.json`, `Blender/surreal_arch/melodia_gn/core.py`
(+261/−13 lines — a substantial fork change), and `build_gouache_lookdev.py`.

The fork change is the notable one: the vendored `core.py` is 261 lines ahead of its
committed state, and the gate's fork-sync check passes. That means the vendored copy now
matches upstream, and the change should be committed or it will drift again.

### C-5 — Editor state is clean and consistent

Checked live:
- `list_dirty_packages` → **0**. No unsaved editor work.
- Master on disk is byte-identical to HEAD.
- 21 ToonProfiles on disk = 21 in repo. 20 instances = 20. Editor agrees (21/21, 20/20;
  the editor's 21 instances include the outline pair).
- Master's `dependencies` are `MF_ColorRamp3`, `MF_PBRDetail`, `MF_ProceduralPatterns`,
  `MF_RampLUT` — so **`MF_PBRDetail` is now wired**, closing the orphan state I flagged
  earlier. `MF_SurfaceBlend` is not.

**No editor work is at risk.** Everything is on disk.

---

## 4. Recommended order

1. **Commit P:'s 12 dirty files** (gouache + fork). They are finished work sitting
   uncommitted, and the fork change is drift waiting to happen.
2. **Recover the 13 unique files from salvage** — `MF_SurfaceBlend`, both bake builders,
   `build_mf_surfaceblend.py`, `import_pbr_textures.py`. Copy files, do not merge the
   branch (175 deletions would come with it).
3. **Decide the gate**: port salvage's three extra checks into P:'s `verify_all.ps1`, or
   accept P:'s 8. Recommend porting — the orphaned-function check is the one that keeps
   catching real defects.
4. **Push the 9+ commits** to origin. This is the only step that unblocks the desktop.
5. **Only then** sync D: forward again, and re-verify the LFS objects materialise.

## 5. Open decisions

1. Push now, or commit the 12 dirty files first? *(recommend commit first — one push)*
2. Gate: port the three checks, or accept 8?
3. The 138 LFS objects / 58 MB: accept the bandwidth cost, or move bulk art off git to a
   shared drive as `GROUP_WORKFLOW.md` already anticipates?
4. Delete `salvage/d-working-20261003` once its 13 files are recovered? It is a local-only
   branch on D:.
5. Is the gouache lane (`M_PainterlyGouache`) in scope for this film, or an experiment?
