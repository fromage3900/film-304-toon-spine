"""READ-ONLY follow-up: resolve CineCamera focal length + UDS time-of-day member.

The first probe read focal_length as 0.0 for all four hero cameras. That is a
property-resolution failure in the probe, NOT scene drift, so resolve it properly
before drawing any conclusion. Also enumerate UDS members to find the real
time-of-day handle, since 'time_of_day' and 10 variants all failed.

Run:  python Tools/run_ue_file.py Python/probe_lens_and_uds_members_20261018.py
"""
import json
import os

import unreal

OUT = r"G:/film-304-toon-spine/Saved/Audit/HeroLock20261018/lens_and_uds_members.json"
MAP_NAME = "L_Film_Office"

LABELS = [
    "HERO01_Wide_Establishing",
    "HERO02_Medium_TwoShot",
    "HERO03_Close_Portrait",
    "HERO04_Macro_Insert",
]

report = {"read_only": True, "saved_anything": False, "errors": [], "cameras": []}

eds = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = eds.get_editor_world()
report["current_world"] = world.get_name() if world else None
if report["current_world"] != MAP_NAME:
    report["errors"].append("unexpected world %s" % report["current_world"])

actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
by_label = {}
for a in actors:
    try:
        by_label[a.get_actor_label()] = a
    except Exception:
        continue

# ---------------------------------------------------- focal length resolution
cc_members = None
for label in LABELS:
    a = by_label.get(label)
    entry = {"label": label, "found": a is not None}
    if a is None:
        report["cameras"].append(entry)
        continue

    cc = None
    try:
        cc = a.get_cine_camera_component()
    except Exception as exc:
        entry["error"] = "get_cine_camera_component: %r" % (exc,)

    if cc is not None:
        if cc_members is None:
            members = [m for m in dir(cc) if not m.startswith("__")]
            cc_members = sorted(
                m for m in members
                if any(k in m.lower() for k in ("focal", "lens", "aperture", "filmback", "zoom"))
            )
            report["cine_camera_lens_members"] = cc_members

        attempts = {}
        for name in ("focal_length", "current_focal_length"):
            try:
                attempts[name] = float(cc.get_editor_property(name))
            except Exception as exc:
                attempts[name] = "FAILED: %s" % exc.__class__.__name__

        ls = None
        try:
            ls = cc.get_editor_property("lens_settings")
        except Exception as exc:
            attempts["lens_settings"] = "FAILED: %s" % exc.__class__.__name__
        if ls is not None:
            try:
                attempts["lens_settings.focal_length"] = float(
                    ls.get_editor_property("focal_length")
                )
            except Exception as exc:
                attempts["lens_settings.focal_length"] = "FAILED: %s" % exc.__class__.__name__

        entry["attempts"] = attempts
        resolved = [v for v in attempts.values() if isinstance(v, float) and v > 0.0]
        entry["resolved_focal_length"] = resolved[0] if resolved else None
    report["cameras"].append(entry)

# -------------------------------------------------------- UDS member listing
uds = by_label.get("Film_UDS_Daylight")
if uds is None:
    report["errors"].append("Film_UDS_Daylight not found")
else:
    report["uds_class"] = uds.get_class().get_name()
    members = [m for m in dir(uds) if not m.startswith("__")]
    report["uds_time_members"] = sorted(
        m for m in members
        if any(k in m.lower() for k in ("time", "day", "sun", "hour", "date"))
    )
    # Blueprint variables often surface as functions; capture callables too.
    report["uds_callable_time_members"] = sorted(
        m for m in report["uds_time_members"] if callable(getattr(uds, m, None))
    )

report["saved_anything"] = False
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as fh:
    json.dump(report, fh, indent=2)

print("LENS_PROBE wrote " + OUT)
for c in report["cameras"]:
    print("  %s -> %s" % (c["label"], c.get("resolved_focal_length")))
print("UDS_TIME_MEMBERS=%d" % len(report.get("uds_time_members", [])))
