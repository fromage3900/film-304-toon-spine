"""Dump L_Toon_Shot_Office's actual lighting rig versus the stage spec.

Output: %TEMP%/office_light_dump.json
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

for a in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        cls = a.get_class().get_name()
        label = a.get_actor_label()
        if cls in ("DirectionalLight", "SkyLight", "RectLight", "PointLight",
                   "SpotLight", "ExponentialHeightFog", "SkyAtmosphere",
                   "VolumetricCloud", "EnvironmentLight", "OpenColorIODisplay"):
            row = {"label": label, "class": cls}
            comp = None
            for getter in ("get_component_by_class",):
                pass
            ccls = {"DirectionalLight": unreal.DirectionalLightComponent,
                    "SkyLight": unreal.SkyLightComponent,
                    "RectLight": unreal.RectLightComponent,
                    "PointLight": unreal.PointLightComponent,
                    "SpotLight": unreal.SpotLightComponent}.get(cls)
            if ccls:
                comp = a.get_component_by_class(ccls)
                if comp:
                    try:
                        row["intensity"] = comp.get_editor_property("intensity")
                    except Exception:
                        pass
                    try:
                        row["light_color"] = str(comp.get_editor_property("light_color"))
                    except Exception:
                        pass
                    try:
                        row["source_type"] = str(comp.get_editor_property("source_type"))
                    except Exception:
                        pass
                    try:
                        row["cubemap"] = (comp.get_editor_property("cubemap")
                                          .get_path_name() if cls == "SkyLight" else None)
                    except Exception:
                        pass
            try:
                row["rotation"] = str(a.get_actor_rotation())
            except Exception:
                pass
            rows.append(row)
    except Exception as exc:                                       # noqa: BLE001
        rows.append({"error": str(exc)[:80]})

out = os.path.join(tempfile.gettempdir(), "office_light_dump.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(rows, fh, indent=2)
print("[lightdump] -> %s" % out)
