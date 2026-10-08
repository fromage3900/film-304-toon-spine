"""Probe #2: the MoviePipeline (MRQ) python surface for in-process stills.

Follow-up to _api_probe_20261008.py: the driver needs a primitive that
RENDERS AND BLOCKS inside one startup-script session (5.8's
-ExecutePythonScript issues QUIT_EDITOR when the script returns, so a
post-tick wait model is dead). MoviePipelineInProcessExecutor is the
engine-native block-and-render. This probe lists the exact classes and
methods to drive it.

Output: %TEMP%/ue_py_mrq_probe.txt
"""
import os
import tempfile

import unreal

rows = []

rows.append("MOVIEPIPELINE CLASSES: %s" % sorted(
    n for n in dir(unreal) if n.startswith("MoviePipeline")))

for cls_name in ("MoviePipelineInProcessExecutor", "MoviePipelineExecutorJob",
                 "MoviePipelineQueueSubsystem", "MoviePipelineQueue",
                 "MoviePipelineConfigBase", "MoviePipelineMasterShotConfig",
                 "MoviePipelinePrimaryConfig",
                 "MoviePipelineImageSequenceOutput_PNG",
                 "MoviePipelineOutputSetting", "MoviePipelineAntiAliasingSetting",
                 "MoviePipelineGameOverrideSetting",
                 "MoviePipelineConsoleVariableSetting",
                 "MoviePipelineCameraCutSection", "MoviePipelineSetting"):
    obj = getattr(unreal, cls_name, None)
    if obj is None:
        rows.append("%s: MISSING" % cls_name)
        continue
    try:
        rows.append("%s: %s" % (cls_name, sorted(
            n for n in dir(obj) if not n.startswith("_"))))
    except Exception as exc:                                       # noqa: BLE001
        rows.append("%s: ERROR %s" % (cls_name, exc))

# new_object availability for in-memory configs
rows.append("new_object: %s" % hasattr(unreal, "new_object"))

out = os.path.join(tempfile.gettempdir(), "ue_py_mrq_probe.txt")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n\n".join(rows))
print("[mrq-probe] wrote %s" % out)
