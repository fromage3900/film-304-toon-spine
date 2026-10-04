# Group workflow

Written 2026-09-30 for a small group (3–6 people) on one Unreal film project. It is short on
purpose: everything here exists because a specific failure already happened, and it names that
failure so the rule does not get "simplified" away later.

## The one rule that matters most

**Never let two people edit the same binary asset — and never let git merge one.**

`.uasset` / `.umap` are binary. Git cannot merge them; if it tries, the result is a file Unreal
cannot open and nobody can recover. `.gitattributes` declares every binary type so git refuses to
attempt a merge, but that only turns corruption into a conflict — it does not stop two people
overwriting each other.

So assign ownership per asset, not per folder:

| Asset | Owner (fill in) |
|---|---|
| `M_Master_Toon_Universal` | |
| `M_Outline_InvertedHull` | |
| `MF_*` functions | |
| `TP_*` toon profiles | |
| `MI_Toon_*` instances | |
| `L_Toon_Lookdev` | |
| `Content/Environment/Brutalist/**` | |

Announce in the group chat *before* you open a shared binary. If you need a variation, make a
**material instance**, not a copy of the master.

## What generates vs what is authored

- `Content/Materials/**` is **generated** by `Python/`. Change the builder, not the asset.
  An editor-only tweak is lost the next time the spine is rebuilt, and the builders are run often.
- `Blender/surreal_arch/**` is a **vendored copy** of the Melodia library. Change it upstream and
  re-extract; never edit the fork in place.
- `Docs/**`, `Tools/**`, `Python/**`, `Config/**` are ordinary text files — normal review.

## Every clone, once

```powershell
git config core.hooksPath .githooks
powershell -File Tools/verify_all.ps1
```

The first line enables the pre-commit gate. **Without it the hook is inert** — git only reads
`.githooks/` if `core.hooksPath` points at it. Check with `git config core.hooksPath`.

## The gate

```powershell
powershell -File Tools/verify_all.ps1     # exit 0 = healthy
```

Eight checks; a report is written to `Saved/Audit/verify_all_<date>.txt` every run so the result
is evidence, not a console scroll. What it covers:

1. fork sync — is the vendored builder set still the code we reviewed?
2. builders build, are acyclic, 21 presets resolve, dials move geometry, cycle guard fires
3. level health — no `__ExternalActors__` references, no self-named packages
4. documented paths actually exist
5. the pre-commit hook still blocks what it claims

**A red gate is not a nuisance, it is the point.** On 2026-09-30 it caught a level whose actors
live in a gitignored folder — meaning every other clone would have opened an empty level.

## Branches and tags

Daily work is on a lane branch; `main` is only what passes the gate.

```powershell
git switch -c feat/<yourname>-<topic>
# ... work, then:
powershell -File Tools/verify_all.ps1        # must be exit 0 to count as done
git add <files>
git commit -m "feat(<area>): <what changed>"
git push -u origin feat/<yourname>-<topic>
```

Then open a pull request. Do not push to `main` directly, and do not force-push a shared branch.

Tag what you showed, so feedback has something to point at:

| Tag | When |
|---|---|
| `assetlist-v0` | the asset list is locked |
| `capstone-preprod-v1` | animatic / beat board export |
| `wkNN-<theme>` | end of each week, after the Friday merge |
| `reel-v2` | review cut |

## Never run these

Not hypothetical. In the source project, `git checkout -- .` silently destroyed uncommitted work
from other sessions, and `git clean -fd` was one interruption away from deleting the protagonist -
the bulk of `Content/` has been untracked at times, and `clean` deletes untracked files with no
copy to restore from.

| Command | Why it is catastrophic here |
|---|---|
| `git clean -fd` / `-fdx` | deletes untracked files; one run can erase art that exists nowhere else |
| `git checkout -- .` | reverts every modified tracked file to HEAD; uncommitted work is not in the object store and `reflog` cannot bring it back |
| `git push --force` on a shared branch | discards other people's commits |
| `git filter-branch` / any history rewrite | breaks every clone the group has |

If you think one of these is the right move: **stop and ask.** There is no situation on this
project where it should happen unprompted.

## Never commit these

- `Intermediate/`, `Saved/`, `Binaries/`, `DerivedDataCache/` — build output. The hook blocks them.
- `*.blend1` / `*.blend2` — Blender autosaves.
- **Not** `Content/__ExternalActors__/**` — those are **TRACKED** since 2026-10-01 (they are the
  level's actor data). See "The external-actors policy" below.
- Anything over ~50 MB that is not LFS-tracked.
- OS junk, editor junk, archives.

Evidence **is** committed: `Saved/Audit/*.json|md|txt` is allowlisted, because a report plus the
harness that produced it is evidence, while a PNG on its own is not.

## The external-actors policy (reversed 2026-10-01)

`L_Toon_Lookdev` is a **World Partition** level: its actors are stored as separate
`/Game/__ExternalActors__/...` packages. The repo used to gitignore that folder on the theory
that it is "regenerated with the .umap". It is not — for a WP level those packages **are** the
actor data, so every fresh clone opened an empty level (audit finding F1).

**The folder is now tracked.** What that means in practice:

- **Do** commit `Content/__ExternalActors__/**` when it changes. It is not noise.
- Do **not** hand-edit anything in it. Regenerate the level with
  `Python/build_test_level.py`, or edit the level in the editor and let it write the packages.
- It is large and churns on every level save — expect big diffs and treat them as normal.
- `Tools/verify_all.ps1` now fails only if a level references external actors that are **not
  present on disk**, which is the failure that actually loses the level.
- The pre-commit hook permits the folder (it used to block it). If a clone still opens the
  level empty, the externals were not committed — re-run the gate and read the count it reports.

## When you add assets

Big art (`.blend`, `.fbx`, `.exr`, `.mov`, `.psd`, `.spp`) is LFS-tracked; text and
`.uasset`/`.umap` are not. GitHub's free LFS tier is **1 GB storage / 1 GB bandwidth per month**,
and bandwidth is consumed on every clone and pull by every member.

If repeated clones start exhausting it, the answer is the one the source project already uses:
keep bulk art out of git and share it from a drive. Ask before adding art above ~100 MB.

## Reporting a problem

Include the gate output. Run `powershell -File Tools/verify_all.ps1` and paste the failing line
plus `Saved/Audit/verify_all_<date>.txt`. "It doesn't work" costs a day; a failing check name and
its evidence costs ten minutes.

