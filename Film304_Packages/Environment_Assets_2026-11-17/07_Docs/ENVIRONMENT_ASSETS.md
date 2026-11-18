# Film 304 — Environment Assets

Buildings, blinds, windows and walls: what each family is, where it came from,
and how to reuse it.

**Author:** Brennan Shepherd · **Built:** 2026-10-04 → 2026-10-18 · **Packaged:** 2026-11-17

---

## 1. Buildings — `01_Buildings/`

A procedural brutalist set in six families, 25 meshes. Built W2–W3 from the
live scene's measurements so the group had geometry to dress with before
anyone else had layout.

| Family | Folder of origin | Meshes |
|---|---|---|
| City, PBR | `01_CITY_PBR` | CivicSuperblock, LowSprawl, TightEstate, TowerCluster |
| City, Komikaze toon | `02_CITY_KOMIKAZE` | same four |
| Office block | `03_OFFICE_BLOCK` | BarbicanScale, Bunker, CivicSlab, SlenderTower |
| Interior cubicles | `04_INTERIOR_CUBICLES` | Canonical, MazeShift, OpenPlan, Swarm |
| Facade variation | `05_FACADE_VARIATION` | CivicColonnade, PunchedEstate, TowerRibbon |
| Roofs | `06_ROOFS` | BarrelVault, FlatParapet, LowPitch, PlantDeck, PyramidHip, Sawtooth |

- **FBX** in `01_Buildings/FBX/` — exported from the capstone scaffold.
- **UE meshes** in `01_Buildings/UE/` — the `/Game/Environment/Brutalist/**` imports.
- Review sheets (cast-sphere and palette grids) are in `08_Evidence/`.

**Reuse:** the FBX files are standalone. Import into any DCC or UE project;
the scaffold's two material treatments (PBR and Komikaze toon) are both
represented in the mesh set.

---

## 2. Blinds — `02_Blinds/`

`SM_VenetianBlinds_Bay` — the venetian bay that dresses the office glazing.

- `SM_VenetianBlinds_Bay.fbx` / `..._uv.fbx` — source meshes, with and without the UV pass.
- `SM_VenetianBlinds_Bay.uasset` / `..._uv.uasset` — UE imports.
- `MI_OfficeSpider_Blinds.uasset`, `MI_Dusk_Blinds.uasset` — scene material instances.
- `T_SDF_Blinds.uasset` — the SDF blind pattern driving the toon shade.
- `bake_cinematic_window_blinds.py` — the headless bake that produced the geometry.

---

## 3. Windows — `03_Windows/`

- `E1_horizon_windows.fbx` + `SM_E1_HorizonWindows.uasset` — the establishing-shot horizon glazing.
- `M_Film304_NightWindows.uasset` — emissive night-window master.
- `M_WindowGlass_Restored.uasset` / `MI_WindowGlass_Restored.uasset` — restored architectural glass.
- `MI_Dusk_HorizonWindows.uasset` — dusk scene instance.
- `build_window_light_rig_20261018.py` — builds the window light rig that backs the glazing.

---

## 4. Walls — `04_Walls/`

- Break room shell: `SM_O_BreakRoomWall_`, `SM_O_BreakRoomFloor_`, `SM_O_BreakRoomShelf_`, and the combined `SM_BreakRoomTogether_` (OneDrive rigs, 2026-10-16).
- Wall materials: `MI_Film304_Wall`, `MI_Film304_WarmWall`, `MI_Dusk_Wall`, `MI_Dusk_WarmWall`, `MI_Film_Wall`, `MI_Film_WarmWall`.
- Build/audit scripts: `build_south_wall.py`, `extend_north_wall.py`, `fix_walls_pos.py`, `find_perimeter_walls.py`, `inspect_walls.py`, `inspect_backwall.py`, `check_wall_gaps.py`, `check_wall_materials.py`, `check_wall_visibility.py`.

---

## 5. How these were used

- The building set dressed the establishing shots and the dusk city.
- Blinds and windows carried the window-hero and dusk-glazing sequences.
- The wall set plus the ceiling/HVAC kit (see the sibling
  `Ceiling_HVAC_ReusableKit_2026-11-17`) closed the office interior.

---

## 6. Verification

Every file is hash-listed in `MANIFEST.json` with its source path, so any
claim here can be checked against the repo.
