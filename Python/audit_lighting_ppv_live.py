"""Read-only live audit of the Film 304 light rig and post-process stack.

Why this exists
---------------
Docs/SCENE_LIGHTING_AUDIT_20261018.md reports specific numbers (RimKicker 4.88,
EST_Fill 0, SunBeam 5.5, five PPVs all at priority 100 / blend weight 1.0). The fog
probe showed the level was hand-tuned past every setup script, so those light figures
are no more trustworthy than the fog ones were. This re-reads them from the live editor.

Nothing here mutates the level. Safe to run at any time.

    powershell -File Tools/mcp_exec.ps1 -Path Python/audit_lighting_ppv_live.py
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "G:/film-304-toon-spine/Python")

import unreal
import film304_fog

import importlib

importlib.reload(film304_fog)

OUT = Path("G:/film-304-toon-spine/Saved/Audit/Film304_Closeout_20261018")

LIGHT_PROPS = (
    "intensity",
    "intensity_units",
    "light_color",
    "use_temperature",
    "temperature",
    "cast_shadows",
    "volumetric_scattering_intensity",
    "atmosphere_sun_light",
    "visible",
    "inner_cone_angle",
    "outer_cone_angle",
    "attenuation_radius",
    "light_source_angle",
)


def read(obj, prop):
    """Read an editor property, recording absence instead of raising."""
    try:
        value = obj.get_editor_property(prop)
    except Exception:
        return "<unavailable>"
    if hasattr(value, "to_tuple"):
        try:
            return list(value.to_tuple())
        except Exception:
            return str(value)
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    return str(value)


def lighting_channels(component):
    """Read LightingChannels. The struct has no usable repr, so report which are on.

    Verified live: the property name is `lighting_channels`; `light_channels` does not
    exist. Reading it as a bare struct makes every light look identical.
    """
    try:
        ch = component.get_editor_property("lighting_channels")
    except Exception:
        return "<unavailable>"
    try:
        on = [str(i) for i in range(4) if getattr(ch, f"channel{i}")]
        return on or ["none"]
    except Exception:
        return str(ch)


def _blendable_count(settings):
    """Count weighted blendables; the struct has no len() in this engine build."""
    if settings is None:
        return 0
    try:
        blendables = settings.weighted_blendables
    except Exception:
        return "<unavailable>"
    try:
        return len(blendables.array)
    except Exception:
        pass
    try:
        return len(blendables)
    except Exception:
        return "<unavailable>"


def main():
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

    # Guard against auditing the Play-In-Editor world. In PIE, get_all_level_actors()
    # returns the PIE world, which does not contain editor-placed actors. An unguarded
    # audit then finds zero lights and reports "no competing keys" and a single-writer
    # PPV stack - a clean bill of health for a scene it never actually looked at.
    # Observed live on 2026-10-19: a probe run during PIE reported every actor as
    # absent and printed a false all-clear.
    all_actors = actors.get_all_level_actors()
    if len(all_actors) < 50:
        raise RuntimeError(
            f"Only {len(all_actors)} level actors visible; the editor assembly has 200+. "
            "The editor is almost certainly in Play-In-Editor mode. Exit play mode and "
            "re-run - auditing the PIE world produces a false pass."
        )

    lights = []
    ppvs = []
    for a in actors.get_all_level_actors():
        label = a.get_actor_label()
        cls = a.get_class().get_name()

        if isinstance(a, unreal.Light):
            c = a.get_component_by_class(unreal.LightComponent)
            if c is None:
                continue
            entry = {
                "label": label,
                "class": cls,
                "component": c.get_name(),
                "values": {p: read(c, p) for p in LIGHT_PROPS},
                "lighting_channels": lighting_channels(c),
                "location_cm": [round(v, 1) for v in a.get_actor_location().to_tuple()],
            }
            lights.append(entry)

        elif isinstance(a, unreal.PostProcessVolume):
            s = a.get_editor_property("settings")
            ppvs.append(
                {
                    "label": label,
                    "unbound": read(a, "unbound"),
                    "priority": read(a, "priority"),
                    "blend_weight": read(a, "blend_weight"),
                    "enabled": read(a, "enabled"),
                    "blend_radius": read(a, "blend_radius"),
                    "weighted_blendables_count": _blendable_count(s),
                    "location_cm": [round(v, 1) for v in a.get_actor_location().to_tuple()],
                }
            )

    directionals = [l for l in lights if "DirectionalLight" in l["class"]]
    spots = [l for l in lights if "SpotLight" in l["class"]]
    points = [l for l in lights if "PointLight" in l["class"]]
    rects = [l for l in lights if "RectLight" in l["class"]]

    # Directionals with meaningful intensity competing in one frame.
    active_directionals = [
        l
        for l in directionals
        if isinstance(l["values"].get("intensity"), (int, float)) and l["values"]["intensity"] > 0
    ]
    heavy_directionals = [
        l
        for l in active_directionals
        if isinstance(l["values"].get("intensity"), (int, float))
        and l["values"]["intensity"] >= 4.0
    ]

    # PPVs that actually contribute: enabled, unbound-or-in-range, non-zero weight.
    active_ppvs = [
        p
        for p in ppvs
        if p["enabled"] is True
        and isinstance(p["blend_weight"], (int, float))
        and p["blend_weight"] > 0
    ]
    conflicting = [p for p in active_ppvs if p["unbound"] is True]
    same_priority = {}
    for p in active_ppvs:
        same_priority.setdefault(p["priority"], []).append(p["label"])
    contested_priority = {k: v for k, v in same_priority.items() if len(v) > 1}

    shafts = [l for l in lights if l["label"].startswith("Film_WindowShaft")]

    # Clobber check. The level was hand-tuned past the setup scripts here too: the
    # shafts sit at 180cd / vol_scatter 8.0, but converge_master_showcase_20261018.py
    # writes 140 / 6.0. Re-running that script would silently drop the godray rig to a
    # level nobody has rendered. Same failure mode as the fog drift.
    SHAFT_SCRIPT_VALUES = {"intensity": 140.0, "volumetric_scattering_intensity": 6.0}
    shaft_drift = []
    for s in shafts:
        v = s["values"]
        for prop, script_value in SHAFT_SCRIPT_VALUES.items():
            actual = v.get(prop)
            if isinstance(actual, (int, float)) and abs(actual - script_value) > 1e-4:
                shaft_drift.append(
                    {
                        "light": s["label"],
                        "property": prop,
                        "live": actual,
                        "script_writes": script_value,
                    }
                )

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "world": world.get_path_name(),
        "fog": {
            "actor": film304_fog.FOG_ACTOR_LABEL,
            "values": film304_fog.snapshot().values,
            "drift_clean": film304_fog.drift_report()["drift"]["clean"],
        },
        "counts": {
            "lights_total": len(lights),
            "directional": len(directionals),
            "spot": len(spots),
            "point": len(points),
            "rect": len(rects),
            "ppv_total": len(ppvs),
            "ppv_active": len(active_ppvs),
        },
        "findings": {
            "active_directionals": [l["label"] for l in active_directionals],
            "heavy_directionals_ge_4": [l["label"] for l in heavy_directionals],
            "competing_directional_keys": len(heavy_directionals) > 1,
            "active_unbound_ppvs": [p["label"] for p in conflicting],
            "contested_priority": contested_priority,
            "ppv_stack_is_single_writer": len(contested_priority) == 0 and len(active_ppvs) <= 1,
            "window_shaft_count": len(shafts),
            "window_shaft_clobber_by_setup_scripts": shaft_drift,
        },
        "lights": sorted(lights, key=lambda x: x["label"]),
        "postprocess": sorted(ppvs, key=lambda x: x["label"]),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "lighting_ppv_live_audit.json"
    # LinearColor and other UE structs are not JSON serialisable; film304_fog already
    # carries the coercion used by the fog audit.
    path.write_text(
        json.dumps(report, indent=2, default=film304_fog._jsonable), encoding="utf-8"
    )

    print("=== COUNTS ===")
    print(json.dumps(report["counts"], indent=2))
    print("\n=== DIRECTIONAL LIGHTS ===")
    for l in directionals:
        v = l["values"]
        print(
            f"  {l['label']:34s} intensity={v['intensity']!s:>10s} "
            f"vol_scatter={v['volumetric_scattering_intensity']!s:>8s} "
            f"channels={l['lighting_channels']} shadows={v['cast_shadows']}"
        )
    print("\n=== WINDOW SHAFT SPOTS ===")
    for l in shafts:
        v = l["values"]
        print(
            f"  {l['label']:26s} intensity={v['intensity']!s:>8s} "
            f"units={v['intensity_units']} vol_scatter={v['volumetric_scattering_intensity']} "
            f"cone={v['inner_cone_angle']}/{v['outer_cone_angle']} K={v['temperature']}"
        )
    if not shafts:
        print("  (none found)")
    print("\n=== SPOT / RECT LIGHTS ===")
    for l in spots + rects:
        v = l["values"]
        print(
            f"  {l['label']:34s} {l['class']:22s} intensity={v['intensity']!s:>10s} "
            f"vol_scatter={v['volumetric_scattering_intensity']}"
        )
    print("\n=== POST-PROCESS VOLUMES ===")
    for p in ppvs:
        print(
            f"  {p['label']:28s} unbound={str(p['unbound']):5s} priority={p['priority']!s:>6s} "
            f"weight={p['blend_weight']!s:>6s} enabled={p['enabled']} "
            f"blendables={p['weighted_blendables_count']}"
        )
    print("\n=== FINDINGS ===")
    print(json.dumps(report["findings"], indent=2))
    print(f"\nreport written to {path}")


if __name__ == "__main__":
    main()