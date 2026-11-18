# Film304 Suspended Ceiling + HVAC — Reusable System

**Kit:** `Film304_Packages/Ceiling_HVAC_ReusableKit_2026-11-17`
**Version:** 1.0.0 · assembled 2026-11-17
**Authored:** Brennan Shepherd, 2026-10-18 → 2026-11-17
**DCC:** Houdini (hython, headless) → FBX → Unreal Engine 5.8

---

## 1. What this is

A parametric suspended-ceiling system for the Film 304 office: concrete tile
grid, T-bar suspension, routed HVAC trunk/branch ducting with conduits and
junction boxes, and the six hand-placed light troffers. It is a **system**, not
a one-off mesh — every dimension is a named parameter, and the whole thing is
rebuilt by one script.

It was measured from the live scene, not eyeballed, and it converges against
the room's existing fixtures rather than duplicating them.

---

## 2. Authoritative parameters

Source of truth: `01_Parameters/ceiling_system_config.json`.
Code of truth: `04_Builder/build_office_ceiling.py`.

| Parameter | Value | Meaning |
|---|---|---|
| `ROOM` | 2200.0 cm | floor extent, X and Y, centred on origin |
| `CEIL_Z` | 340.0 cm | underside of the ceiling slab |
| `BAYS` | 20 | 20 × 20 grid |
| `BAY` | 110.0 cm | `ROOM / BAYS` |
| `TILE_SIZE` | 107.6 cm | `BAY − 2.4` cm reveal |
| `TILE_T` | 1.6 cm | tile thickness |
| `TILE_DROP` | 2.5 cm | tile top sits at 335.9 |
| `BAR_W` × `BAR_H` | 2.4 × 3.6 cm | T-bar section |
| `BAR_Z` | 336.4 cm | T-bar top — clears the troffer panels at 336.6 |
| `YAW` | −25.0° | whole room is yawed; baked into the geometry |

**Authority rule:** the room FLOOR (`Film_Floor`) governs. The ceiling slab
(`Film_Ceiling_Slab`) is 100 cm larger per side and deliberately overhangs; the
tile grid matches the floor, not the slab.

---

## 3. Geometry specification

### 3.1 Concrete tile field
20 × 20 = 400 tiles, each 107.6 × 107.6 × 1.6 cm, 2.4 cm reveal between
neighbours, hung so the tile top is 2.5 cm below the slab underside.

### 3.2 Metal — T-bars + HVAC
- **T-bar grid:** 21 runners each way (2.4 cm wide × 3.6 cm deep) at 110 cm pitch.
- **Trunk ducts:** 3 runs, 2080 × 62 × 34 cm, at `y = −800 / 0 / +800`.
- **Branch ducts:** 8 runs, 26 × 460 × 22 cm, at `x = −900 + k·257`, `y = 400`.
- **Service details:** cross branches, joint flanges, threaded hangers, conduit
  runs, junction boxes. Trunk/branch ducting is routed down the service aisle
  (offset 260 cm) to clear the six hero light fixtures.
- **Troffers:** the room's six hand-placed fixtures are **reused, not
  regenerated**. Each is 134 × 105 cm spanning z 336.6–339.6 with a matching
  `RectLight` at z 334. Regenerating a 220 cm emissive grid duplicated and
  contradicted them, so the builder deliberately emits none.

### 3.3 Verified build output

From `06_Evidence/ceiling_native_convergence.json` (native Houdini build, 0 inward
faces asserted per primitive):

| Mesh | Material class | Points | Quads | Inward faces | Bounds (cm) |
|---|---|---|---|---|---|
| `SM_Houdini_Office_Ceiling_Tiles` | Concrete | 3,200 | 2,400 | 0 | ±1460.22 × ±1460.22 × 336.70–338.30 |
| `SM_Houdini_Office_Ceiling_Metal` | Metal | 1,016 | 762 | 0 | ±1462.91 × ±1462.91 × 299.00–350.00 |

FBX hashes are recorded in the same report and in `MANIFEST.json`.

---

## 4. Materials

Three master materials carry the ceiling:

- `M_Concrete_Beam` — tile face
- `M_Duct_Metal` — T-bar and ductwork
- `M_Troffer_Diffuser` — light panel

Scene instances: `MI_Dusk_Ceiling`, `MI_Dusk_Metal` (see the assembly section of
the convergence report).

---

## 5. Export rules (do not change casually)

- **Axis:** Z-up right-handed. `convertaxis = 0`, `convertunits = 0`.
- **Units:** everything authored in centimetres so FBX imports 1:1 into UE 5.8.
- Houdini's polygon winding is clockwise; the builder asserts actual
  `hou` primitive normals rather than assuming cross-product order. Keep that
  assertion — it is what guarantees 0 inward faces.
- See `05_Docs/HOUDINI_FBX_UV_PACKMASTER_PIPELINE.md` for the UV pass.

---

## 6. Reuse recipe (a different room)

1. Copy `01_Parameters/ceiling_system_config.json` and edit `ROOM`, `CEIL_Z`,
   `BAYS`, `YAW`. `BAY` and `TILE_SIZE` derive from `ROOM`/`BAYS`.
2. In hython, run `04_Builder/build_office_ceiling.py`. It writes the `.bgeo`
   cache and presses the FBX ROP.
3. Run `04_Builder/export_headless_fbx_uv.py` for the UV pass.
4. Import into UE with **Z-up, no unit conversion**.
5. Re-instance the two masters above; do not re-author materials.

The builder refuses to run if the geometry leaves the room envelope or leaves
the height band, so a bad parameter set fails loudly instead of shipping.

---

## 7. UE integration

Working map used for verification:
`/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office_Assembly_20261018_v01`

Assembly actors and their material bindings are listed in
`06_Evidence/ceiling_native_convergence.json` → `assembly`.

---

## 8. Provenance

| Artifact | Origin |
|---|---|
| `build_office_ceiling.py` | measured-room builder, 2026-10-18 |
| `bake_cinematic_cubicle_ceiling.py` | HVAC service geometry source |
| `converge_office_ceiling_20261018.py` | native-convergence pass, 2026-10-18 |
| `fit_ceiling_to_main_room_20261018.py` | main-room fit, 2026-10-18 |
| `Content/Meshes/Architecture/**` | UE imports of the above |
| `Saved/Audit/Closeout_20261018/**` | build reports and proofs |

Every file in this kit is hash-listed in `MANIFEST.json` with its source path.
