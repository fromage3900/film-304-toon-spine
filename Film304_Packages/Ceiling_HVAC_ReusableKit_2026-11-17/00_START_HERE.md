# Ceiling + HVAC Reusable Kit — Start Here

**Assembled:** 2026-11-17 · **Author:** Brennan Shepherd
**Repo:** `G:/film-304-toon-spine` · **Size:** 4.8 MB · **Files:** 48

A parametric suspended-ceiling system for the Film 304 office — concrete tile
grid, T-bar suspension, routed HVAC ducting with conduits and junction boxes,
and the six hand-placed light troffers. Rebuildable at any room size.

---

## What's inside

| Folder | Contents |
|---|---|
| `01_Parameters/ceiling_system_config.json` | The whole system as named parameters — edit these to re-instantiate |
| `02_Houdini/` | `.hip` scenes, `.bgeo.sc` geometry caches, exported FBX |
| `03_UE_Assets/Meshes/` | UE 5.8 static meshes + FBX sources (converged v02/v03, main-room fit v04/v05, HVAC grid v1/v2) |
| `03_UE_Assets/Materials/` | `M_Concrete_Beam`, `M_Duct_Metal`, `M_Troffer_Diffuser` |
| `04_Builder/` | The measured builder + convergence, fit, UV-export and audit scripts |
| `05_Docs/` | **Read `CEILING_SYSTEM.md` first** — full spec, verified numbers, reuse recipe |
| `06_Evidence/` | Build reports, manifests and before/after renders |
| `MANIFEST.json` | Every file, its byte count, SHA-256 and its source path in the repo |

---

## Read this order

1. `05_Docs/CEILING_SYSTEM.md` — the system spec and the reuse recipe.
2. `01_Parameters/ceiling_system_config.json` — the knobs.
3. `06_Evidence/ceiling_native_convergence.json` — the verified build report
   (3,200 points / 2,400 quads tiles, 1,016 / 762 metal, **0 inward faces**).
4. `06_Evidence/ceiling_hvac_troffers_assembled.png` — the assembled result.

---

## Why it is reusable

Every dimension is a parameter, not a baked number. Change `ROOM`, `CEIL_Z`,
`BAYS` or `YAW` in the config, run the builder in hython, and the tile field,
T-bar grid and duct runs regenerate. The builder asserts the geometry stays
inside the room envelope and the ceiling height band, so a bad parameter set
fails loudly instead of shipping.

Details, including the export rules that must not change:
`05_Docs/CEILING_SYSTEM.md`.

---

## Provenance

Built 2026-10-18 from the live office scene, converged natively in Houdini,
imported and verified in UE 5.8, and re-packaged as a reusable kit 2026-11-17.
Commit and per-file hashes are in `MANIFEST.json`.
