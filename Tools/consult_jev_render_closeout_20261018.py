"""Recorded closed-set Jev review using the existing adapter; no editor writes."""
import hashlib
import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT/'Docs/GOAL_ESTABLISHING_SHOTS_20261017.md'
OUT = ROOT/'Saved/Audit/Closeout_20261018/jev_render_closeout.json'

def main():
    adapter = Path.home()/'.claude/mcp_servers/jev_mcp.py'
    spec = importlib.util.spec_from_file_location('existing_jev_adapter', adapter)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    os.environ['JEV_TIMEOUT_SECONDS'] = '55'
    options = ['PRESERVE_THEN_FIX_CEILING_THEN_LIGHTING_AND_RENDER',
               'PRESERVE_THEN_RENDER_CURRENT_SCENE_BEFORE_CEILING_FIX',
               'HOLD_FOR_MISSING_EVIDENCE']
    context = PLAN.read_text(encoding='utf-8').split('## Historical material work')[0]
    result = module.jev_ask('Choose the next execution order for this film closeout. '
        'The owner explicitly requests ceiling/HVAC assembly, final Houdini convergence, '
        'material-instance/level assembly, lighting variations and updated render planning. '
        'Shared toon shader graphs are frozen after a recovered appearance incident. '
        'Only a new saved map and additive asset versions may be authored. '
        'Existing ceiling imports are vertical and unplaced; correct outward winding and axis proof '
        'are required. Direction is advisory and must not claim a render passed.', options, context)
    receipt = {'time_utc':datetime.now(timezone.utc).isoformat(),'plan':str(PLAN),
               'plan_sha256':hashlib.sha256(PLAN.read_bytes()).hexdigest(),
               'options':options,'judgment':result}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt,indent=2))

if __name__ == '__main__': main()
