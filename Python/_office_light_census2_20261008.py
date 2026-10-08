"""Office light/env census v2: what could eat the direct sun in L_Toon_Shot_Office?

Dumps every light (with enabled-ness, channels, bpm), every volumetric fog /
cloud / atmo / shadow-impactor, plus the level bounds map.
Output: %TEMP%/office_light_census2.json
"""
import json
import os
import tempfile

from pathlib import Path

import unreal

REPO = Path(__file__).resolve().parents[1]
LEVEL = "/Game/Maps/L_Toon_Shot_Office"
rows = []

if not unreal.LevelEditorSubsystem().load_level(LEVEL):
    raise RuntimeError("level did not load")

INTEREST = {
    "DirectionalLight": unreal.DirectionalLightComponent,
    "SkyLight": unreal.SkyLightComponent,
    "RectLight": unreal.RectLightComponent,
    "PointLight": unreal.PointLightComponent,
    "SpotLight": unreal.SpotLightComponent,
}

for a in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        cls = a.get_class().get_name()
        label = a.get_actor_label()
        if cls in INTEREST:
            comp = a.get_component_by_class(INTEREST[cls])
            row = {"label": label, "class": cls}
            if comp:
                for prop in ("intensity", "b_enabled", "cast_shadows",
                             "cast_static_shadows", "use_light_shafts",
                             "lighting_channels", "b_use_temperature",
                             "indirect_lighting_intensity"):
                    try:
                        row[prop] = str(comp.get_editor_property(prop))
                    except Exception:
                        pass
                try:
                    row["rotation"] = str(a.get_actor_rotation())
                except Exception:
                    pass
            rows.append(row)
        elif cls in ("VolumetricCloud", "SkyAtmosphere", "ExponentialHeightFog",
                     "LightingCloud", "CubemapLight", "EnvironmentLight",
                     "HeightFog", "PostProcessVolume", "SkyLightVolume",
                     "SkyDome", "SkyLightActor"):
            row = {"label": label, "class": cls}
            try:
                row["comp_props"] = [n for n in dir(a) if not n.startswith("get_")][:6]
            except Exception:
                pass
            try:
                row["bounds"] = str(a.get_actor_bounds(False))
            except Exception:
                pass
            try:
                row["scale"] = str(a.get_actor_scale3d())
            except Exception:
                pass
            try:
                row["loc"] = str(a.get_actor_location())
            except Exception:
                pass
            rows.append(row)
    except Exception as exc:                                       # noqa: BLE001
        rows.append({"error": str(exc)[:80]})

out = os.path.join(tempfile.gettempdir(), "office_light_census2.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(rows, fh, indent=2)
print("[census2] -> %s" % out)
