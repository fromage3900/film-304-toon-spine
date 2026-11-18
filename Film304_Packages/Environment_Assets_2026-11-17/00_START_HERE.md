# Environment Assets Reusable Kit — Start Here

**Assembled:** 2026-11-17 · **Author:** Brennan Shepherd
**Repo:** `G:/film-304-toon-spine`

The environment dressing the Film 304 office and establishing shots — as a
reusable kit, not a pile of one-off meshes. Buildings, blinds, windows and
walls, each with its FBX source, its UE mesh, its materials, and the scripts
that built it. Plus a Houdini COP2 network that generates **measurably
seamless** tilable textures.

---

## What's inside

| Folder | Contents |
|---|---|
| `01_Buildings/` | 25 FBX (city, office block, cubicles, facades, roofs) + 25 UE meshes |
| `02_Blinds/` | Venetian blind bay — FBX (plain + UV), UE mesh, blind materials, bake script |
| `03_Windows/` | Horizon window mesh + FBX, night-window and glass masters, light-rig script |
| `04_Walls/` | Break room wall/floor/shelf meshes, wall + warm-wall material instances, wall build/audit scripts |
| `05_Textures_Tilable/` | 5 COP2-generated textures, **seam = 0.000 on both axes** |
| `06_Houdini_COP/` | `Film304_TilableTextures_v01.hip` + the builder script |
| `07_Docs/` | **`ENVIRONMENT_ASSETS.md`** (asset spec) and **`COP2_TILABLE_TEXTURES.md`** (texture system) |
| `08_Evidence/` | Material review sheets + `seam_report.json` |
| `MANIFEST.json` | Every file: bytes, SHA-256, source path |

---

## Read this order

1. `07_Docs/ENVIRONMENT_ASSETS.md` — what each family is, where it came from, how to reuse it.
2. `07_Docs/COP2_TILABLE_TEXTURES.md` — the COP2 technique and how to rebuild/extend it.
3. `08_Evidence/seam_report.json` — the measured proof that the textures tile.

---

## Provenance

Buildings: procedural brutalist set built W2–W3 from the live scene measurements,
published to FBX 2026-10-04. Blinds/windows/walls: built 2026-10-18 against the
office set. Tilable textures: generated 2026-11-17 with a Houdini COP2 network.
Per-file source paths are in `MANIFEST.json`.
