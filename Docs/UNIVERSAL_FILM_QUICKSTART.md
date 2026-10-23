# Universal Toon film scenes

Use the existing Melodia Universal Toon shader for the film cast. This is a packaged asset graph, not a rebuild of Humber's older generated shader.

## Start in Humber

Open the root `HumberToonShader.uproject`, not the nested old `HumberToonShader/HumberToonShader.uproject` copy.

The working parent is `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal`. The older `/Game/Materials/Masters/M_Master_Toon_Universal` is a different asset and is preserved. Use the new `MI_Film_*` shelf under `/Game/Materials/Instances/UniversalFilm_20261016` for these scenes. Humber now explicitly matches Melodia's `r.Substrate.ProjectGBufferFormat=0` renderer setting.

Compositions authored by `Python/build_universal_film_scenes.py`:

- `/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Studio`: neutral close-up and full-body cameras; six named cast-position markers.
- `/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office`: warm desk alcove; medium and wide cameras.
- `/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Arrival`: brutalist portal and stepped skyline; wide camera.

Sequences live in `/Game/Sequences/UniversalFilm_20261016`; render presets in `/Game/MoviePipelines/UniversalFilm_20261016`. All three maps retain UDS daylight. Cast placeholders are hidden until a validated film rig and retargeted action exist. They are lighting templates, not approved final shots.

The dark reference-pose renders and subsequent Sparrow-character preview were rejected. Sparrow is an ANIMATION DONOR ONLY. No Sparrow actor or character binding remains in these maps; `cast_reconciliation.json` records the cleanup. `Python/light_and_animate_universal_film.py` is retired and raises an error. Do not re-enable it. Use `Python/reconcile_universal_film_cast.py` only to restore the corrected hidden-placeholder state if needed.

## Add the remaining five characters

First finish each rig's deformation checks with the rig owner. The staged Sparrow mesh/skeleton and Jog_Fwd clip (2.133 seconds) are retarget source data only. Transfer the motion onto each validated film-cast skeleton; never substitute the donor character into a shot. Dana and David's current clips are four-frame export tests, and Dana's old body export has no skin weights. Do not attempt to make those clips into action by moving a T-pose actor around the set.

1. Duplicate the relevant scene for the new cast member using Unreal's asset tools.
2. Replace the subject actor's mesh with that character's validated candidate. Preserve the source mesh asset and its material slots.
3. Set the actor's display height and floor contact from evaluated bounds. The Dana stage normalizes to 170 cm for consistent camera testing; this is stage scale, not a rig-unit correction.
4. Override materials on the scene component, using explicit slot names. Make a per-character child of the closest `MI_Film_*` instance for changes; do not change shared skin colors globally.
5. Check cornea, lashes, and proxy sections with the rig owner. Dana's `Hidden` mapping is specific to her existing reference import and must not be copied blindly to the other rigs.
6. Rebind the shot's camera/subject tracks in the duplicated sequence and run neutral, blink/head-turn, and body-motion checks before final rendering.

The motion import omitted only `Orion_Proto_Retarget`: UE 5.8 cannot load its deprecated `Rig` class. The target mesh, skeleton and clip must still load and match. Preserve that qualification in handoffs; do not call missing runtime assets harmless without checking them.

The current explicit slot map is `specs/humber_toon_spine/universal_film_cast.v1.json`. It records five remaining rigs as pending instead of inventing filenames or importing them automatically. `FILM_CAST_PROFILE` can select another validated profile for an isolated build, but the builder refuses to overwrite existing composition maps.

## Shader delivery

`Saved/UniversalFilmDelivery_20261016/UniversalFilm.uproject` is the isolated shader project. Its `Content/` retains original package paths so the working graph can resolve its dependencies. A single conflicting Humber texture is moved inside this isolated project to `/Game/EnvSandbox/Textures/UniversalFilm/T_SDF_Strokes`; the production source and Humber's existing texture are preserved.

The delivery includes required material functions, textures, profile, parameter collections, and example Dana-look instances. It does not require Melodia's gameplay code or contain the Maya rig source. Required Sky/Weather assets and third-party textures remain subject to their original licenses; this local project bundle is not a declaration that those assets may be published publicly or redistributed as a standalone asset library.

Target: Unreal 5.8, Substrate enabled. Observed engine build: 5.8.0-55116800+++UE5+Release-5.8. Reopening on this workstation is verified; another engine installation/workstation remains a separate portability check. The delivery project's small renderer configuration records its requirements; do not replace Humber's entire configuration with Melodia's.

Reproduction scripts:

- `Python/package_universal_film.py`: source inventory and native engine migration, with graph/size/hash reports.
- `Python/finalize_universal_film.py`: isolated-project texture remap, graph comparison, conflict-safe migration into Humber.
- `Python/build_universal_film_scenes.py`: additive instances, scenes, cameras, sequences and render presets.
- `Python/stage_universal_film_motion.py`: native migration of donor animation dependencies, without changing source assets; donor character is never film cast.
- `Python/light_and_animate_universal_film.py`: RETIRED rejected stand-in builder; do not execute or re-enable.
- `Tools/package_universal_film_delivery.py`: shader-only project zip, package manifest, CRC and hash readback. Donor retarget assets are excluded from the shader archive.

Do not run the existing `build_spine.py` over the packaged master. Its generated `/Game/Materials/` shader family is the older Humber implementation. This handoff deliberately consumes the already-working Melodia graph.

## Proof

Read the actual JSON reports and rendered frames. `humber_migration.json` checks the master expression/function references and exact package bytes. `scenes.json` records saved compositions. Neither alone is visual proof or a rig-deformation check. Reopening the isolated project proves same-machine portability; another workstation is a separate check.

Keep the current rig/eye investigation in the existing **Update Toon Spine material masters** chat. No Git commit, push, group message, or rig-source publication is performed by these scripts.
