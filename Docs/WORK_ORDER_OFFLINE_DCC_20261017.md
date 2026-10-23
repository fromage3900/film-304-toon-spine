# Offline DCC work order — Dana film lane (Maya + Houdini), 2026-10-17

Copy the block in **§0** verbatim to the offline agent. §1–§2 are the reasoning and the
evidence behind it, for a human reading this file.

---

## §0 The prompt

You are an **offline DCC agent** for a Unreal 5.8 film project. You have **Maya** (`mayapy`),
**Houdini** (`hython`), and optionally **Blender**. You do **not** have the Unreal editor and
you must never touch it, git, or Perforce.

### Project

- Unreal film project (read-only for you): `G:\film-304-toon-spine` — project name `HumberToonShader`
- Source assets (**read-only, never modify, never write here**):
  `G:\Film304_AssetIntake_20261016_Source`
- Deliverables go to:
  `G:\film-304-toon-spine\Saved\OfflineIntake\20261017\<task_id>\{fbx,report,preview,log}`
- **Never write** into any `Content/` folder, into the source root, or over any `.mb`/`.ma`.
  Copy a source to your own scratch path before working on it.

### Read this prior art before writing anything

- `Saved\Audit\MayaDanaNative_20261016\` — Dana native export candidates v03–v08 + expected-mesh manifests
- `Saved\Audit\CastMayaExport_20261016\` — David/Sam/Spider census + FBX-content reports
- `Saved\Audit\MayaDanaRoundtrip_20261016\` — Maya export verified by independent Houdini readback
- `Saved\Audit\HoudiniDana_20261016\`, `HoudiniDanaHidden_20261016\` — FBX read-only probes
- `Saved\Audit\OneDriveRigs_20261016\intake.json` — every source path, per asset
- `Docs\CAST_RIGS_2026-10-16.md`, `Docs\DANA_ACTION_SHOT_RUNBOOK.md`

### Tools to EXTEND, not replace

`Tools\export_dana_clean_skin_v08.py`, `Tools\export_dana_film_from_maya.py`,
`Tools\export_cast_from_maya.py`, `Tools\consolidate_fbx_for_ue.py`,
`Tools\inspect_dana_native_maya.py`, `Tools\verify_dana_native_export_houdini.py`,
`Tools\probe_fbx_contents.py`, `Tools\audit_dana_deform_hierarchy.py`.
If you believe a new script is required, say so and say why — do not silently fork the chain.

### Hard rules

1. `1 uu = 1 cm`. The existing exporter handles the Z-up→UE conversion; keep it.
2. **Preserve the skeleton.** Dana's deform skeleton is 1,230 bones. Do not re-rig, do not
   rename bones, do not add/remove bones.
3. **Preserve material slot names exactly** (the UE film lane keys its material mapping on
   these 10 names): `danaskin_mat`, `danahair_mat`, `danaeye_mat`, `danacornea_mat`,
   `danaeyeint_mat`, `danapants_mat`, `danashirt_mat`, `danashoes_mat`, `danagum_mat`,
   `danatongue_mat`.
4. Bind pose is a **T-pose**, nose on local **+Y**. Keep both.
5. **Every claim needs evidence**: a machine-readable JSON report measuring the *exported*
   FBX (read back by a second tool), plus a rendered PNG preview. A log that says "success"
   is not evidence. Write `"not verified"` rather than guessing.
6. Do not import anything into Unreal. The UE side imports once, itself.

### TASK 1 — Dana facial shapes and eye setup (BLOCKER, highest value)

Facts: `Dana_CleanSkin_v08` = 46,041 tris, 1,230 bones, 10 material sections,
**0 morph targets**. Rendered stills read dead because nothing can blink or emote.
Separately, the cornea slot is currently mapped to a hidden-material helper and **no iris slot
survives the import** — the eyes render as blank spheres.

- 1a. Open `G:\Film304_AssetIntake_20261016_Source\3rd Year Film\Rigs\Temp\Dana_Rig_v1.5\Dana_Rig_v1.5.mb`
  and **report what facial controls actually exist**: blendshapes (exact names + count),
  or a bone-driven face, or nothing. Do not invent geometry.
- 1b. Report the eye setup: is the iris separate geometry? Which source material does the
  cornea/iris use, and what is lost by the current 10-slot mapping?
- 1c. If blendshapes exist, export `Dana_CleanSkin_v09.fbx` **with morph targets preserved**,
  keeping tris / bone count / section names identical to v08.
  Minimum useful set (only if the rig has them): `Blink_L`, `Blink_R`, `Brow_Up`, `Brow_Down`,
  `Smile`, `Frown`, `Mouth_Open`, `Mouth_Wide`, `Jaw_Open`, `Eye_Look_L`, `Eye_Look_R`,
  `Eye_Look_Up`, `Eye_Look_Down`. Report any that are missing.

**Acceptance:** a JSON report listing the morph names that survive the *export* (verified by
an independent Houdini readback of the FBX), confirming tris/bones/sections unchanged; plus a
preview PNG of the head with 3 shapes at value 1.0.

### TASK 2 — Dana film pose/clip set

Author on Dana's rig, as FBX animation (not a new rig):

- `IDLE_A` — held idle, 8–16 frames
- `GESTURE_B` — a speaking/talking gesture for the right arm
- `LOOK_L` — head/torso turn
- `WALK_IN` — no root motion

No root motion, no joint scale animation. Frame 0 must be grounded (lowest mesh Z = 0 ± 1 mm).

**Acceptance:** one FBX per clip (or one file with named takes) + a JSON report naming the
frame ranges and the measured frame-0 min-Z, + a PNG of frame 0 per clip.

### TASK 3 — break-room set kit scale repair (BLOCKER)

Facts measured in Unreal 2026-10-17: the kit imports at roughly **1/5 life size**.
`SM_BreakRoomTogether_ZMJ` bounds = 111.2 × 54.6 × 60.0 uu; `SM_O_Counter_ZMJ` =
58.8 × 12.8 × 15.6 uu; the shot cameras sit at z = 20–26 uu **inside** the shell, and frames
rendered from inside show sky **through** the walls (the camera frames nothing).

Sources (`G:\Film304_AssetIntake_20261016_Source\3rd Year Film\3D Models\FBX Files\`):
`BreakRoomTogether_ZMJ.fbx`, `O_BreakRoomFloor_ZMJ.fbx`, `O_Counter_ZMJ.fbx`,
`O_CounterTop_ZMJ.fbx`, `O_EspressoMachine_ZMJ.fbx`, and the rest of the `O_*` kit
(enumerate them from `intake.json`).

- 3a. Measure every source FBX: bounding box, unit metadata, object count. Report whether the
  intended scale is recoverable from the file, or whether it must be chosen from real-world
  reference. State the factor you used and why.
- 3b. Re-export the kit at true scale into `fbx/`.
- 3c. Check the shell's normal orientation and report it: from a camera inside the room all six
  surfaces must be visible (no see-through walls). Fix if needed.

**Acceptance:** room width ≥ 450 cm, ceiling 260–300 cm, counter top 88–105 cm high with
55–70 cm depth; a JSON with before/after bounds per mesh; a rendered PNG from inside the room
showing the walls.

### TASK 4 — Dana UDIM skin: UV audit and (optionally) a single-tile repack

Facts: the skin albedo is UDIM — `Dana_Diffuse.1001.png`, `.1002`, `.1003`
(`...\Rigs\Temp\Dana_Rig_v1.5\TexturesDana\Dana_Skin_Texture\`), imported as
`T_Dana_Skin_D_1001_20261016` etc.

**Update 2026-10-17:** the tile *content* is now known — **1001 = head/face**, **1002 = hands
and body panels**. A 3-tile If-chain master already exists in-engine
(`M_OneDriveRigs_FilmToon_UDIM_20261016`: `frac(UV)` sample UV, `floor(u)` tile select, nested
`If`) and compiles at 456 pixel instructions, so multi-tile skin **is** renderable today. What
is still unknown is the mesh's actual UV range.

- 4a. In Maya, load `Dana_Rig_v1.5.mb` and report the **UV bounding box of the skin geometry**
  in `map1`: min/max U, min/max V, and how much geometry lives in each U range
  (`[0,1)` / `[1,2)` / `[2,3)`). This single measurement decides the whole skin binding.
- 4b. Report which UV islands belong to which body region, so the UE side can predict what
  each tile paints.
- 4c. **Optional (only if 4a shows a clean 3-band split):** re-lay the UVs into a single 0–1
  set and repack the three tiles into one ≤ 4096² texture, so skin needs one bind and no
  tile logic. Do this only if no UV island would drop below 50 % of its current texel density.
  If in doubt, skip — the If-chain master already works.

**Acceptance:** a JSON with the measured UV bounds and per-tile geometry fractions (4a) and the
island→region map (4b); a preview PNG per tile with the island borders overlaid. 4c, if
attempted, adds the repacked texture + before/after texel-density numbers.

### TASK 5 — cast rig readiness (second wave)

Facts: David/Sam/Spider Deform meshes were imported raw (`David_v151_Deform_v3`,
`Sam_Deform_v3`, `Spider_Deform_v2`) with no validated bind/scale gate. Sources:
`Rigs\Temp\David_Rig_v1.51\David_Rig_v1.51.mb`, `Rigs\Guy\Sam Rig\C_Guy.mb`,
`Rigs\Spider\C_Spider.ma`.

Run the same clean-skin chain that produced `Dana_CleanSkin_v08` for each: T-pose, true scale,
skeleton preserved, slot names normalized to the film lane's part mapping, census JSON.

**Acceptance:** per character — height (cm), tris, bones, sections, morph count, + preview PNG.

### TASK 6 — hair (optional, only after 1–3)

Dana's hair is a single solid mesh. Hair cards or a groom would suit the toon look better.
Propose before doing.

### TASK 7 — derived surface-detail maps (normal / AO / curvature) — NEW 2026-10-17

**Fact first, so you do not hunt for files that do not exist:** the source rigs ship
**diffuse-only**. Measured across the entire intake there are 18 image files — 12 `*_Diffuse`
PNGs and 6 FAQ JPGs — and **no `_N`, `_Normal`, `_NRM`, bump, roughness, AO or height map for
any of the three rigs**. The rig author's own `FAQ\TextureSetup.jpg` shows a Maya blinn with a
color input only. There are no normal maps to import; any detail must be **derived**.

- 7a. In Houdini, import `Dana_CleanSkin_v08` (or the source FBX for it) and bake, per UDIM
  tile, an **AO map**, a **curvature map**, and a **tangent-space normal derived from the
  AO/curvature height field**. Resolution 2048², matching the existing tile split. This is
  real surface detail from real geometry — cavity, creases, contact shading — not noise.
- 7b. Also bake the **shoes/legwear atlas** (`DanaShoes_Texture.png` is a single non-UDIM tile
  that visibly contains both shoe and legwear islands).
- 7c. Label every output `derived` in the report and in the filename. These are not
  author-supplied maps and must never be presented as if they were.

**Acceptance:** per map — the PNG, plus a JSON recording source mesh, bake resolution, tile
assignment, and the Houdini node graph used; a preview PNG of the head with the derived normal
applied, so the UE side can judge whether the detail is worth binding.

### Deliverable contract (every task)

```
Saved\OfflineIntake\20261017\<task_id>\
    fbx\        exported FBX(s)
    report\<task_id>.json
    preview\    rendered PNG(s)
    log\        raw stdout of every tool run
```

`report\<task_id>.json` must contain: input paths + sizes/hashes, tool name+version for each
step, measured before/after numbers, the acceptance checks with pass/fail, and a
`verified_by` field naming the *different* tool that read the result back. If a check could not
be run, say `"not verified"` — never imply a check that did not happen.

---

## §1 Why these five tasks (evidence, 2026-10-17)

| # | Task | Evidence it is needed |
|---|------|----------------------|
| 1 | Facial shapes / eye setup | `Dana_CleanSkin_v08` has **0 morphs**; `cast.json` maps `danacornea_mat → M_ImportHelpersHidden` and exposes **no iris slot**; every rendered still has lifeless eyes and no blink is possible |
| 2 | Pose/clip set | In-engine posing is being done by hand-computed quaternion deltas (`Python\universal_film_style_session_20261016.py`); it works but is the wrong authoring tool, and a film needs clips, not a math exercise |
| 3 | Break-room scale | Measured: shell 111.2 × 54.6 × 60.0 uu, counter 15.6 uu tall, cameras inside at z 20–26 uu. Frames render as sky/void from inside — the set is ~1/5 life size and may have outward-facing shell normals |
| 4 | UDIM skin | The canvas is UDIM (`Dana_Diffuse.100*.png`, 1001 = head, 1002 = hands/body); tile **content** is now known and a working 3-tile If-chain master exists in-engine — what is missing is the **measured UV range** (4a) |
| 5 | Cast readiness | David/Sam/Spider were imported as raw deform meshes with no validated bind/scale gate |
| 7 | Derived detail maps | **No normal/bump/roughness/AO map exists in the source** (18 images total, all diffuse); any surface detail must be baked from geometry |

Task 6 is deliberately last: it is polish, and the toon master already renders a readable hair
silhouette.

## §2 Interface the UE film lane honours

- The offline side **never imports**; the UE lane imports once from the drop folder and owns
  `/Game/Staging/**`.
- UE-side material mapping is keyed on the ten slot names in Hard rule 3 — renaming a slot
  silently breaks the style shelf.
- The UE lane measures its own results: cast height in cm, floor min-Z, `display_scale`, and
  slot → material instance mapping, all written to
  `Saved\Renders\universal_film_styles\_cast.json`.
- A T-posed or floating character in a delivered frame is a **defect**, not a preview.
