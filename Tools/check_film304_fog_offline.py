"""Offline check of film304_fog logic against a stubbed unreal module.

The real editor is not reachable from a plain interpreter, so this stubs the handful
of UE types film304_fog touches and asserts the behaviour that matters:

  * exactly-one-actor resolution, and the assert on duplicates
  * drift detection for the reviewed extinction scale
  * double-fog / unbound UDS hook detection
  * a mutating apply() records before/after and respects intent

Run:  python Tools/check_film304_fog_offline.py
"""
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Python"))


# --------------------------------------------------------------------------
# Stub just enough of the unreal module for import and the code paths we exercise.
# --------------------------------------------------------------------------
class _Color(tuple):
    def __new__(cls, r, g, b, a=1.0):
        return super().__new__(cls, (r, g, b, a))

    def to_tuple(self):
        return tuple(self)


class _Component:
    def __init__(self, props, name="Component"):
        self._props = dict(props)
        self._visible = True
        self._name = name

    def get_name(self):
        return self._name

    def get_editor_property(self, name):
        if name not in self._props:
            raise AttributeError(f"no such property: {name}")
        return self._props[name]

    def set_editor_property(self, name, value):
        if name not in self._props:
            raise AttributeError(f"no such property: {name}")
        self._props[name] = value

    def modify(self):
        pass

    def is_visible(self):
        return self._visible


class _FogComponent(_Component):
    def __init__(self, props, name="HeightFogComponent0"):
        super().__init__(props, name)

    @property
    def fog_density(self):
        return self._props["fog_density"]

    def set_fog_density(self, v):
        self._props["fog_density"] = v


class _Actor:
    def __init__(self, label, props=None, has_fog=True, cls=None):
        self._label = label
        if cls:
            self._cls = cls
        self._loc = _Color(0.0, 20000.0, 0.0)
        self._comp = _FogComponent(props or {}) if has_fog else None
        self._comps = [self._comp] if has_fog else []
        self._custom_fog = None

    def get_actor_label(self):
        return self._label

    def get_class(self):
        return _ClassName(self._class_name)

    @property
    def _class_name(self):
        return getattr(self, "_cls", "Actor")

    def get_path_name(self):
        return f"/Game/Map.{self._label}"

    def get_actor_location(self):
        return self._loc

    def get_component_by_class(self, cls):
        return self._comp

    def get_components_by_class(self, cls):
        return list(self._comps)

    def get_editor_property(self, name):
        if name == "Custom Height Fog Actor":
            return self._custom_fog
        raise AttributeError(name)

    def modify(self):
        pass

    @property
    def component(self):
        return self._comp


class ExponentialHeightFog(_Actor):
    def __init__(self, label, props=None, **kw):
        kw.setdefault("cls", "ExponentialHeightFog")
        super().__init__(label, props, **kw)


class _ClassName:
    def __init__(self, name):
        self._name = name

    def get_name(self):
        return self._name


class ExponentialHeightFogComponent:
    pass


class EditorActorSubsystem:
    def __init__(self, actors):
        self._actors = actors

    def get_all_level_actors(self):
        return list(self._actors)


class Paths:
    @staticmethod
    def project_dir():
        return str(ROOT)


class _FakeUnreal(types.ModuleType):
    ExponentialHeightFog = ExponentialHeightFog
    ExponentialHeightFogComponent = ExponentialHeightFogComponent
    EditorActorSubsystem = EditorActorSubsystem
    Paths = Paths
    LinearColor = _Color

    def get_editor_subsystem(self, cls):
        return _SUBSYSTEM


unreal = _FakeUnreal("unreal")
_SUBSYSTEM = None
sys.modules["unreal"] = unreal

import film304_fog  # noqa: E402


# Mirrors the LIVE_BASELINE_20261018 values probed from the saved level (rev 2, after
# the UDS sky swap), so the offline checks assert against what the level ships with.
DEFAULT_PROPS = {
    "fog_density": 0.00551,
    "fog_height": 0.0,
    "fog_height_falloff": 0.06,
    "fog_inscattering_color": _Color(0.55, 0.40, 0.30, 1.0),
    "fog_inscattering_luminance": _Color(0.0, 0.0, 0.0, 1.0),
    "fog_max_opacity": 1.0,
    "fog_cutoff_distance": 0.0,
    "start_distance": 7348.03369140625,
    "enable_volumetric_fog": True,
    "volumetric_fog": True,
    "volumetric_fog_distance": 8000.0,
    "volumetric_fog_scattering_distribution": 0.65,
    "volumetric_fog_extinction_scale": 2.5,
    "volumetric_fog_start_distance": 0.0,
    "volumetric_fog_cutoff_distance": 0.0,
    "volumetric_fog_height": 0.0,
}


def subsystem(fog_props=None, extras=(), bind_uds=True, uds_internal_visible=False,
              uds_label="Film_UDS_Daylight"):
    global _SUBSYSTEM
    fog = ExponentialHeightFog("EST_Fog_E1", fog_props or dict(DEFAULT_PROPS))
    actors = [fog]
    for label in extras:
        actors.append(ExponentialHeightFog(label, dict(DEFAULT_PROPS)))
    # The sky carries its own fog component; it must expose the same properties,
    # because the custom-fog hook re-applies these onto the external actor.
    uds = _Actor(uds_label, props=dict(DEFAULT_PROPS), has_fog=True, cls="Ultra_Dynamic_Sky_C")
    uds._comp._visible = uds_internal_visible
    uds._custom_fog = fog if bind_uds else None
    actors.append(uds)
    _SUBSYSTEM = EditorActorSubsystem(actors)
    return _SUBSYSTEM


def uds_actor():
    """The sky actor in the current stub subsystem."""
    for a in _SUBSYSTEM.get_all_level_actors():
        if a.get_actor_label() != "EST_Fog_E1":
            return a
    raise AssertionError("no sky actor in stub")


FAILURES = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


def main():
    print("film304_fog offline checks")

    print("\n1. reviewed baseline is clean")
    subsystem()
    report = film304_fog.drift_report()
    check("single owner", report["ownership_is_singleton"])
    check("clean at reviewed values", report["drift"]["clean"],
          json.dumps(report["drift"]["findings"]))

    print("\n2. extinction drift is detected (the 1.2 clobber)")
    subsystem(fog_props={**DEFAULT_PROPS, "volumetric_fog_extinction_scale": 1.2})
    report = film304_fog.drift_report()
    codes = [f["code"] for f in report["drift"]["findings"]]
    check("flags off-reviewed extinction", "extinction_scale_off_reviewed_value" in codes,
          str(codes))
    check("flags off live baseline",
          "off_live_baseline_volumetric_fog_extinction_scale" in codes, str(codes))

    print("\n2b. script-authored values are flagged against the live level")
    # The scripts write these; the level holds the values above. Re-running a setup
    # script must therefore read as drift, not as a restore.
    subsystem(fog_props={**DEFAULT_PROPS,
                         "fog_density": 0.0016,
                         "fog_height_falloff": 0.12,
                         "fog_max_opacity": 0.92,
                         "start_distance": 3000.0})
    codes = [f["code"] for f in film304_fog.drift_report()["drift"]["findings"]]
    check("flags script falloff", "off_live_baseline_fog_height_falloff" in codes, str(codes))
    check("flags script max_opacity", "off_live_baseline_fog_max_opacity" in codes, str(codes))
    check("flags script start_distance", "off_live_baseline_start_distance" in codes, str(codes))
    check("does not flag per-shot density",
          "off_live_baseline_fog_density" not in codes, str(codes))

    print("\n2c. disabled volumetric fog is an error (godrays would not render)")
    subsystem(fog_props={**DEFAULT_PROPS, "enable_volumetric_fog": False})
    report = film304_fog.drift_report()
    check("flags disabled volumetric fog",
          any(f["code"] == "volumetric_fog_disabled" and f["severity"] == "error"
              for f in report["drift"]["findings"]),
          str([f["code"] for f in report["drift"]["findings"]]))
    check("reports godrays impossible", report["fog_drive"]["godrays_possible"] is False)

    print("\n3. duplicate fog is an error")
    subsystem(extras=("ExponentialHeightFog_1",))
    report = film304_fog.drift_report()
    check("not singleton", not report["ownership_is_singleton"])
    check("duplicate is error severity",
          any(f["code"] == "duplicate_fog_actor" and f["severity"] == "error"
              for f in report["drift"]["findings"]))
    try:
        film304_fog.assert_single_owner()
        check("assert_single_owner raises", False, "no exception")
    except AssertionError:
        check("assert_single_owner raises", True)

    print("\n4. unbound UDS hook is an error")
    subsystem(bind_uds=False)
    report = film304_fog.drift_report()
    check("flags unbound hook",
          any(f["code"] == "uds_fog_hook_unbound" for f in report["drift"]["findings"]))

    print("\n5. visible UDS internal fog is the double-fog condition")
    subsystem(uds_internal_visible=True)
    report = film304_fog.drift_report()
    check("flags visible internal fog",
          any(f["code"] == "uds_internal_fog_visible" for f in report["drift"]["findings"]))

    print("\n6. apply() records before/after and does not touch extinction by default")
    subsystem()
    receipt = film304_fog.apply({"fog_density": 0.003},
                                film304_fog.INTENT_SHOT_LOOK)
    check("density changed", receipt["changed"]["fog_density"]["after"] == 0.003,
          json.dumps(receipt["changed"]))
    check("intent recorded", receipt["intent"]["name"] == "shot_look")
    check("nothing skipped", not receipt["skipped"], json.dumps(receipt["skipped"]))
    check("extinction untouched by shot look",
          _SUBSYSTEM.get_all_level_actors()[0].component.get_editor_property(
              "volumetric_fog_extinction_scale") == 2.5)

    print("\n7. apply_reviewed_baseline writes the EXTERNAL fog only")
    # Measured 2026-10-19: writing the volumetric settings onto the sky's internal fog
    # component makes UDS force enable_volumetric_fog back to False on EST_Fog_E1.
    # An external-only write holds. The dual seed is the trap, not the fix.
    subsystem(fog_props={**DEFAULT_PROPS,
                         "volumetric_fog_extinction_scale": 1.2,
                         "enable_volumetric_fog": False})
    sky_before = uds_actor().component.get_editor_property("volumetric_fog_extinction_scale")
    film304_fog.apply_reviewed_baseline()
    ext = _SUBSYSTEM.get_all_level_actors()[0].component
    check("external extinction now 2.5",
          ext.get_editor_property("volumetric_fog_extinction_scale") == 2.5)
    check("external volumetric re-enabled",
          ext.get_editor_property("enable_volumetric_fog") is True)
    check("sky internal NOT written",
          uds_actor().component.get_editor_property("volumetric_fog_extinction_scale")
          == sky_before,
          "apply_reviewed_baseline must not touch the sky's internal fog")
    check("drift clean after baseline", film304_fog.drift_report()["drift"]["clean"])

    print("\n8. a missing property is surfaced, not silently swallowed")
    subsystem(fog_props={k: v for k, v in DEFAULT_PROPS.items()
                         if k != "volumetric_fog_height"})
    receipt = film304_fog.apply({"volumetric_fog_height": 10.0},
                                film304_fog.INTENT_SHOT_LOOK)
    check("skipped reported", "volumetric_fog_height" in receipt["skipped"],
          json.dumps(receipt["skipped"]))

    print("\n9. console overrides carry the temporal reprojection default")
    overrides = film304_fog.render_console_overrides()
    check("temporal reprojection off",
          overrides.get("r.VolumetricFog.TemporalReprojection") == 0,
          json.dumps(overrides))

    print("\n9b. a renamed sky is reported, not silently treated as unbound")
    # Observed 2026-10-19: the sky was replaced and relabelled 'Ultra_Dynamic_Sky',
    # which made ~15 scripts fail on a KeyError and made the audit blame the fog hook
    # for an actor it never found.
    subsystem(uds_label="Ultra_Dynamic_Sky")
    report = film304_fog.drift_report()
    codes = [f["code"] for f in report["drift"]["findings"]]
    check("reports missing sky actor", "uds_actor_missing" in codes, str(codes))
    check("does not misreport hook unbound", "uds_fog_hook_unbound" not in codes, str(codes))
    check("names the candidate", report.get("uds_actor_candidates") == ["Ultra_Dynamic_Sky"],
          json.dumps(report.get("uds_actor_candidates")))
    try:
        film304_fog.get_uds_actor()
        check("get_uds_actor raises on rename", False, "no exception")
    except AssertionError as exc:
        check("get_uds_actor raises on rename", "Ultra_Dynamic_Sky" in str(exc), str(exc))

    print("\n10. lookup rejects an ambiguous label")
    subsystem(extras=("EST_Fog_E1",))
    try:
        film304_fog.get_fog_actor()
        check("duplicate label rejected", False, "no exception")
    except AssertionError:
        check("duplicate label rejected", True)

    print("\n11. fog drive mode classification")
    # Measured 2026-10-19. The drive mode is what makes an audit line actionable:
    # the same "volumetrics off" symptom has a completely different fix depending on
    # whether UDS is overwriting the value every tick.
    subsystem(fog_props={**DEFAULT_PROPS, "enable_volumetric_fog": False},
              uds_internal_visible=False)
    d = film304_fog.drive_report(film304_fog.snapshot())
    check("hook bound -> EXTERNAL_BOUND", d["mode"] == film304_fog.DRIVE_MODE_EXTERNAL_BOUND, d["mode"])
    check("authority is UDS", d["authority"] == "UDS", d["authority"])
    check("writable here (single visible fog)", d["values_writable_here"] is True)
    check("godrays impossible while off", d["godrays_possible"] is False)
    check("names the component not to write",
          d["do_not_write"] == "the sky's internal ExponentialHeightFogComponent",
          str(d["do_not_write"]))
    codes = [f["code"] for f in film304_fog.drift_report()["drift"]["findings"]]
    check("reports disabled volumetrics", "volumetric_fog_disabled" in codes, str(codes))
    check("no longer splits on UDS-driven",
          "volumetric_fog_disabled_uds_driven" not in codes, str(codes))
    finding = next(f for f in film304_fog.drift_report()["drift"]["findings"]
                   if f["code"] == "volumetric_fog_disabled")
    check("finding names the correct write",
          "apply_reviewed_baseline" in finding["detail"]
          and "Do NOT write the sky" in finding["detail"], finding["detail"])
    check("finding carries the drive mode",
          finding.get("drive_mode") == film304_fog.DRIVE_MODE_EXTERNAL_BOUND)

    subsystem(bind_uds=False, uds_internal_visible=False)
    d = film304_fog.drive_report(film304_fog.snapshot())
    check("unbound + hidden -> SPLIT_CLEAN", d["mode"] == film304_fog.DRIVE_MODE_SPLIT_CLEAN, d["mode"])
    check("authority is this project", d["authority"] == "this project", d["authority"])
    check("writable here", d["values_writable_here"] is True)
    check("nothing forbidden when unbound", d["do_not_write"] is None, str(d["do_not_write"]))

    subsystem(bind_uds=False, uds_internal_visible=True)
    d = film304_fog.drive_report(film304_fog.snapshot())
    check("unbound + visible -> SPLIT_DOUBLE_FOG",
          d["mode"] == film304_fog.DRIVE_MODE_SPLIT_DOUBLE_FOG, d["mode"])
    codes = [f["code"] for f in film304_fog.drift_report()["drift"]["findings"]]
    check("flags visible internal fog", "uds_internal_fog_visible" in codes, str(codes))

    subsystem(fog_props={**DEFAULT_PROPS, "enable_volumetric_fog": False},
              uds_internal_visible=False)
    check("EXTERNAL_BOUND with volumetrics off is clean of ownership errors",
          film304_fog.drift_report()["ownership_is_singleton"] is True)

    subsystem(uds_label="Ultra_Dynamic_Sky")
    d = film304_fog.drive_report(film304_fog.snapshot())
    check("missing sky -> NO_SKY", d["mode"] == film304_fog.DRIVE_MODE_NO_SKY, d["mode"])

    print("\n12. drive report is attached to the audit payload")
    subsystem()
    report = film304_fog.drift_report()
    check("payload has fog_drive", "fog_drive" in report, str(list(report.keys())))
    check("clean run reports godrays possible", report["fog_drive"]["godrays_possible"] is True,
          json.dumps(report["fog_drive"]))

    print("\n13. missing-fog errors say WHY, not just that it is missing")
    # Observed 2026-10-19: with no map open, the audit said only
    # "No fog actor labelled 'EST_Fog_E1'", which sent the reader hunting for a
    # renamed actor instead of telling them the editor was empty.
    globals()["_SUBSYSTEM"] = EditorActorSubsystem([])
    try:
        film304_fog.get_fog_actor()
        check("raises with no map open", False, "no exception")
    except AssertionError as exc:
        check("raises with no map open", True)
        check("names the empty-level cause", "no map open" in str(exc), str(exc))

    subsystem(fog_props=dict(DEFAULT_PROPS))
    for a in _SUBSYSTEM.get_all_level_actors():
        if a.get_actor_label() == "EST_Fog_E1":
            a._label = "Renamed_Fog"
    try:
        film304_fog.get_fog_actor()
        check("raises when fog renamed", False, "no exception")
    except AssertionError as exc:
        check("raises when fog renamed", True)
        check("lists what is actually present",
              "Renamed_Fog" in str(exc) and "renamed" in str(exc), str(exc))

    print()
    if FAILURES:
        print(f"FAILED {len(FAILURES)}: {FAILURES}")
        return 1
    print("ALL OFFLINE CHECKS PASSED")
    return 0


if __name__ == "__main__":
    import json
    raise SystemExit(main())