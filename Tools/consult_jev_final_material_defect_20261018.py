import importlib.util,os,json
from pathlib import Path
p=Path.home()/'.claude/mcp_servers/jev_mcp.py'
s=importlib.util.spec_from_file_location('jev_existing',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
os.environ['JEV_TIMEOUT_SECONDS']='35'
r=m.jev_ask('Final viewed 4K Office proof: eyes present and hand cups head, but David hair and blue shirt render white. Hair original instance points to ShaderIncident Candidate_2015 master despite brown BaseTint; shirt uses old EnvSandbox master and blue BaseTint, no textures. Dana isolated hair instance using surviving master renders correct brown. Deadline 25 minutes. Choose bounded next step.', ['DUPLICATE_WORKING_NONSKIN_INSTANCE_FOR_DAVID_HAIR_AND_SHIRT_PRESERVE_ORIGINALS','CHANGE_SHARED_MASTER','DELIVER_WHITE_HAIR_UNFIXED'], 'Reuse the already working isolated DanaParts hair material parent and its palette/texture bypass settings as separate David candidates, set David original brown/blue tints, assign only semantic hair/shirt slots, save, inspect one proof then export. Dana skin and shared graphs remain frozen. Advisory only, no visual approval.')
o=Path(__file__).resolve().parents[1]/'Saved/Audit/Closeout_20261018/jev_final_material_defect.json';o.write_text(json.dumps({'judgment':r,'visual_approval':False},indent=2));print(json.dumps(r))
