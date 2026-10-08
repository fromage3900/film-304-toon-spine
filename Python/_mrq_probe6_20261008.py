"""Probe #6: inspect the saved MasterConfig assets — which settings are present + enabled?

Output: %TEMP%/ue_py_mrq_probe6.txt
"""
import os
import tempfile

import unreal

rows = []
infl = unreal.MoviePipelineEditorLibrary  # == UMoviePipelineEditorBlueprintLibrary
for cfg in ("CFG_CTRL_ABC_20261008", "CFG_OS_SH020_proto_v02"):
    path = "/Game/MoviePipelines/" + cfg
    obj = unreal.load_asset(path)
    rows.append("%s: %s" % (cfg, obj.get_class().get_name() if obj else "MISSING"))
    if obj is None:
        continue
    settings = obj.get_all_settings() if hasattr(obj, "get_all_settings") else []
    for s in settings:
        try:
            enabled = s.get_editor_property("is_enabled")
            cls = s.get_class().get_name()
            extra = ""
            if cls == "MoviePipelineOutputSetting":
                extra = (" res=%r dir=%r fmt=%r" % (
                    s.get_editor_property("output_resolution"),
                    s.get_editor_property("output_directory"),
                    s.get_editor_property("file_name_format")))
            rows.append("  %s enabled=%s %s" % (cls, enabled, extra))
        except Exception as exc:                                   # noqa: BLE001
            rows.append("  row err: %s" % exc)

out = os.path.join(tempfile.gettempdir(), "ue_py_mrq_probe6.txt")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n".join(str(r) for r in rows))
print("[mrq-probe6] wrote %s" % out)
