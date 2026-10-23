"""Read-only audit of the post-process + stencil wiring in the open level.

Writes Saved/Audit/PPV/wiring.json. Saves nothing, changes nothing.

Three questions can only be answered by reading live objects, not by grepping
binaries: which post-process material is in which PPV slot; whether any actor
writes custom depth/stencil; and whether MI_* override names still exist on
their parents (a reparent leaves stale names that silently do nothing).
"""
import json
from pathlib import Path
import unreal

OUT = Path(unreal.Paths.project_dir()) / "Saved/Audit/PPV"
OUT.mkdir(parents=True, exist_ok=True)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MEL = unreal.MaterialEditingLibrary

report = {
    "stage": "ppv_wiring",
    "world": None,
    "renderer": {},
    "ppvs": [],
    "stencil_writers": [],
    "folders": {},
    "instances": [],
    "errors": [],
}
STEP = {"name": "init"}


def safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def err(where, exc):
    report["errors"].append(f"{where}: {str(exc)[:160]}")


def prop(obj, name, default=None):
    return safe(lambda: obj.get_editor_property(name), default)


def jsonable(v):
    """Enums, Vectors and Vector4s are not JSON types; flatten them."""
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, (list, tuple)):
        return [jsonable(x) for x in v]
    if isinstance(v, dict):
        return {str(k): jsonable(x) for k, x in v.items()}
    if all(hasattr(v, a) for a in ("r", "g", "b", "a")):
        return [v.r, v.g, v.b, v.a]
    if all(hasattr(v, a) for a in ("x", "y", "z")):
        return [v.x, v.y, v.z]
    return safe(lambda: str(v), None) or safe(lambda: repr(v), "?")


def cv_int(name):
    try:
        return unreal.SystemLibrary.get_console_variable_int_value(name)
    except Exception:
        return None


def obj_path(obj):
    if obj is None:
        return None
    return safe(lambda: obj.get_path_name(), None) or safe(lambda: str(obj), None)


def blendable_list(settings):
    out = []
    wb = prop(settings, "weighted_blendables", None)
    if wb is None:
        return out, "weighted_blendables missing"
    arr = prop(wb, "array", None)
    if arr is None:
        arr = safe(lambda: list(wb), None)
    if arr is None:
        return out, f"unreadable WeightedBlendables type={type(wb).__name__}"
    for e in arr:
        out.append({"weight": prop(e, "weight", None),
                    "object": obj_path(prop(e, "object", None))})
    return out, None


def parameter_names(material):
    names = {"scalar": set(), "vector": set(), "switch": set(), "texture": set()}
    if material is None:
        return {k: [] for k in names}
    for e in safe(lambda: MEL.get_material_expressions(material), []) or []:
        cls = type(e).__name__
        pn = safe(lambda: str(e.get_editor_property("parameter_name")), None)
        if not pn or pn == "None":
            continue
        if "ScalarParameter" in cls:
            names["scalar"].add(pn)
        elif "VectorParameter" in cls:
            names["vector"].add(pn)
        elif "StaticSwitchParameter" in cls:
            names["switch"].add(pn)
        elif "TextureParameter" in cls or "TextureObjectParameter" in cls:
            names["texture"].add(pn)
    return {k: sorted(v) for k, v in names.items()}


def api_parameter_names(material):
    """Authoritative list, including parameters nested inside material functions.

    get_material_expressions() does not descend into called functions, so a
    parameter owned by MF_StencilDepthAlpha looks 'stale' under a pure
    expression scan. These editors APIs do descend; use them as the arbiter.
    """
    out = {}
    for kind, fn_name in (("scalar", "get_scalar_parameter_names"),
                          ("vector", "get_vector_parameter_names"),
                          ("texture", "get_texture_parameter_names"),
                          ("switch", "get_static_switch_parameter_names")):
        fn = getattr(MEL, fn_name, None)
        if fn is None:
            out[kind] = None
            continue
        out[kind] = sorted(safe(lambda fn=fn: [str(n) for n in fn(material)], []) or [])
    return out


def instance_overrides(mi):
    out = {"scalar": [], "vector": [], "texture": [], "switch": []}
    for v in safe(lambda: mi.get_editor_property("scalar_parameter_values"), []) or []:
        info = prop(v, "parameter_info", None)
        out["scalar"].append(
            {"name": safe(lambda: str(info.get_editor_property("name")), "?"),
             "value": jsonable(prop(v, "parameter_value", None))})
    for v in safe(lambda: mi.get_editor_property("vector_parameter_values"), []) or []:
        info = prop(v, "parameter_info", None)
        val = prop(v, "parameter_value", None)
        out["vector"].append(
            {"name": safe(lambda: str(info.get_editor_property("name")), "?"),
             "value": [val.r, val.g, val.b, val.a] if val is not None else None})
    for v in safe(lambda: mi.get_editor_property("texture_parameter_values"), []) or []:
        info = prop(v, "parameter_info", None)
        out["texture"].append(
            {"name": safe(lambda: str(info.get_editor_property("name")), "?")})
    sp = prop(mi, "static_parameters", None)
    switches = prop(sp, "static_switch_parameters", None) if sp is not None else None
    for v in switches or []:
        info = prop(v, "parameter_info", None)
        out["switch"].append(
            {"name": safe(lambda: str(info.get_editor_property("name")), "?"),
             "value": prop(v, "value", None)})
    return out


PPV_KEYS = [
    "override_bloom_intensity", "bloom_intensity",
    "override_vignette_intensity", "vignette_intensity",
    "override_film_grain_intensity", "film_grain_intensity",
    "override_scene_fringe_intensity", "scene_fringe_intensity",
    "override_auto_exposure_bias", "auto_exposure_bias",
    "override_auto_exposure_method", "auto_exposure_method",
    "override_color_saturation", "color_saturation",
]

try:
    STEP["name"] = "world"
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    report["world"] = world.get_path_name()

    STEP["name"] = "renderer"
    for key in ("r.CustomDepth", "r.CustomDepthTemporalAAJitter",
                "r.TemporalAA.Upsampling", "r.AntiAliasingMethod"):
        report["renderer"][key] = cv_int(key)

    STEP["name"] = "actors"
    folders = {}
    for a in EAS.get_all_level_actors():
        label = safe(lambda: a.get_actor_label(), "?")
        cls = a.get_class().get_name()
        folder = safe(lambda: str(a.get_folder_path()), "None")
        folders[folder] = folders.get(folder, 0) + 1

        if cls == "PostProcessVolume":
            loc = safe(lambda: a.get_actor_location(), None)
            row = {"label": label, "folder": folder,
                   "blend_weight": prop(a, "blend_weight", None),
                   "priority": prop(a, "priority", None),
                   "unbound": prop(a, "unbound", None),
                   "location": [round(v, 2) for v in loc.to_tuple()] if loc else None}
            settings = prop(a, "settings", None)
            if settings is not None:
                blends, why = blendable_list(settings)
                row["blendables"] = blends
                if why:
                    row["blendables_error"] = why
                row["settings"] = {k: jsonable(prop(settings, k, None)) for k in PPV_KEYS}
            report["ppvs"].append(row)

        comps = safe(lambda: a.get_components_by_class(unreal.PrimitiveComponent), []) or []
        for c in comps:
            depth = prop(c, "render_custom_depth", None)
            stencil = prop(c, "custom_depth_stencil_value", None)
            if depth or (stencil not in (None, 0)):
                report["stencil_writers"].append(
                    {"actor": label, "class": cls,
                     "component": safe(lambda: c.get_name(), "?"),
                     "render_custom_depth": depth, "stencil": stencil})

    report["folders"] = dict(sorted(folders.items(), key=lambda kv: -kv[1]))

    STEP["name"] = "instances"
    checks = [
        "/Game/Materials/Instances/Film304/PostProcess/Outline/MI_Outline_Storybook",
        "/Game/Materials/Instances/Film304/PostProcess/Outline/MI_Outline_BoldSepia",
        "/Game/Materials/Instances/Film304/PostProcess/Outline/MI_Outline_Thin",
        "/Game/Materials/Instances/Film304/PostProcess/Composite/MI_Composite_Clean",
        "/Game/Materials/Instances/Film304/PostProcess/Composite/MI_Composite_Dither",
        "/Game/Materials/Instances/Film304/PostProcess/Composite/MI_Composite_Riso",
        "/Game/Materials/Instances/MI_Outline_Thin",
        "/Game/Materials/Instances/MI_Outline_Heavy",
        "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Render2026/MI_StorybookOutline_Render2026",
    ]
    for path in checks:
        mi = safe(lambda: unreal.load_asset(path), None)
        row = {"path": path, "loaded": mi is not None}
        if mi is not None:
            parent = prop(mi, "parent", None)
            row["parent"] = obj_path(parent)
            row["domain"] = str(prop(mi, "material_domain", None))
            ov = instance_overrides(mi)
            row["overrides"] = {k: [o["name"] for o in v] for k, v in ov.items()}
            pnames = parameter_names(parent)
            anames = api_parameter_names(parent) if parent is not None else {}
            row["parent_parameters_expressions"] = pnames
            row["parent_parameters_api"] = anames
            stale = {}
            for kind in ("scalar", "vector", "texture", "switch"):
                valid = set(pnames.get(kind, []))
                api = anames.get(kind)
                if api:
                    valid |= set(api)
                bad = [n for n in row["overrides"][kind] if n not in valid]
                if bad:
                    stale[kind] = bad
            row["stale_overrides"] = stale
            row["override_values"] = ov
        report["instances"].append(row)

    report["stage"] = "ok"
except Exception as exc:  # noqa: BLE001
    err("step:" + STEP["name"], exc)
    report["stage"] = "failed:" + STEP["name"]

(OUT / "wiring.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("wiring.json written; stage=" + report["stage"]
      + " ppvs=" + str(len(report["ppvs"]))
      + " stencil_writers=" + str(len(report["stencil_writers"]))
      + " errors=" + str(len(report["errors"])))
for row in report["ppvs"]:
    print("PPV", row["label"], "w=", row["blend_weight"], "pri=", row["priority"],
          "blendables=", row.get("blendables"))
for row in report["instances"]:
    print("MI", row["path"].split("/")[-1], "parent=", row.get("parent"),
          "stale=", row.get("stale_overrides"))
