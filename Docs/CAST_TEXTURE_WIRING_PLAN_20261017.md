# Cast texture wiring + scene setup plan — 2026-10-17 (evening)

**Owner asks (2026-10-17):** do for every rig what was just done for Dana; place the cast
next to each other in the current level; keep a standing `/goal`//`cron` running until every
asset is in the scene with its proper material wiring.

**Deferred, not cancelled:** trimming `M_Master_Toon_Universal`. Its purpose is **handoff
hygiene** — the Humber collaborators should not receive Melodia's shader functions, only what
the film needs. The cast master set is already film-owned and small; the trim is a separate
offline job when the handout is prepared.

---

## 0. The two defects being fixed, per rig

| Defect | Cause | Fix |
|---|---|---|
| **Skin renders white / wrong tile** | The importer combined each rig's 3 UDIM tiles into one 6144×2048 strip per asset, so `frac(UV)` samples the leftmost third — the head tile — for the whole body | Re-import the tiles from clean-named copies (no `.1001` pattern), enable VT, rebind the three tile params |
| **Blank white eyes** | The iris is a per-face material split on the eyeball; the import chain assigned each duplicate wholly to its first shading engine, so iris faces inherit sclera | Needs an offline Maya export with per-face splits preserved (Dana: done as v09) |

Both defects are **import-time**, not material-graph, defects. No master edit fixes either.

## 1. Verified current state

**Masters** (`/Game/Materials/Masters/OneDriveRigs_20261016/`): `UDIM` (3-tile skin),
`Albedo` (single BaseColorMap), `Character` (tint only), `Eyes`, `Environment`,
plus `M_Master_UniversalToon_DanaFilmClean_20261016` (a 762 KB copy of the Universal master).

**Instances** — a full parallel set per character:
`MI_OneDriveRigs_{Dana,David,Sam}_{Skin,Hair,Shirt,Skirt→Cloth,Shoes,EyeWhite,EyeInterior,Iris,Cornea,Detail,Mouth}`;
Spider has `Body / Eye / Fang`.

**Staged meshes** (`/Game/Staging/CastRigs_20261016/`): `David_v151_Deform_v3`,
`Sam_Deform_v3`, `Spider_Deform_v2` (+ physics), `Dana_CleanSkin_v08` elsewhere.

**Dana — done.** Skin on the 3-tile UDIM master (correct 2048² tiles), shoes atlas bound,
pants reparented to the Albedo master with the atlas bound. Verified dark in a fresh render;
the only white left is her blank eyes, which v09 fixes.

**David / Sam — known broken.** Their skin tiles are the same 6144×2048 combined strips
(measured: `T_David_Skin_D_100*.uasset` = 8,971,405 bytes ×3; `T_Sam_Skin_D_100*` =
11,774,187/11,774,187/11,774,188). Same fix as Dana's.

**Spider — unmeasured.** Body/Eye/Fang, no skin tiles. Probe before assuming.

## 2. Per-rig runbook

For **each** of David, Sam, Spider:

1. **Stage clean-named texture copies** to
   `Saved/OfflineIntake/20261017/skin_tiles/<rig>/` — one file per tile, no `.1001`
   pattern, or the importer regroups them into a strip.
2. **Re-import** as 2048² sRGB DXT1; **enable VT streaming** (the UDIM master samples
   `SAMPLERTYPE_VirtualColor`); save.
3. **Rebind** `BaseColorTile1001/1002/1003` on that rig's `MI_OneDriveRigs_<Rig>_Skin`.
4. **Shoes/pants:** confirm the rig's shoes atlas (`T_<Rig>_Shoes_D`) is bound on the Shoes
   instance; reparent the Cloth/pants instance to the `Albedo` master and bind the same atlas.
5. **Verify by re-read** — never trust the tool's OK. Then a lookdev render, viewed, with the
   level's own lights.
6. **Face/eyes:** offline Maya pass (same chain that produced Dana's v09) to preserve the
   per-face iris split and export morphs. This is the only step that needs a DCC.
7. **Place in `L_Film_Office`**, spaced next to Dana, floor-snapped, facing camera.

**Spider:** measure first — source is `C_Spider.ma`, so its material split and UV convention
are unknown. Report, then wire.

## 3. Definition of done

Per rig: skin reads as authored skin tone with no tile seams; shoes and pants show the atlas;
no blank-white eyes; the actor is in `L_Film_Office` beside Dana, floor-snapped; a viewed PNG
proves it. Whole cast: all four standing in the level, all evidence PNGs in
`Saved/Renders/universal_film_styles/`.

## 4. The standing task

A `/cron`-style loop runs until §3 is met. Each tick: check which rigs are still missing or
unwired, do the next bounded step for one of them, record evidence, and stop when done. The
loop is the driver, not a substitute for the runbook — it advances the same steps.

## 5. Guardrails

Do not edit `M_Master_Toon_Universal` or any shared function. Do not delete the broken
6144×2048 textures until every instance is off them. Never present a derived normal map as
author-supplied. Never place a T-posed or floating character and call it set up. One editor,
one mutating surface. Save every instance immediately after changing it — an unsaved
reparent is silently reverted by the next package reload.
