"""Shared level-fixture helpers for the lookdev builders.

WHY THIS MODULE EXISTS
----------------------
All three lookdev builders (gouache / foliage / water) need the same
level-open sequence, and getting it wrong fatals the headless editor in a
way that is easy to misdiagnose. Two facts, both measured 2026-10-03:

1. ONE LEVEL LOAD PER PROCESS. Loading a second level in the same process
   fatals: "World Memory Leaks: 2 leaks objects and packages"
   (EditorServer.cpp:2544). An explicit collect_garbage() does NOT clear it.
   Hence Tools/build_lookdev_levels.py runs one process per level.

2. A PHANTOM PACKAGE IS WORSE THAN A MISSING ONE. When a run dies between
   create_asset and save, the asset REGISTRY keeps the package name while the
   .umap never reaches disk. `does_asset_exist` then answers True, so a later
   run skips creation and calls load_level on a package with no file - which
   takes the engine's "make a new map" path and fatals on the still-current
   startup world. This is exactly what happened to L_Gouache_Lookdev after
   spine runs 12/13 crashed mid-build.

So: purge the phantom, create the real asset, SAVE it so the file exists,
then load it. Save-before-load is the part that makes the load path a plain
"open an existing map" rather than a creation.
"""
from __future__ import annotations

from pathlib import Path

import unreal

import spine_lib as lib


def resolve_world_factory():
    for nm in ("WorldFactory", "WorldFactoryNew", "WorldFactoryNewLevel"):
        cls = getattr(unreal, nm, None)
        if cls is not None:
            return cls
    return None


def _disk_path(level_name: str) -> Path:
    root = Path(unreal.Paths.convert_relative_path_to_full(
        unreal.Paths.project_content_dir()))
    return root / "Maps" / f"{level_name}.umap"


def _current_level_name() -> str:
    try:
        world = unreal.EditorLevelLibrary.get_editor_world()
        if world is None:
            return ""
        outer = world.get_outer()
        return outer.get_name() if outer is not None else world.get_name()
    except Exception:
        return ""


def save_current_level(asset_path: str) -> bool:
    """Save the current world to asset_path. Returns whether the FILE exists.

    `EditorLevelLibrary.save_current_level()` fails on a world that has no
    filename ("Can't save the level because it doesn't have a filename") -
    which is exactly the state after new_blank_map. save_map(world, path)
    is the call that gives the world its filename AND writes it.
    The boolean is the on-disk check, not the API's return value: the API
    can report success while the write is still pending.
    """
    las = getattr(unreal, "EditorLoadingAndSavingUtils", None)
    if las is None:
        return False
    world = unreal.EditorLevelLibrary.get_editor_world()
    try:
        las.save_map(world, asset_path)
    except Exception as exc:
        lib.log(f"WARN save_map({asset_path}): {str(exc)[:120]}")
    level_name = asset_path.rsplit("/", 1)[-1]
    return _disk_path(level_name).exists()


def ensure_level(level_name: str, map_dir: str = "/Game/Maps") -> dict:
    """Open (creating if needed) a fixture level. Returns a small status dict.

    THREE MEASURED FACTS, all 2026-10-03, in the order they were learned:

    1. ONE LEVEL LOAD PER PROCESS. A second load_level fatals with "World
       Memory Leaks" (EditorServer.cpp:2544); collect_garbage does not clear
       it. Callers run one process per level.

    2. create_asset DOES NOT PUT A LEVEL ON DISK. It makes an UNTITLED world
       current ("SaveCurrentLevel. Can't save the level because it doesn't
       have a filename"), and a following load_level then fatals on that very
       world still being current. Creating and loading in one process is
       therefore self-defeating.

    3. THE WORKING SEQUENCE avoids load entirely when creating:
         EditorLoadingAndSavingUtils.new_blank_map(False)   -> fresh current world
         <spawn actors>
         EditorLoadingAndSavingUtils.save_map(world, path)  -> writes the .umap
       and for an existing level:
         EditorLoadingAndSavingUtils.load_map(path)
    A phantom registry entry (package name known, no file on disk) is purged
    first, because that is what made the earlier attempts take the create
    path against a name the registry already claimed.
    """
    asset_path = f"{map_dir}/{level_name}"
    disk = _disk_path(level_name)
    status = {"level": level_name, "asset_path": asset_path,
              "disk_path": str(disk), "actions": []}

    # phantom purge: registry says yes, disk says no
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path) and not disk.exists():
        try:
            unreal.EditorAssetLibrary.delete_asset(asset_path)
            status["actions"].append("purged-phantom")
        except Exception as exc:
            status["actions"].append(f"phantom-purge-failed:{str(exc)[:50]}")

    las = getattr(unreal, "EditorLoadingAndSavingUtils", None)
    if las is None:
        raise RuntimeError("EditorLoadingAndSavingUtils unavailable")

    if disk.exists():
        las.load_map(asset_path)
        status["actions"].append("loaded-existing")
    else:
        lib.ensure_dir(map_dir)
        # new_blank_map makes the blank world CURRENT; nothing to load after
        las.new_blank_map(False)
        status["actions"].append("new-blank-map")
        world = unreal.EditorLevelLibrary.get_editor_world()
        ok = las.save_map(world, asset_path)
        status["actions"].append(f"saved-new:{bool(ok)}")
        if not ok or not disk.exists():
            status["actions"].append("save-failed")

    status["ok"] = disk.exists()
    return status
