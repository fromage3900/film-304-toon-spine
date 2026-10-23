"""Restore volumetric fog on EST_Fog_E1.

Write the reviewed volumetric baseline to the EXTERNAL fog actor ONLY.

Earlier this script seeded both fog components. That was wrong: measured 2026-10-19,
writing the volumetric settings onto the sky's internal fog component makes UDS
re-evaluate and force enable_volumetric_fog back to False on EST_Fog_E1 within the same
tick. An external-only write holds across ticks with the hook bound.

Does NOT save the level.
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

uds_actor = film304_fog.get_uds_actor(eas)
ext_fog = film304_fog.get_fog_component(eas)
internal = uds_actor.get_components_by_class(unreal.ExponentialHeightFogComponent)
assert len(internal) == 1, f"Expected 1 internal fog component, got {len(internal)}"
sky_fog = internal[0]

# Deliberately NOT setting fog_density: the swap moved it (0.0055 -> 0.0075 -> 0.00551)
# and there is no evidence which value is intended. Only restore what we know.
VOLUMETRIC = film304_fog.reviewed_volumetric_values()

print("=== sky internal fog (READ ONLY - must not be written) ===")
before_sky = {p: sky_fog.get_editor_property(p) for p in VOLUMETRIC}
print("  before:", json.dumps({k: str(v) for k, v in before_sky.items()}))

print("\n=== EST_Fog_E1 ===")
before = {p: ext_fog.get_editor_property(p) for p in VOLUMETRIC}
print("  before:", json.dumps({k: str(v) for k, v in before.items()}))
receipt = film304_fog.apply(VOLUMETRIC, film304_fog.INTENT_REVIEWED_BASELINE, actors=eas)
after = {p: ext_fog.get_editor_property(p) for p in VOLUMETRIC}
print("  after: ", json.dumps({k: str(v) for k, v in after.items()}))
if receipt["skipped"]:
    print("  SKIPPED:", receipt["skipped"])

after_sky = {p: sky_fog.get_editor_property(p) for p in VOLUMETRIC}
print("\n=== sky internal fog after (must be unchanged) ===")
print("  after: ", json.dumps({k: str(v) for k, v in after_sky.items()}))
sky_untouched = before_sky == after_sky
print(f"  SKY INTERNAL UNTOUCHED: {sky_untouched}")

# ---------------------------------------------------------------- verify
report = film304_fog.drift_report()
print("\n=== VERIFY ===")
print("enable_volumetric_fog (EST_Fog_E1) =", ext_fog.get_editor_property("enable_volumetric_fog"))
print("extinction   =", ext_fog.get_editor_property("volumetric_fog_extinction_scale"))
print("mie          =", ext_fog.get_editor_property("volumetric_fog_scattering_distribution"))
print("volumetric_distance =", ext_fog.get_editor_property("volumetric_fog_distance"))
print("fog_density  =", ext_fog.get_editor_property("fog_density"), "(intentionally untouched)")
print("\ndrive mode:", report["fog_drive"]["mode"])
print("drift clean:", report["drift"]["clean"])

out = Path("G:/film-304-toon-spine/Saved/Audit/Film304_Closeout_20261018")
out.mkdir(parents=True, exist_ok=True)
path = out / "volumetric_restore.json"
path.write_text(
    json.dumps(
        {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "action": "restore_volumetric_fog_external_only",
            "receipt": receipt,
            "sky_internal_before": {k: str(v) for k, v in before_sky.items()},
            "sky_internal_after": {k: str(v) for k, v in after_sky.items()},
            "sky_internal_untouched": sky_untouched,
            "fog_density_left_untouched": ext_fog.get_editor_property("fog_density"),
            "drive": report["fog_drive"],
            "drift": report["drift"],
            "level_saved_by_this_script": False,
        },
        indent=2,
    ),
    encoding="utf-8",
)
print(f"\nRECEIPT: {path}")
print("NOTE: level NOT saved. Save from the editor if this looks right.")