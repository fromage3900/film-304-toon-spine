"""Single source of truth for Film 304 height-fog ownership, values and drift detection.

Background
----------
`EST_Fog_E1` is the one and only volumetric fog owner in the Film 304 levels. Ultra
Dynamic Sky's `Custom Height Fog Actor` hook points at it and the sky's internal fog
component is hidden, so double fog cannot recur as long as exactly one actor exists.

Before this module, five scripts wrote fog values with five different numbers and
nothing detected the conflict:

    build_establishing_stage.py                 fog_density 0.0016
    converge_morning_fx_and_skyline_20261018.py fog_density 0.0018
    execute_houdini_cinematic_lookdev.py         fog_density 0.0020
    converge_master_showcase_20261018.py        fog_density 0.0030
    build_city_night_showcase_20261018.py       fog_density 0.0060

Re-running any of them silently reverted whatever the last one had set. Two scripts
also hard-coded `volumetric_fog_extinction_scale = 1.2` after the render review had
actually settled on 4.0 (Docs/GOAL_ESTABLISHING_SHOTS_20261017.md v07 entry), so a
re-run destroyed an approved value.

Design rules
------------
1. Resolve the actor by label with an assert on the count. The project was previously
   bitten by duplicate fog, and the old first-match `isinstance()` lookups would have
   silently re-broken it.
2. APPLY_* functions require an explicit intent token. Callers must say whether they
   are establishing a stage, authoring a shot look, or reading current state. That is
   what stops an unrelated script from stomping a reviewed value.
3. Every mutating helper returns the before/after delta so the caller can record a
   receipt instead of guessing.
4. `drift_report()` is read-only and safe to run at any time. It is the cheap guard
   that should run before any delivery render.

Run headless:
    UnrealEditor-Cmd.exe HumberToonShader.uproject ^
      -ExecutePythonScript="Python/audit_fog_drift.py" -stdout -unattended

Assert on the report FILE, not the log (see Python/spine_lib.py).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import unreal

# ---------------------------------------------------------------------------
# Ownership
# ---------------------------------------------------------------------------

#: The canonical fog actor label. Every writer resolves through this constant.
FOG_ACTOR_LABEL = "EST_Fog_E1"

#: The UDS actor that owns the `Custom Height Fog Actor` hook.
UDS_ACTOR_LABEL = "Film_UDS_Daylight"

#: Every property any script in this project reads or writes on the fog component.
#: Keep this list complete; `drift_report` iterates it.
FOG_PROPERTIES = (
    "fog_density",
    "fog_height",
    "fog_height_falloff",
    "fog_inscattering_color",
    "fog_inscattering_luminance",
    "fog_max_opacity",
    "fog_cutoff_distance",
    "start_distance",
    "enable_volumetric_fog",
    "volumetric_fog",
    "volumetric_fog_distance",
    "volumetric_fog_scattering_distribution",
    "volumetric_fog_extinction_scale",
    "volumetric_fog_start_distance",
    "volumetric_fog_cutoff_distance",
    "volumetric_fog_height",
)

# ---------------------------------------------------------------------------
# Reviewed values
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------

#: What `EST_Fog_E1` actually held after the UDS sky was replaced on 2026-10-19.
#:
#: Revision history:
#:   rev 1 (pre-swap)  density 0.0055, falloff 0.06488, start 7357.9
#:   rev 2 (post-swap) density 0.00551, falloff 0.06, start 7348.03,
#:                     inscattering luminance zeroed to (0,0,0,0)
#:
#: The swap replaced the sky, which re-seeded the fog through the
#: `Custom Height Fog Actor` hook. Note the inscattering tint went to zero: the warm
#: (0.55, 0.40, 0.30) establishing-stage tint is gone. That was deliberate in the
#: establishing pass and is worth restoring if the exterior look depends on it.
LIVE_BASELINE_20261018 = {
    "fog_density": 0.00551,
    "fog_height_falloff": 0.06,
    "fog_max_opacity": 1.0,
    "start_distance": 7348.03369140625,
    "enable_volumetric_fog": True,
    "volumetric_fog_extinction_scale": 2.5,
    "volumetric_fog_scattering_distribution": 0.65,
    "volumetric_fog_distance": 8000.0,
}

#: Volumetric fog extinction scale, taken from the live level (2.5).
#:
#: Docs/GOAL_ESTABLISHING_SHOTS_20261017.md v07 records "tests extinction 4.0 versus
#: the prior 2.5; keep only after render review". The level held 2.5 through the sky
#: swap, so either the review kept 2.5 or the 4.0 candidate was never applied. Do not
#: raise this to 4.0 on the strength of the doc entry alone -- that would change the
#: render with no visual approval behind it. Raising it is a Phase 3 A/B item, not a
#: config default.
REVIEWED_EXTINCTION_SCALE = 2.5

#: Forward Mie scattering. Documented in HOUDINI_ENGINE_VFX_AND_COMPOSED_STAGING as the
#: value that makes the window shafts read as crisp forward-scattered light. Matches the
#: live level.
REVIEWED_SCATTERING_DISTRIBUTION = 0.65

#: Volumetric fog integration distance. Matches the live level.
REVIEWED_VOLUMETRIC_DISTANCE = 8000.0

#: Properties this engine build (UE 5.8) does not expose as editor properties.
#: Probed live rather than guessed:
#:   fog_height                  -> renamed/removed in 5.8
#:   fog_inscattering_color      -> replaced by fog_inscattering_luminance in 5.8
#:   volumetric_fog              -> NOT readable; this is why the old check_fog.py was
#:                                 reporting the wrong thing (it read this, while every
#:                                 writer set enable_volumetric_fog)
#:   volumetric_fog_cutoff_distance, volumetric_fog_height -> not exposed
UNAVAILABLE_IN_THIS_ENGINE = (
    "fog_height",
    "fog_inscattering_color",
    "volumetric_fog",
    "volumetric_fog_cutoff_distance",
    "volumetric_fog_height",
)


@dataclass(frozen=True)
class FogIntent:
    """An explicit, auditable reason to mutate the fog component.

    Callers cannot mutate the fog without naming one of these, which makes an
    accidental stomping of a reviewed value a visible code change rather than a
    silent side effect of re-running an unrelated script.
    """

    #: Short machine-readable id, recorded in receipts.
    name: str
    #: Human-readable justification, recorded in receipts.
    reason: str


#: Authoring the exterior establishing shot. Fog is atmosphere and depth here.
INTENT_ESTABLISHING_STAGE = FogIntent(
    "establishing_stage",
    "Exterior establishing shot; fog provides atmospheric depth and hides the skyline horizon.",
)

#: Authoring one shot's look. Fog is graded per shot alongside the lighting variant.
INTENT_SHOT_LOOK = FogIntent(
    "shot_look",
    "Per-shot authored look for a single camera/sequence.",
)

#: Adopting the render-reviewed baseline. This is the only intent that may set
#: REVIEWED_EXTINCTION_SCALE.
INTENT_REVIEWED_BASELINE = FogIntent(
    "reviewed_baseline",
    "Adopt the render-reviewed volumetric extinction scale.",
)

#: Fixing ownership so exactly one volumetric fog is visible.
INTENT_OWNERSHIP = FogIntent(
    "ownership",
    "Ensure exactly one visible volumetric fog owner via the UDS custom-fog hook.",
)


@dataclass
class FogSnapshot:
    """Full read of the fog component, plus the derived drift verdict."""

    actor_label: str
    actor_path: str
    location_cm: list
    values: dict
    extra_fog_actors: list = field(default_factory=list)
    uds_custom_fog_actor: str | None = None
    uds_internal_fog_hidden: bool | None = None
    uds_actor_found: bool = True
    uds_actor_candidates: list = field(default_factory=list)
    timestamp_utc: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp_utc:
            self.timestamp_utc = datetime.now(timezone.utc).isoformat()

    @property
    def ownership_is_singleton(self) -> bool:
        return not self.extra_fog_actors

    def as_dict(self) -> dict:
        data = {
            "actor_label": self.actor_label,
            "actor_path": self.actor_path,
            "location_cm": self.location_cm,
            "values": {k: _jsonable(v) for k, v in self.values.items()},
            "extra_fog_actors": self.extra_fog_actors,
            "uds_custom_fog_actor": self.uds_custom_fog_actor,
            "uds_internal_fog_hidden": self.uds_internal_fog_hidden,
            "uds_actor_found": self.uds_actor_found,
            "uds_actor_candidates": self.uds_actor_candidates,
            "ownership_is_singleton": self.ownership_is_singleton,
            "timestamp_utc": self.timestamp_utc,
        }
        data["drift"] = drift_from_snapshot(self)
        data["fog_drive"] = drive_report(self)
        return data


def _jsonable(value):
    """Coerce a UE property value into something json.dump can handle."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    for attr in ("to_tuple", "export_text"):
        method = getattr(value, attr, None)
        if callable(method):
            try:
                return method() if attr == "to_tuple" else str(method())
            except Exception:  # pragma: no cover - defensive
                pass
    return str(value)


def _describe_actor_ref(ref) -> str | None:
    """Render an actor reference as its label.

    `Custom Height Fog Actor` returns a live actor object. Comparing the label is what
    actually proves the hook points at the right fog; stringifying the object would
    produce an address and always look unbound.
    """
    if ref is None:
        return None
    getter = getattr(ref, "get_actor_label", None)
    if callable(getter):
        try:
            return getter()
        except Exception:  # pragma: no cover - defensive
            pass
    return str(ref)


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


def _resolve_actor_source(actors):
    """Accept an EditorActorSubsystem, a list of actors, or a label->actor dict.

    Call sites in this project already pass all three shapes, and guessing wrong
    silently resolves no actors at all, so normalise here instead of at each call site.
    """
    if actors is None:
        return unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    if hasattr(actors, "get_all_level_actors"):
        return actors.get_all_level_actors()
    if isinstance(actors, dict):
        return list(actors.values())
    return list(actors)


def get_fog_actor(actors=None, label: str = FOG_ACTOR_LABEL) -> unreal.Actor:
    """Return the canonical fog actor, asserting there is exactly one.

    Replaces the old first-match ``isinstance(ExponentialHeightFog)`` lookups, which
    would have configured the wrong actor the moment a duplicate appeared.
    """
    matches = [a for a in _resolve_actor_source(actors) if a.get_actor_label() == label]
    if not matches:
        # Distinguish "the fog actor is gone" from "there is nothing loaded to look
        # at". An empty actor list means no map is open, and saying only "no fog
        # actor" sends the reader hunting for a renamed actor that does not exist.
        seen = _resolve_actor_source(actors)
        present = sorted(
            {a.get_actor_label() for a in seen if isinstance(a, unreal.ExponentialHeightFog)}
        )
        hint = (
            "No level actors at all - the editor has no map open. Open the level first."
            if not seen
            else (
                f"Height fog actors present: {present}. The fog was renamed, moved to "
                "another level, or deleted."
            )
        )
        raise AssertionError(f"No fog actor labelled {label!r}. {hint}")
    assert len(matches) == 1, (
        f"Expected exactly one fog actor labelled {label!r}, found {len(matches)}. "
        "Double fog is how the earlier ownership bug started; delete the extras before continuing."
    )
    return matches[0]


def get_fog_component(actors=None, label: str = FOG_ACTOR_LABEL):
    """Return the fog component of the canonical actor."""
    actor = get_fog_actor(actors, label)
    component = actor.get_component_by_class(unreal.ExponentialHeightFogComponent)
    assert component, f"{label} has no ExponentialHeightFogComponent."
    return component


def get_uds_actor(actors=None) -> unreal.Actor:
    """Return the sky actor, asserting it exists.

    Several scripts across this project resolve the sky by the label
    `Film_UDS_Daylight`. Replacing the sky once renamed it to `Ultra_Dynamic_Sky` and
    silently broke all of them, so give the lookup a named helper and a useful error.
    """
    all_actors = _resolve_actor_source(actors)
    matches = [a for a in all_actors if a.get_actor_label() == UDS_ACTOR_LABEL]
    if matches:
        return matches[0]
    present = sorted(
        {a.get_actor_label() for a in all_actors
         if a.get_class().get_name() == "Ultra_Dynamic_Sky_C"}
    )
    raise AssertionError(
        f"No sky actor labelled {UDS_ACTOR_LABEL!r}. Ultra_Dynamic_Sky_C actors present: "
        f"{present or ['none']}. Rename the sky back to {UDS_ACTOR_LABEL!r} so the "
        "setup scripts and sequencer bindings keep resolving."
    )


def find_extra_fog_actors(actors=None, label: str = FOG_ACTOR_LABEL) -> list:
    """Return any height-fog actors other than the canonical one."""
    return [
        a.get_actor_label()
        for a in _resolve_actor_source(actors)
        if isinstance(a, unreal.ExponentialHeightFog) and a.get_actor_label() != label
    ]


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------


def snapshot(actors=None, label: str = FOG_ACTOR_LABEL) -> FogSnapshot:
    """Read the full fog state without mutating anything."""
    actors_source = actors
    if actors is None:
        actors_source = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = _resolve_actor_source(actors_source)
    actor = get_fog_actor(all_actors, label)
    component = get_fog_component(all_actors, label)

    values = {}
    for prop in FOG_PROPERTIES:
        try:
            values[prop] = component.get_editor_property(prop)
        except Exception:
            # Property absent in this engine build. Absence is itself useful signal
            # for the audit, so record it rather than hiding it.
            values[prop] = "<unavailable>"

    uds = next((a for a in all_actors if a.get_actor_label() == UDS_ACTOR_LABEL), None)
    if uds is None:
        # The sky actor may have been replaced or renamed. Report that distinctly
        # from "hook bound to the wrong fog", otherwise the audit blames the hook for
        # an actor it never found.
        fallback = sorted(
            {
                a.get_actor_label()
                for a in all_actors
                if a.get_class().get_name() == "Ultra_Dynamic_Sky_C"
            }
        )
        return FogSnapshot(
            actor_label=actor.get_actor_label(),
            actor_path=actor.get_path_name(),
            location_cm=list(actor.get_actor_location().to_tuple()),
            values=values,
            extra_fog_actors=find_extra_fog_actors(all_actors, label),
            uds_custom_fog_actor=None,
            uds_internal_fog_hidden=None,
            uds_actor_found=False,
            uds_actor_candidates=fallback,
        )

    ref = uds.get_editor_property("Custom Height Fog Actor")
    custom = _describe_actor_ref(ref)
    internal = uds.get_components_by_class(unreal.ExponentialHeightFogComponent)
    internal_hidden = bool(internal) and all(not c.is_visible() for c in internal)

    return FogSnapshot(
        actor_label=actor.get_actor_label(),
        actor_path=actor.get_path_name(),
        location_cm=list(actor.get_actor_location().to_tuple()),
        values=values,
        extra_fog_actors=find_extra_fog_actors(all_actors, label),
        uds_custom_fog_actor=custom,
        uds_internal_fog_hidden=internal_hidden,
        uds_actor_found=True,
        uds_actor_candidates=[],
    )


# ---------------------------------------------------------------------------
# Fog drive mode
# ---------------------------------------------------------------------------

#: Fog ownership modes, as classified by `fog_drive_mode`.
#:
#: Correction, 2026-10-19. This file previously claimed the `Custom Height Fog Actor`
#: hook re-applies the sky's fog settings to EST_Fog_E1 every tick, and that both fog
#: components had to be seeded to keep volumetrics on. Both claims were wrong, and the
#: dual-seed "fix" they inspired actively switched volumetrics back off. Reproduced:
#:
#:   hook bound + write enable_volumetric_fog=True on EST_Fog_E1 only -> HOLDS (3+ ticks)
#:   write volumetric settings onto the sky's internal fog component -> UDS re-evaluates
#:   and forces enable_volumetric_fog back to False on EST_Fog_E1 in the same tick
#:
#: So the hook is not the writer; writing to the sky's internal fog component is. What
#: remains true is the ownership split: with the hook bound, UDS decides the sky's own
#: fog, and unbinding it lets UDS force-enable its internal fog, which is double fog.
DRIVE_MODE_EXTERNAL_BOUND = "EXTERNAL_BOUND"
DRIVE_MODE_SPLIT_CLEAN = "SPLIT_CLEAN"
DRIVE_MODE_SPLIT_DOUBLE_FOG = "SPLIT_DOUBLE_FOG"
DRIVE_MODE_WRONG_TARGET = "WRONG_TARGET"
DRIVE_MODE_NO_SKY = "NO_SKY"

_DRIVE_MODE_FIX = {
    DRIVE_MODE_EXTERNAL_BOUND:
        "Hook bound: the sky supplies its own fog and the sky's internal fog is hidden. "
        "EST_Fog_E1 is the single visible fog and is writable - but do NOT write the "
        "sky's internal fog component, because that makes UDS force "
        "enable_volumetric_fog back off here.",
    DRIVE_MODE_SPLIT_CLEAN:
        "Hook unbound and the sky's internal fog is hidden: this project owns the fog. "
        "Fog values set here will hold.",
    DRIVE_MODE_SPLIT_DOUBLE_FOG:
        "Hook unbound but the sky's internal fog is visible: two fogs are rendering. "
        "Rebind the hook, or hide the sky's internal fog - but note that with the hook "
        "unbound the sky re-enables it on the next tick.",
    DRIVE_MODE_WRONG_TARGET:
        f"The hook points at the wrong fog actor. It must point at {FOG_ACTOR_LABEL}.",
    DRIVE_MODE_NO_SKY:
        f"No {UDS_ACTOR_LABEL} actor; nothing drives the fog, but the sky lookups used "
        "throughout this project will fail.",
}


def fog_drive_mode(snap: FogSnapshot) -> str:
    """Classify who owns the fog values right now.

    This is the single field that explains most fog surprises in this project: the same
    audit output means different things depending on whether UDS is driving, and the
    remediation differs completely.
    """
    if not snap.uds_actor_found:
        return DRIVE_MODE_NO_SKY
    if snap.uds_custom_fog_actor == FOG_ACTOR_LABEL:
        return DRIVE_MODE_EXTERNAL_BOUND
    if snap.uds_custom_fog_actor is None:
        return (
            DRIVE_MODE_SPLIT_DOUBLE_FOG
            if snap.uds_internal_fog_hidden is False
            else DRIVE_MODE_SPLIT_CLEAN
        )
    return DRIVE_MODE_WRONG_TARGET


def drive_report(snap: FogSnapshot) -> dict:
    """Explain the drive mode, who has authority, and what to do about it."""
    mode = fog_drive_mode(snap)
    volumetric_on = snap.values.get("enable_volumetric_fog")
    # A single visible fog is the precondition for writing values here at all. With the
    # hook bound and the sky's internal fog hidden, EST_Fog_E1 is the only fog and a
    # write of enable_volumetric_fog holds (measured 2026-10-19).
    writable_here = mode in (DRIVE_MODE_SPLIT_CLEAN, DRIVE_MODE_EXTERNAL_BOUND)
    return {
        "mode": mode,
        "authority": "UDS" if mode == DRIVE_MODE_EXTERNAL_BOUND else "this project",
        "values_writable_here": writable_here,
        "volumetric_fog_enabled": volumetric_on,
        "godrays_possible": volumetric_on is True,
        "do_not_write": (
            "the sky's internal ExponentialHeightFogComponent"
            if mode == DRIVE_MODE_EXTERNAL_BOUND
            else None
        ),
        "explanation": _DRIVE_MODE_FIX[mode],
    }


def drift_from_snapshot(snap: FogSnapshot) -> dict:
    """Compare a snapshot against the reviewed baseline. Read-only."""
    findings = []
    mode = fog_drive_mode(snap)
    drive = drive_report(snap)

    if not snap.ownership_is_singleton:
        findings.append(
            {
                "severity": "error",
                "code": "duplicate_fog_actor",
                "detail": f"Extra height fog actors present: {snap.extra_fog_actors}",
            }
        )

    if not snap.uds_actor_found:
        findings.append(
            {
                "severity": "error",
                "code": "uds_actor_missing",
                "detail": f"No actor labelled {UDS_ACTOR_LABEL!r}. "
                f"Ultra_Dynamic_Sky_C actors present: {snap.uds_actor_candidates or ['none']}. "
                "The sky was replaced or renamed; every script that looks the sky up by "
                f"{UDS_ACTOR_LABEL!r} will fail.",
            }
        )
    elif snap.uds_custom_fog_actor != FOG_ACTOR_LABEL:
        # Covers both "hook not bound at all" (None) and "bound to the wrong fog",
        # which are both ownership errors that would reintroduce double fog.
        findings.append(
            {
                "severity": "error",
                "code": "uds_fog_hook_unbound",
                "detail": f"{UDS_ACTOR_LABEL} custom fog actor is "
                f"{snap.uds_custom_fog_actor!r}, expected {FOG_ACTOR_LABEL}.",
            }
        )

    if snap.uds_actor_found and snap.uds_internal_fog_hidden is False:
            findings.append(
                {
                    "severity": "error",
                    "code": "uds_internal_fog_visible",
                    "detail": f"{UDS_ACTOR_LABEL} still has a visible internal fog component; "
                    "this is the double-fog condition.",
                }
            )

    extinction = snap.values.get("volumetric_fog_extinction_scale")
    if isinstance(extinction, (int, float)) and abs(extinction - REVIEWED_EXTINCTION_SCALE) > 1e-4:
        findings.append(
            {
                "severity": "warning",
                "code": "extinction_scale_off_reviewed_value",
                "detail": f"volumetric_fog_extinction_scale={extinction}, "
                f"live baseline is {REVIEWED_EXTINCTION_SCALE}.",
            }
        )

    distribution = snap.values.get("volumetric_fog_scattering_distribution")
    if isinstance(distribution, (int, float)) and abs(
        distribution - REVIEWED_SCATTERING_DISTRIBUTION
    ) > 1e-4:
        findings.append(
            {
                "severity": "info",
                "code": "scattering_distribution_off_reviewed_value",
                "detail": f"volumetric_fog_scattering_distribution={distribution}, "
                f"documented value is {REVIEWED_SCATTERING_DISTRIBUTION}.",
            }
        )

    # Whole-baseline comparison against the values the level actually shipped with.
    # Per-shot density is intentionally excluded: it is authored per intent and is
    # expected to differ between an establishing, morning and night look.
    per_shot = {"fog_density"}
    for prop, expected in LIVE_BASELINE_20261018.items():
        if prop in per_shot:
            continue
        actual = snap.values.get(prop)
        if isinstance(actual, (int, float)) and abs(actual - expected) > 1e-4:
            findings.append(
                {
                    "severity": "warning",
                    "code": f"off_live_baseline_{prop}",
                    "detail": f"{prop}={actual}, level baseline is {expected}.",
                }
            )

    if snap.values.get("enable_volumetric_fog") is False:
        # The reason matters more than the symptom. Measured 2026-10-19: a write of
        # enable_volumetric_fog=True on EST_Fog_E1 holds, but only if nothing has
        # written the sky's internal fog component first - doing so makes UDS force
        # this flag back off. So the fix is a specific write, not a UI toggle.
        detail = (
            "enable_volumetric_fog is False, so no godrays will render. "
            f"Drive mode is {mode}. "
            "FIX: call film304_fog.apply_reviewed_baseline(), which writes EST_Fog_E1 "
            "only. Do NOT write the sky's internal fog component: that makes UDS force "
            "this flag back off on the next evaluation."
        )
        findings.append(
            {
                "severity": "error",
                "code": "volumetric_fog_disabled",
                "drive_mode": mode,
                "detail": detail,
            }
        )

    return {
        "clean": not findings,
        "findings": findings,
        "error_count": sum(1 for f in findings if f["severity"] == "error"),
        "warning_count": sum(1 for f in findings if f["severity"] == "warning"),
        "drive": drive,
    }


def drift_report(actors=None) -> dict:
    """Read-only guard. Safe to run before any delivery render."""
    snap = snapshot(actors)
    return snap.as_dict()


# ---------------------------------------------------------------------------
# Mutation
# ---------------------------------------------------------------------------


def apply(
    values: dict,
    intent: FogIntent,
    actors=None,
    label: str = FOG_ACTOR_LABEL,
    save: bool = False,
) -> dict:
    """Write fog properties under an explicit intent and return a before/after receipt.

    Every mutating path in the project should go through here so that receipts carry
    the intent and the exact delta, and so no script can change fog without a
    justification attached to it.
    """
    component = get_fog_component(actors, label)
    actor = get_fog_actor(actors, label)

    before = {}
    for prop in values:
        try:
            before[prop] = _jsonable(component.get_editor_property(prop))
        except Exception:
            before[prop] = "<unavailable>"

    applied = {}
    skipped = {}
    for prop, value in values.items():
        try:
            component.set_editor_property(prop, value)
            applied[prop] = _jsonable(value)
        except Exception as exc:
            # Surface rather than swallow: a silently skipped property is exactly how
            # the 1.2 extinction clobber went unnoticed.
            skipped[prop] = str(exc)

    component.modify()
    actor.modify()

    if save:
        unreal.EditorLevelLibrary.save_current_level()

    after = {}
    for prop in values:
        try:
            after[prop] = _jsonable(component.get_editor_property(prop))
        except Exception:
            after[prop] = "<unavailable>"

    changed = {k: {"before": before[k], "after": after[k]} for k in values if before[k] != after[k]}

    return {
        "intent": {"name": intent.name, "reason": intent.reason},
        "actor": label,
        "applied": applied,
        "skipped": skipped,
        "changed": changed,
        "no_op": sorted(k for k in values if before[k] == after[k]),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


def apply_stage_establishing(
    density: float,
    height_falloff: float = 0.12,
    start_distance: float = 3000.0,
    max_opacity: float = 0.92,
    inscattering_luminance=None,
    actors=None,
    save: bool = False,
) -> dict:
    """Exterior establishing shot look.

    Deliberately does NOT touch the extinction scale: that belongs to the reviewed
    baseline and is set by `apply_reviewed_baseline`.
    """
    values = {
        "fog_density": density,
        "fog_height_falloff": height_falloff,
        "start_distance": start_distance,
        "fog_max_opacity": max_opacity,
    }
    if inscattering_luminance is not None:
        values["fog_inscattering_luminance"] = inscattering_luminance
    return apply(values, INTENT_ESTABLISHING_STAGE, actors=actors, save=save)


def apply_shot_look(density: float, actors=None, **extra) -> dict:
    """A single shot's authored density. Everything else stays as reviewed."""
    values = {"fog_density": density, **extra}
    return apply(values, INTENT_SHOT_LOOK, actors=actors)


def reviewed_volumetric_values() -> dict:
    """The render-reviewed volumetric settings, as a single dict."""
    return {
        "enable_volumetric_fog": True,
        "volumetric_fog_extinction_scale": REVIEWED_EXTINCTION_SCALE,
        "volumetric_fog_scattering_distribution": REVIEWED_SCATTERING_DISTRIBUTION,
        "volumetric_fog_distance": REVIEWED_VOLUMETRIC_DISTANCE,
    }


def apply_reviewed_baseline(actors=None, save: bool = False) -> dict:
    """Adopt the render-reviewed volumetric settings on EST_Fog_E1.

    Write to the EXTERNAL fog actor only. Measured 2026-10-19: writing the volumetric
    settings onto the sky's own internal fog component makes UDS re-evaluate and force
    enable_volumetric_fog back to False on the external actor, killing the godrays.
    An external-only write of that flag holds across ticks with the hook bound.

    This is the only function permitted to write the extinction scale.
    """
    return apply(reviewed_volumetric_values(), INTENT_REVIEWED_BASELINE,
                 actors=actors, save=save)


def seed_both_fog_components(values: dict, actors=None, label: str = FOG_ACTOR_LABEL) -> dict:
    """Write fog values to BOTH the external actor and the sky's internal fog.

    DO NOT USE for the volumetric settings. Kept only because it is occasionally useful
    for density/height shaping, and because its failure mode is now a documented trap:
    writing volumetric properties on the sky's internal component causes UDS to turn
    enable_volumetric_fog back off on the external actor within the same tick. That was
    originally believed to be the "seed both so a re-apply carries the right values"
    fix; it is in fact the thing that breaks volumetrics.

    For volumetrics use `apply_reviewed_baseline`, which writes the external actor only.
    """
    component = get_fog_component(actors, label)
    sky_actor = get_uds_actor(actors)
    internal = sky_actor.get_components_by_class(unreal.ExponentialHeightFogComponent)
    assert internal, (
        f"{UDS_ACTOR_LABEL} has no internal ExponentialHeightFogComponent; nothing to seed."
    )

    receipts = {"external": apply(values, INTENT_REVIEWED_BASELINE, actors=actors, label=label),
                "sky_internal": {}, "warning":
                    "sky_internal was written; UDS may force enable_volumetric_fog "
                    "back to False on the external actor"}
    for sky_component in internal:
        sky_component.modify()
        before, after, skipped = {}, {}, {}
        for prop, value in values.items():
            try:
                before[prop] = _jsonable(sky_component.get_editor_property(prop))
            except Exception:
                before[prop] = "<unavailable>"
            try:
                sky_component.set_editor_property(prop, value)
            except Exception as exc:
                skipped[prop] = str(exc)
            # Read `after` unconditionally: a failed write still has a current value,
            # and omitting the key makes the receipt unreadable for that property.
            try:
                after[prop] = _jsonable(sky_component.get_editor_property(prop))
            except Exception:
                after[prop] = "<unavailable>"
        receipts["sky_internal"][sky_component.get_name()] = {
            "before": before, "after": after, "skipped": skipped,
        }
    return receipts


def assert_single_owner(actors=None) -> None:
    """Fail loudly on the double-fog condition before a delivery render."""
    extras = find_extra_fog_actors(actors)
    assert not extras, (
        "Double fog condition: extra ExponentialHeightFog actors present "
        f"{extras}. Remove or reassign them; {FOG_ACTOR_LABEL} must be the only owner."
    )


# ---------------------------------------------------------------------------
# Sequencer interaction
# ---------------------------------------------------------------------------


def fog_property_names(seq=None, actors=None) -> dict:
    """Map engine snake_case property names to sequencer track names.

    Sequencer tracks use the component property name verbatim (``FogDensity``), not the
    snake_case name used by ``set_editor_property`` (``fog_density``). Scripts writing
    sequencer tracks must go through this mapping so the two conventions cannot drift
    apart and a track silently targets a property that does not exist.
    """
    component = get_fog_component(actors)
    mapping = {}
    for prop in FOG_PROPERTIES:
        try:
            component.get_editor_property(prop)
        except Exception:
            continue  # Not exposed in this engine build; nothing to map.
        mapping[prop] = _to_pascal(prop)
    return mapping


def _to_pascal(snake: str) -> str:
    """fog_density -> FogDensity."""
    return "".join(part.capitalize() for part in snake.split("_"))


# ---------------------------------------------------------------------------
# Console variables
# ---------------------------------------------------------------------------

#: Volumetric fog temporal reprojection accumulates history and was responsible for
#: most of the loop seam drift (wrap MAE 1.8899 -> 0.3451, ~82 percent, when disabled).
#: It is currently applied as a per-shot MRQ override in lock_main_office_delivery.
#: ``render_console_overrides`` returns it so new sequences can adopt the same setting
#: instead of silently inheriting the drift.
VOLUMETRIC_FOG_STABLE_CONSOLE = {"r.VolumetricFog.TemporalReprojection": 0}


def render_console_overrides() -> dict:
    """Console overrides every Film 304 render path should apply.

    Shot-scoped on purpose: changing the global project setting was rejected in review.
    """
    return dict(VOLUMETRIC_FOG_STABLE_CONSOLE)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def write_report(data: dict, subdir: str = "Film304_Closeout_20261018") -> Path:
    """Write a JSON receipt next to the other closeout audit files."""
    out = Path(unreal.Paths.project_dir()) / "Saved/Audit" / subdir
    out.mkdir(parents=True, exist_ok=True)
    path = out / "fog_drift_report.json"
    path.write_text(json.dumps(data, indent=2, default=_jsonable), encoding="utf-8")
    return path