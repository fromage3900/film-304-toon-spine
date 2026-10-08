"""One-shot API probe: what frame-pump / wait primitives does 5.8 Python expose?

The 2026-10-08 control session proved -ExecutePythonScript on the full editor
ISSUES Cmd: QUIT_EDITOR ~0.4 s after the script returns, so a post-tick
callback can never outlive the script. The script must therefore block and
pump editor frames itself until the latent capture lands. This probe lists
the candidate APIs so the driver uses what actually exists.

Run: UnrealEditor-Cmd.exe HumberToonShader.uproject -ExecutePythonScript=<abs> -stdout -unattended
Output: %TEMP%/ue_py_api_probe.txt
"""
import unreal

KEYS = ("tick", "pump", "frame", "sleep", "wait", "idle", "yield", "exec")


def interesting(names):
    return sorted(n for n in names if any(k in n.lower() for k in KEYS))


rows = []
rows.append("UNREAL module: %s" % interesting(dir(unreal)))
for cls_name in ("EditorLevelLibrary", "UnrealEditorSubsystem",
                 "EditorActorSubsystem", "EditorLoadingAndSavingUtils",
                 "SystemLibrary", "AutomationLibrary", "SlateApplication",
                 "Application", "RenderingLibrary",
                 "EditorTextureRenderingUtils", "MoviePipelineLibrary",
                 "KismetSystemLibrary"):
    obj = getattr(unreal, cls_name, None)
    if obj is None:
        rows.append("%s: MISSING" % cls_name)
        continue
    try:
        rows.append("%s: %s" % (cls_name, interesting(dir(obj))[:60]))
    except Exception as exc:                                       # noqa: BLE001
        rows.append("%s: ERROR %s" % (cls_name, exc))

# registration helpers live on the module: the post-tick callback exists --
# also look for unregister + the handle type
rows.append("register helpers: %s" % [n for n in dir(unreal)
                                      if n.startswith("register_")
                                      or n.startswith("unregister_")])

# SceneCapture2D export path (fallback if no pump exists)
try:
    sc = unreal.SceneCaptureComponent2D
    rows.append("SceneCaptureComponent2D: %s" % [n for n in dir(sc)
                                                 if not n.startswith("_")][:40])
    rows.append("EditorTextureRenderingUtils: %s" % dir(unreal.EditorTextureRenderingUtils))
except Exception as exc:                                           # noqa: BLE001
    rows.append("SceneCapture probe error: %s" % exc)

import os
import tempfile
out = os.path.join(tempfile.gettempdir(), "ue_py_api_probe.txt")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n".join(rows))
print("[probe] wrote %s" % out)
