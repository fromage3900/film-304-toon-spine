# Film 304 — Office Asset & Full PBR Pack (v2.0 — NumPy Procedural Pipeline Upgrade)

**Assembled:** 2026-11-18 · **Author:** Brennan Shepherd

Upgraded procedural asset & texture package for the Film 304 office set:
1. **`01_CAD_Pass/`**: 8 parametric chamfered & UV-unwrapped office modules (`.fbx`), plus **`baked_maps/`** containing 1024×1024 UV-rasterized mesh curvature & cavity AO maps baked directly from the Houdini per-polygon `curvature` attribute via our NumPy rasterizer.
2. **`02_TrimSheet/`**: Detailed 8-tile architectural trim sheet atlas (`2048x1024` standard + `4096x2048` 4K master + `tiles_512/` individual strips) across 8 PBR channels (`Albedo`, `Height`, `Normal`, `ORM`, `Roughness`, `Metallic`, `AO`, `Curvature`). Normals and cavity AO are computed per-tile with toroidal boundary wrapping so cross-tile bleed is eliminated (`0.0000` per-tile seam error).
3. **`03_TilableTextures/`**: 8 complete office material families (`Blinds`, `Concrete`, `Facade`, `Hatch`, `MetalPanel`, `CarpetFloor`, `OfficeWall`, `WoodLaminate`) × 7 full PBR maps (`BaseColor`, `Height`, `Normal`, `Roughness`, `Metallic`, `AO`, `ORM`) at both `1024x1024` and `512x512`, plus drop-in root `T_Tilable_<Name>_512.png` files — all verified at `seam_left_right = 0.0` and `seam_top_bottom = 0.0`.
4. **`04_MayaTest/`**: `L_Scene62-66_BS_v28_cad_pass.mb` composed layout scene with documented Arnold `aiToon` look.
5. **`05_CanonDriveIndex/`**: Canonical shared drive index (`canon_index.json`).
6. **`06_ContactSheets_and_Pipeline/`**: Visual contact sheets, 3×3 seamless tiling proof sheet, and the standalone reproducible NumPy generator (`film304_numpy_pbr_pipeline.py`).
