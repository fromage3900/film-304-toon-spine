"""Render only Dana's private queue in the current editor process."""
import builtins
import json
import time
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'Saved/Audit/dana_rig_preview_capture.json'
build = json.loads((ROOT/'Saved/Audit/dana_refined_uds_build.json').read_text())
if unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages():
    raise RuntimeError('Save the current map before rendering')
queue = unreal.MoviePipelineQueue()
for item in build['jobs']:
    job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
    job.job_name = item['stem']
    job.map = unreal.SoftObjectPath(item['map']+'.'+item['map'].rsplit('/',1)[1])
    job.sequence = unreal.SoftObjectPath(item['sequence']+'.'+item['sequence'].rsplit('/',1)[1])
    job.set_configuration(unreal.load_asset(item['config']))
executor = unreal.MoviePipelinePIEExecutor()
record = {'status':'running','started_epoch':time.time(),'errors':[],'qualification':'helper geometry hidden in material slot; source rig and weights unchanged'}
REPORT.write_text(json.dumps(record,indent=2),encoding='utf-8')
def failed(exec_instance,pipeline,is_fatal,message):
    record['errors'].append({'fatal':is_fatal,'message':str(message)})
    REPORT.write_text(json.dumps(record,indent=2),encoding='utf-8')
def finished(exec_instance,success):
    rows=[]
    for item in build['jobs']:
        path=ROOT/'Saved/Renders/dana_refined_uds'/(item['stem']+'.png')
        fresh=path.exists() and path.stat().st_mtime>=record['started_epoch']
        rows.append({'shot':item['stem'],'image':str(path),'fresh':fresh,'bytes':path.stat().st_size if path.exists() else 0})
    record.update({'status':'completed','executor_success':bool(success),'captures':rows,'capture_pass':bool(success and all(r['fresh'] for r in rows))})
    REPORT.write_text(json.dumps(record,indent=2),encoding='utf-8')
    unreal.log('[DanaRigPreviewCapture] '+json.dumps(record))
executor.on_executor_errored_delegate.add_callable(failed)
executor.on_executor_finished_delegate.add_callable(finished)
builtins._dana_private_render_queue=queue
builtins._dana_private_render_executor=executor
executor.execute(queue)
unreal.log('[DanaRigPreviewCapture] started private three-shot queue')
