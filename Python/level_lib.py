"""Shared helpers for the level-owning UE scripts.

Two scripts own a level end-to-end (open/create it, spawn meshes and lights,
clean up their own actors on re-run): `compose_shot_env_level.py`
(`L_Toon_Shot_Env`) and `stage_brutalist_layout.py` (`L_Brutalist_Layout`).
Each carried its own copies of the same helpers, and the copies had drifted in
exactly the places that matter:

  * `stage_brutalist_layout.py` still had the pre-2026-10-02 sun-rotation bug
    (`unreal.Rotator(-46, 0, 35)` is roll=-46 / pitch=0 / yaw=35, i.e. the sun
    sits ON the horizon) that `compose_shot_env_level.py` fixed in keyword
    form;
  * only `compose_shot_env_level.py` had the dirty-map guard, so re-running the
    layout script with a dirty editor map could open the blocking "save
    changes?" modal and wedge MCP (observed 2026-10-01).

Same function, one implementation now - the rule `spine_lib.py` applies to the
toon spine, applied to the level-owning scripts.
"""
from __future__ import annotations

import unreal  # noqa: E402  (imported after the editor's sys.path is set up)


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def sun_rotator(pitch, yaw, roll):
    """`unreal.Rotator` built WITHOUT positional ambiguity.

    BUG (2026-10-02, caught in compose_shot_env_level.py): the positional
    constructor is (roll, pitch, yaw), while every spec in this repo writes
    rotations as (pitch, yaw, roll). `Rotator(-46.0, 0.0, 35.0)` was therefore
    applied as roll=-46, pitch=0, yaw=35 - a sun 46 degrees above the horizon
    landed exactly ON it, and every up-facing surface rendered as a
    near-black silhouette. Keyword args make the ordering explicit.
    """
    return unreal.Rotator(roll=float(roll), pitch=float(pitch), yaw=float(yaw))


def open_or_create_level(pkg, clean_labels=None):
    """Idempotent: an existing level is reloaded and (optionally) cleaned.

    `clean_labels`: when given and the level was reloaded, every actor whose
    label is in the set is destroyed first - a re-run must never stack a
    second set of actors. Only actors the caller OWNS are removed; destroying
    every actor in a level is fatal headless on an engine template map
    (documented in build_test_level.py).
    """
    ensure_dir(pkg.rsplit("/", 1)[0])

    # Switching levels while a map is dirty makes the editor raise a "save
    # changes?" MODAL, which blocks the game thread and leaves MCP unresponsive
    # (AGENTS.md rule 8 - observed 2026-10-01 as MODAL_OPEN title='' text='').
    # Fail closed and let a human resolve it rather than wedge the editor.
    # get_dirty_MAP_packages only: the _content_ variant enumerates every loaded
    # package and took >30 s, which is what abandoned the HTTP client that time.
    dirty = [p.get_name() for p in
             unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
    if dirty:
        raise RuntimeError(
            "dirty map package(s) %s -- save or discard them in the editor "
            "before opening %s; switching levels would open a blocking modal"
            % (dirty, pkg))

    sub = unreal.LevelEditorSubsystem()
    if unreal.EditorAssetLibrary.does_asset_exist(pkg):
        if not sub.load_level(pkg):
            raise RuntimeError("could not load %s" % pkg)
        print("[level-lib] reloaded existing level %s" % pkg, flush=True)
        if clean_labels is not None:
            removed = remove_owned_actors(clean_labels)
            print("[level-lib] removed %d previously owned actor(s)"
                  % removed, flush=True)
        return "reloaded"
    if not sub.new_level(pkg):
        raise RuntimeError("could not create %s" % pkg)
    print("[level-lib] created level %s" % pkg, flush=True)
    return "created"


def remove_owned_actors(labels):
    """Destroy every level actor whose label is in `labels`. Returns the count."""
    removed = 0
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        try:
            if a.get_actor_label() in labels:
                unreal.EditorLevelLibrary.destroy_actor(a)
                removed += 1
        except Exception:                                          # noqa: BLE001
            continue
    return removed


def spawn_mesh(object_name, collection, location, mesh_root):
    """One StaticMeshActor carrying `mesh_root/<collection>/SM_<object>`.

    Labelled <object>. Returns (actor, mesh, asset_path).
    """
    asset = "%s/%s/SM_%s" % (mesh_root, collection, object_name)
    mesh = unreal.load_asset(asset)
    if mesh is None:
        raise RuntimeError("mesh not found: %s" % asset)

    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, location, unreal.Rotator(0.0, 0.0, 0.0))
    actor.set_actor_label(object_name)

    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if comp is None:
        raise RuntimeError("%s: no StaticMeshComponent" % object_name)
    # Static mobility refuses a mesh swap mid-session; move it, set, move back.
    comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    comp.set_static_mesh(mesh)
    comp.set_mobility(unreal.ComponentMobility.STATIC)
    return actor, mesh, asset


def spawn_lights(sun_rotation=(0.0, 0.0, 0.0), sun_height=4000.0,
                 sun_intensity=3.2, sky_height=1000.0, sky=True,
                 atmosphere=True, light_mobility="movable"):
    """Sun + sky + atmosphere, so the level reads on open.

    `sun_rotation` is (pitch, yaw, roll) - the spec convention, applied in
    keyword form by `sun_rotator` (see its docstring for the bug this prevents).

    2026-10-08: lights spawn MOVABLE by default and STAY movable. The old
    spawn-static dance (MOVABLE -> set intensity -> STATIC) produced levels
    whose unbaked static geometry received NO direct light under the headless
    -game/MRQ render path (lightmap-only evaluation without BuiltData) -- the
    black-render class recorded in Saved/Audit/render_test_20261008.json and
    bisected to mobility in the office_asset_bisect pass. Movable lights
    evaluate per-pixel everywhere, including cooked builds. Pass
    light_mobility="static" only for a level that is certain to ship with
    built lighting.
    """
    pitch, yaw, roll = (list(sun_rotation) + [0.0, 0.0, 0.0])[:3]
    d = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0.0, 0.0, sun_height),
        sun_rotator(pitch, yaw, roll))
    d.set_actor_label("LGT_Sun")
    try:
        c = d.get_component_by_class(unreal.DirectionalLightComponent)
        c.set_intensity(float(sun_intensity))
        if light_mobility == "static":
            c.set_mobility(unreal.ComponentMobility.MOVABLE)
            c.set_mobility(unreal.ComponentMobility.STATIC)
    except Exception:                                              # noqa: BLE001
        pass

    if sky:
        unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.SkyLight,
            unreal.Vector(0.0, 0.0, sky_height)).set_actor_label("LGT_Sky")
    if atmosphere:
        try:
            unreal.EditorLevelLibrary.spawn_actor_from_class(
                unreal.SkyAtmosphere,
                unreal.Vector(0.0, 0.0, 0.0)).set_actor_label("Sky")
        except Exception as e:                                     # noqa: BLE001
            print("[level-lib] WARN SkyAtmosphere not spawned: %s" % e,
                  flush=True)
