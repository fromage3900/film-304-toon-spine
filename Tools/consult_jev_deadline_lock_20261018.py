"""Closed-set deadline/defect audit; advisory only, no editor writes."""
import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path

root=Path(__file__).resolve().parents[1]
adapter=Path.home()/'.claude/mcp_servers/jev_mcp.py'
spec=importlib.util.spec_from_file_location('existing_jev_adapter',adapter)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
os.environ['JEV_TIMEOUT_SECONDS']='55'
options=['LOCK_PERSISTENCE_AND_DELIVERY_BLOCKERS_THEN_FINAL_BATCH','RESTORE_ENTIRE_PRE_DUSK_AUDIT_THEN_RENDER','HAND_OFF_SAVED_QUEUE_ONLY_WITHOUT_NEW_EXPORTS']
question='Choose the smallest reliable closeout before 9 PM Toronto tonight. Also advise bounded fixes for each observed defect; do not certify visuals you cannot see.'
context={
    'deadline':'2026-10-18 21:00 America/Toronto; current approximately 19:54',
    'authority':'Original /Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office only; no new maps; no Git operations',
    'owner_constraints':['Dana CURRENT face assignment and all its material parameters are now strictly frozen by the owner; do not restore/reparent/change her skin','Shared toon master/function/profile graphs frozen','Finish scene and persistence before more render experiments','Converge morning work from two existing copies; provide user-operable saved render queue and light variants','Minimize tool calls; fix any newly observed defects with Jev advice'],
    'measured_findings':['Both morning copies read in memory, 225/238 actors; main retained as active world','Main has one fitted v05 ceiling pair, one film dust actor, three shafts, existing UDS, four head-anchored snore spawnables','Some set_material changes did not mark the level dirty; explicit actor.modify/component.modify is needed before targeted save and reload proof','v49 shows huge white dust cards in room; disabling film dust removes them in v50. Renderer uses film-owned SubstrateUnlit material with legacy translucent blend; existing clear-cornea graph uses colored-transmittance mode','David wrist 180-degree roll makes fingers hang down; measured original palm-normal/head target yields approximately -59.4 degree local forearm roll for palm toward head, keeping wrist position fixed','Original pre-Dusk material audit has only 23 actors and an older 10-slot Dana; current mesh has 12 named slots, so blind replay is invalid','v49 skyline avoids former cream-white gap but currently too dense/close; later Gemini prompt should be bounded to existing Houdini skyline/fog','No saved MRQ queue yet; native duplicate of transient queue now created successfully, pending populated jobs/preset/save'],
    'proposed_bounded_fixes':['Explicitly modify/save changed components, reacquire actors after MRQ, verify same-map reload before final exports','Repair only film-owned dust material transparency using supported colored-transmittance mode, reduce oversized sprites; keep existing system and native collection loop clock','Replace only left wrist track in a preserved duplicate of original 48-frame sleep clip using measured -60 roll; inspect contact','Populate native saved queue with main-only shot paths and fixed output directory, one enabled default job, native lighting options; disable duplicate autoplay during rendering','No more Dana skin edits under any circumstance; capture and assert exact current assignment remains unchanged']}
result=module.jev_ask(question,options,json.dumps(context,indent=2))
if result.get('status')=='error':
    result=module.jev_ask('Deadline audit: choose one option. Original Office only; owner freezes Dana skin/shared shaders. Assembly changes sometimes fail to persist without actor/component.modify(). Dust has opaque oversized cards (isolated by disable test); proposes fixing only its own Substrate transparency and shrinking sprites. David palm 180 flip hangs down; geometric alignment suggests -60 local wrist roll. Need saved MRQ queue/light options and persistence proof before one final render batch. Recommend the bounded next action and any safer defect remedies.',options,'Hard deadline 9 PM Toronto tonight; minimize calls; preserve all original assets; no new levels; no skin changes. Do not assert visual sign-off.')
receipt={'time_utc':datetime.now(timezone.utc).isoformat(),'question':question,'options':options,'context':context,'judgment':result,'visual_approval':False}
out=root/'Saved/Audit/Closeout_20261018/jev_deadline_lock.json';out.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
