"""Repair fog ownership after the UDS sky was replaced.

Restores the invariant the project had before the swap:
  * the sky actor is named Film_UDS_Daylight, which is the label every setup script,
    sequencer script and doc in this project looks it up by
  * its `Custom Height Fog Actor` hook points at EST_Fog_E1
  * its own internal HeightFog component is hidden, so exactly one fog is visible

Does NOT save the level. Saving is left to the operator so this cannot silently
capture unrelated in-flight edits; the receipt reports the dirty state either way.
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

UDS_CLASS = "Ultra_Dynamic_Sky_C"
WANTED_LABEL = film304_fog.UDS_ACTOR_LABEL  # 'Film_UDS_Daylight'

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = eas.get_all_level_actors()
if len(actors) < 50:
    raise RuntimeError(f"Only {len(actors)} actors - editor likely in PIE.")

before = film304_fog.drift_report()
print("BEFORE")
print(json.dumps(
    {k: before[k] for k in
     ("uds_custom_fog_actor", "uds_internal_fog_hidden", "uds_actor_found",
      "uds_actor_candidates", "extra_fog_actors")},
    indent=2,
))

# ---------------------------------------------------------------- resolve
candidates = [a for a in actors if a.get_class().get_name() == UDS_CLASS]
print(f"\nUltra_Dynamic_Sky_C actors: {[a.get_actor_label() for a in candidates]}")
assert len(candidates) == 1, (
    f"Expected exactly one {UDS_CLASS}, found {len(candidates)}: "
    f"{[a.get_actor_label() for a in candidates]}. Resolve the duplicate by hand."
)
uds = candidates[0]

fog_actor = film304_fog.get_fog_actor(eas)
fog_component = film304_fog.get_fog_component(eas)
print(f"sky to repair : {uds.get_actor_label()!r} -> rename to {WANTED_LABEL!r}")
print(f"fog owner     : {fog_actor.get_actor_label()!r} ({fog_component.get_name()})")

# ---------------------------------------------------------------- 1. rename
if uds.get_actor_label() != WANTED_LABEL:
    uds.set_actor_label(WANTED_LABEL)
    print(f"  renamed -> {uds.get_actor_label()!r}")
else:
    print(f"  already named {WANTED_LABEL!r}, no rename needed")
uds.modify()

# ---------------------------------------------------------------- 2. bind hook
uds.set_editor_property("Custom Height Fog Actor", fog_actor)
print(f"  Custom Height Fog Actor -> {uds.get_actor_label()!r} hook set to EST_Fog_E1")

# ---------------------------------------------------------------- 3. hide internal fog
internal = uds.get_components_by_class(unreal.ExponentialHeightFogComponent)
print(f"  internal fog components: {len(internal)}")
for fc in internal:
    was = fc.get_editor_property("visible")
    fc.set_visibility(False)
    now = fc.get_editor_property("visible")
    print(f"    {fc.get_name()}: visible {was} -> {now}")

# Also confirm the project fog is the visible one.
print(f"  EST_Fog_E1 visible = {fog_component.get_editor_property('visible')}")
uds.modify()

# ---------------------------------------------------------------- verify
after = film304_fog.drift_report()
print("\nAFTER")
print(json.dumps(
    {k: after[k] for k in
     ("uds_custom_fog_actor", "uds_internal_fog_hidden", "uds_actor_found",
      "uds_actor_candidates", "extra_fog_actors")},
    indent=2,
))
print("\nDRIFT")
print(json.dumps(after["drift"], indent=2))

# Count every visible height fog in the level: must be exactly one.
visible_fogs = []
for a in actors:
    for fc in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
        try:
            if fc.get_editor_property("visible"):
                visible_fogs.append(f"{a.get_actor_label()}/{fc.get_name()}")
        except Exception:
            pass
print(f"\nVISIBLE HEIGHT FOGS IN LEVEL: {visible_fogs}")
assert len(visible_fogs) == 1, f"Expected exactly one visible fog, got {visible_fogs}"
assert after["drift"]["error_count"] == 0, f"Ownership errors remain: {after['drift']}"

receipt = {
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "action": "repair_fog_ownership_after_sky_swap",
    "renamed_to": WANTED_LABEL,
    "hook_bound_to": fog_actor.get_actor_label(),
    "internal_fog_hidden": [fc.get_name() for fc in internal],
    "visible_fogs": visible_fogs,
    "drift": after["drift"],
    "fog_values": after["values"],
    "level_saved_by_this_script": False,
}

out = Path("G:/film-304-toon-spine/Saved/Audit/Film304_Closeout_20261018")
out.mkdir(parents=True, exist_ok=True)
path = out / "fog_ownership_repair.json"
path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(f"\nRECEIPT: {path}")
print("NOTE: level NOT saved by this script. Save from the editor if the change is good.")