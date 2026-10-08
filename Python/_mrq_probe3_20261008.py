"""Probe #3: exact names for the MRQ queue builder.

- enum members of MoviePipelineTextureStreamingMethod / AntiAliasingMethod
- whether job.map / job.sequence accept plain strings vs need SoftObjectPath
- MoviePipelineQueue asset-save path (allocate_new_job signature)
Output: %TEMP%/ue_py_mrq_probe3.txt
"""
import os
import tempfile

import unreal

rows = []

for enum_name in ("MoviePipelineTextureStreamingMethod", "AntiAliasingMethod",
                  "MoviePipelineGameMode"):
    e = getattr(unreal, enum_name, None)
    rows.append("%s: %s" % (enum_name, [n for n in dir(e) if not n.startswith("_")] if e else "MISSING"))

rows.append("SoftObjectPath ctor: %s" % hasattr(unreal, "SoftObjectPath"))

# property types on the job: read the defaults back to learn the types
job = unreal.new_object(unreal.MoviePipelineExecutorJob)
for prop in ("map", "sequence"):
    try:
        rows.append("job.%s default: %r (type %s)"
                    % (prop, job.get_editor_property(prop),
                       type(job.get_editor_property(prop)).__name__))
    except Exception as exc:                                       # noqa: BLE001
        rows.append("job.%s ERROR %s" % (prop, exc))

rows.append("queue.allocate_new_job doc: %s" %
            getattr(unreal.MoviePipelineQueue.allocate_new_job, "__doc__", None))
rows.append("MasterConfig methods: %s" % [n for n in dir(unreal.MoviePipelineMasterConfig)
                                          if not n.startswith("_")])
rows.append("OutputSetting.output_resolution doc: %s" %
            getattr(unreal.MoviePipelineOutputSetting, "__doc__", None)[:200])

# Try a string assignment against a transient queue/job/config trio.
try:
    q = unreal.new_object(unreal.MoviePipelineQueue)
    j = q.allocate_new_job(unreal.MoviePipelineExecutorJob)
    j.set_editor_property("map", "/Game/Maps/L_Toon_Shot_Office.L_Toon_Shot_Office")
    rows.append("job.map str assign OK -> %r" % j.get_editor_property("map"))
except Exception as exc:                                           # noqa: BLE001
    rows.append("job.map str assign FAILED: %s" % exc)

try:
    cfg = unreal.new_object(unreal.MoviePipelineMasterConfig)
    out_set = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting, True)
    out_set.set_editor_property("output_resolution", unreal.IntPoint(1280, 720))
    rows.append("output_resolution assign OK -> %r" % out_set.get_editor_property("output_resolution"))
except Exception as exc:                                           # noqa: BLE001
    rows.append("config/settings FAILED: %s" % exc)

out = os.path.join(tempfile.gettempdir(), "ue_py_mrq_probe3.txt")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n".join(rows))
print("[mrq-probe3] wrote %s" % out)
