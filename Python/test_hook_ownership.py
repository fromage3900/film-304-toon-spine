"""Test whether the UDS custom-height-fog hook is what forces volumetrics off.

Observation: with the hook bound, writing enable_volumetric_fog=True onto
EST_Fog_E1 succeeds, then reverts to False on the next tick. With the hook unbound,
EST_Fog_E1 should be ours alone.

This is a reversible experiment. It unbinds the hook, sets volumetrics, then
re-reads in a SEPARATE script invocation to confirm the value survives a tick.
Re-binding is left to the caller if the hook turns out to be innocent.
"""
import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "G:/film-304-toon-spine/Python")

import unreal
import film304_fog

importlib.reload(film304_fog)

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = eas.get_all_level_actors()
if len(actors) < 50:
    raise RuntimeError(f"Only {len(actors)} actors - editor likely in PIE.")

MODE = sys.argv[1] if len(sys.argv) > 1 else "status"

uds = film304_fog.get_uds_actor(eas)
ext = film304_fog.get_fog_component(eas)
internal = uds.get_components_by_class(unreal.ExponentialHeightFogComponent)
sky_fog = internal[0]

hook = uds.get_editor_property("Custom Height Fog Actor")


def describe():
    return {
        "hook": film304_fog._describe_actor_ref(hook if MODE == "status" else
                                                uds.get_editor_property("Custom Height Fog Actor")),
        "ext_enable_volumetric": ext.get_editor_property("enable_volumetric_fog"),
        "sky_internal_enable_volumetric": sky_fog.get_editor_property("enable_volumetric_fog"),
        "ext_visible": ext.get_editor_property("visible"),
        "sky_internal_visible": sky_fog.get_editor_property("visible"),
    }


print(f"MODE={MODE}")
print("BEFORE:", json.dumps(describe(), indent=2))

if MODE == "unbind":
    uds.set_editor_property("Custom Height Fog Actor", None)
    uds.modify()
    ext.modify()
    print("\nunbound hook; setting volumetrics on EST_Fog_E1...")
    film304_fog.apply_reviewed_baseline()
    print("AFTER (same tick):", json.dumps(describe(), indent=2))

elif MODE == "verify":
    pass  # just report

elif MODE == "rebind":
    film304_fog.get_fog_actor(eas)
    uds.set_editor_property("Custom Height Fog Actor", film304_fog.get_fog_actor(eas))
    for c in internal:
        c.set_visibility(False)
    uds.modify()
    print("\nrebound hook and re-hid sky internal fog")
    print("AFTER:", json.dumps(describe(), indent=2))

print("\nAFTER:", json.dumps(describe(), indent=2))

receipt = {
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "mode": MODE,
    "state": describe(),
}
out = Path("G:/film-304-toon-spine/Saved/Audit/Film304_Closeout_20261018")
out.mkdir(parents=True, exist_ok=True)
(out / f"hook_test_{MODE}.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print("\nNOTE: level NOT saved.")