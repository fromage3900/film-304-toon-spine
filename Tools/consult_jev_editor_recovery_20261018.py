import importlib.util,json,os
from pathlib import Path
from datetime import datetime,timezone
adapter=Path.home()/'.claude/mcp_servers/jev_mcp.py'
spec=importlib.util.spec_from_file_location('jev_existing',adapter);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
os.environ['JEV_TIMEOUT_SECONDS']='45'
result=module.jev_ask('Choose recovery after a repeatable native editor defect. The original Office, native 5-job render queue and both 1080p presets saved successfully at 19:59:58-59. Immediately reloading the same map from a Python call holding live actors/components crashed TypedElement world cleanup. No saved asset failure is logged. The owner wants the scene locked and selected final renders by 21:00 Toronto; current 20:02. Skin and shared shaders frozen. Options?', ['REOPEN_SAVED_MAIN_VERIFY_PERSISTENCE_THEN_ONE_FINAL_BATCH','REPEAT_IN_CALL_MAP_RELOAD','DISCARD_SAVED_MAIN_AND_REBUILD_IN_NEW_MAP'], 'Preserve original Office; no new levels, no skin edits. Avoid the evidenced live-reference reload path. Verify actual saved queue/settings after normal reopen; do not claim finished visuals without inspecting exports.')
out=Path(__file__).resolve().parents[1]/'Saved/Audit/Closeout_20261018/jev_editor_recovery.json'
out.write_text(json.dumps({'time_utc':datetime.now(timezone.utc).isoformat(),'judgment':result,'visual_approval':False},indent=2))
print(json.dumps(result,indent=2))
