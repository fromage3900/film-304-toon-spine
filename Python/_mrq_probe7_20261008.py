"""Probe #7: what settings does the MoviePipelinePrimaryConfig CDO carry by default?

Output: %TEMP%/ue_py_mrq_probe7.txt
"""
import os
import tempfile

import unreal

rows = []
cdo = unreal.get_default_object(unreal.MoviePipelinePrimaryConfig)
settings = cdo.get_all_settings()
for s in settings:
    rows.append("CDO default: %s" % s.get_class().get_name())

# also the executor-level config defaults
try:
    subsys = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    q = subsys.get_queue()
    j = q.allocate_new_job(unreal.MoviePipelineExecutorJob)
    j.setup_basic_configuration()
    for s in j.get_configuration().get_all_settings():
        rows.append("basic config: %s" % s.get_class().get_name())
except Exception as exc:                                           # noqa: BLE001
    rows.append("basic config probe FAILED: %s" % exc)

out = os.path.join(tempfile.gettempdir(), "ue_py_mrq_probe7.txt")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n".join(str(r) for r in rows))
print("[mrq-probe7] wrote %s" % out)
