# Film 304 — task-sheet addendum for Brennan Shepard

**Prepared:** 2026-11-18 · **For:** `Documentation/Tasks-3rd Year Film.xlsx` (the group's
own tracker) and `Documentation/Roles.docx` (currently contains only the word "Roles:").

The tracker's `Tasks` sheet has a row per member with weekly columns
`Sept 20-26 … Dec 6-12`. **Brennan Shepard's row is blank**, and so are most
others. Below is what can be entered, with the evidence for each line.

---

## Roles.docx — proposed entry

> **Brennan Shepard** — Toon shader & material pipeline; procedural environment
> kit; scene 62–66 layout; CAD office module kit; asset UV unwrap.

---

## Tasks sheet — proposed row entries

| Week | Entry |
|---|---|
| Sep 29 – Oct 5 | Toon film spine: master, 15 material functions, 18 toon profiles; texture library generated from code |
| Oct 6 – Oct 12 | Procedural brutalist environment kit (city / office block / cubicle / facade / roof families) shared to the group |
| Oct 13 – Oct 19 | Dana cast staging, v08 preflight, `Jog_Fwd` retarget; MRQ render gate |
| Oct 20 – Oct 26 | Office ceiling + HVAC + trim geometry; Houdini FBX/UV export pipeline |
| Oct 27 – Nov 1 | (no commits recorded) |
| Nov 2 – Nov 8 | ANMN301 animatic timing sheet + shot list; film repo recovery |
| Nov 9 – Nov 15 | (no commits recorded) |
| Nov 16 – Nov 22 | Scene 62–66 layout execution (45 versioned Maya scenes); office trim sheet; CAD office module kit; UV unwrap of 107 canonical assets; converged the modules into the group's textured office set and applied the documented toon shader |

---

## Evidence for each claim

```bash
cd G:/film-304-toon-spine
git log --date=short --format='%ad %h %s' --author='fromage'      # dated history
git log --date=format:'%Y-W%V' --format='%ad' | sort | uniq -c     # per-week counts
ls Film304_Packages/                                             # 5 packages, each with MANIFEST.json (SHA-256)
```

| Claim | Where |
|---|---|
| 78 commits, 2026-09-29 → 2026-11-17 | `git log --author='fromage'` |
| Toon material core | `Film304_Packages/Environment_Assets_2026-11-17/`, `Docs/` |
| Office ceiling + HVAC kit | `Film304_Packages/Ceiling_HVAC_ReusableKit_2026-11-17/` |
| Environment asset kit | `Film304_Packages/Environment_Assets_2026-11-17/` |
| Office trim sheet (8 seamless tiles) | `Film304_Packages/Office_TrimSheet_2026-11-17/` |
| CAD office modules (chamfered, UV'd) | `Film304_Packages/Office_CAD_Pass_2026-11-17/` |
| 107 canonical assets unwrapped + packed | `Film304_Packages/Office_UV_Unwrapped_2026-11-17/01_FBX/` |
| Converged scene + documented toon shader | `Saved/Scenes/S_OfficeScene01_BS_Toon_v01.mb`, `converge_report.json` |
| Scene 62–66 layouts | `Saved/Scenes/L_Scene62-66_BS_v2*.mb` (45 scenes) |
| Canonical group drive (extracted) | `G:/film-304-canon-onedrive/` — 947 files, 107 FBX + 104 Maya sources the repo lacked |

---

## Note on the blank row

This is not an accusation — it is the reason the work has been invisible. The
weekly columns were never filled in for most members, so "who did what" was
never written down. Filling the row (or attaching this addendum to the
workbook) is the single cheapest fix to the "he hasn't contributed" reading.
