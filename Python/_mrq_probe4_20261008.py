"""Probe #4: the queue save/load API in MoviePipelineEditorLibrary / BlueprintLibrary.

Output: %TEMP%/ue_py_mrq_probe4.txt
"""
import os
import tempfile

import unreal

rows = []
for cls_name in ("MoviePipelineEditorLibrary", "MoviePipelineBlueprintLibrary"):
    obj = getattr(unreal, cls_name, None)
    if obj is None:
        rows.append("%s: MISSING" % cls_name)
        continue
    rows.append("%s: %s" % (cls_name, sorted(
        n for n in dir(obj) if not n.startswith("_"))))

rows.append("factories: %s" % sorted(
    n for n in dir(unreal) if "MoviePipeline" in n and "Factory" in n))

out = os.path.join(tempfile.gettempdir(), "ue_py_mrq_probe4.txt")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n\n".join(rows))
print("[mrq-probe4] wrote %s" % out)
