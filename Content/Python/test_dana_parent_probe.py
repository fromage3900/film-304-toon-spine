"""Read-only authority probe for Dana's skin material in the meeting map."""
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
OUT=ROOT/'Saved/Audit/DanaMeeting/active_skin_material_authority.json'
MAP='/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office'
ACTOR='Film_Subject_Dana_v08_CleanSkin'

def path(obj):
    try:return obj.get_path_name() if obj else None
    except Exception:return None

@unreal.AutomationScheduler.add_latent_command
def probe():
    yield
    dirty=[p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
    if dirty:raise RuntimeError('Refusing probe while a map is dirty: '+str(dirty))
    if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP):
        raise RuntimeError('Could not load read-only probe map '+MAP)
    actor=next((a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
                if a.get_actor_label()==ACTOR),None)
    if not actor:raise RuntimeError('Dana actor not found: '+ACTOR)
    comp=actor.get_component_by_class(unreal.SkeletalMeshComponent)
    active=comp.get_material(0)
    parent=None
    try:parent=active.get_editor_property('parent')
    except Exception:pass
    row={'map':MAP,'actor':ACTOR,'mesh':path(comp.get_skeletal_mesh_asset()),
      'slot0_name':'danaSkin_mat','active_slot0':path(active),
      'active_class':active.get_class().get_name() if active else None,
      'active_parent':path(parent)}
    probes=[]
    for asset_path in [
      '/Game/Materials/Masters/M_Master_Toon_Face',
      '/Game/Materials/Masters/Film304/M_UniversalToon_Film304_v06',
      '/Game/Recovery/ShaderIncident_20261018/Candidate_2015/M_UniversalToon_Film304_v06']:
        obj=unreal.load_asset(asset_path)
        info={'requested_path':asset_path,'resolved_path':path(obj),
          'class':obj.get_class().get_name() if obj else None}
        if obj and isinstance(obj,unreal.MaterialInstanceConstant):
            try:info['parent']=path(obj.get_editor_property('parent'))
            except Exception as exc:info['parent_error']=str(exc)
        elif obj and isinstance(obj,unreal.Material):
            try:
                exprs=unreal.MaterialEditingLibrary.get_material_expressions(obj)
                info['expression_count']=len(exprs)
                info['parameters']=[{'class':e.get_class().get_name(),'name':str(e.get_editor_property('parameter_name'))}
                  for e in exprs if e.get_class().get_name() in ('MaterialExpressionScalarParameter','MaterialExpressionVectorParameter','MaterialExpressionTextureObjectParameter')]
            except Exception as exc:info['expression_error']=str(exc)
        probes.append(info)
    row['candidate_assets']=probes
    me=unreal.MaterialEditingLibrary
    row['active_parameters']={'scalars':{},'vectors':{},'textures':{}}
    for k in ['PaletteRampStrength','PaletteRampDriver','TextureWeight','Roughness','FilmGradeShadowLift','RampStrength','PatternStrength','FaceShadowMask']:
        try:row['active_parameters']['scalars'][k]=float(me.get_material_instance_scalar_parameter_value(active,k))
        except Exception as exc:row['active_parameters']['scalars'][k]='READBACK_ERROR: '+str(exc)
    for k in ['BaseTint','PaletteRampLow','PaletteRampMid','PaletteRampHigh','AccentTint','FaceShadowTint']:
        try:
            v=me.get_material_instance_vector_parameter_value(active,k)
            row['active_parameters']['vectors'][k]=[float(v.r),float(v.g),float(v.b),float(v.a)]
        except Exception as exc:row['active_parameters']['vectors'][k]='READBACK_ERROR: '+str(exc)
    for k in ['Albedo','PatternSDFMap','NormalMap','RoughnessMap']:
        try:row['active_parameters']['textures'][k]=path(me.get_material_instance_texture_parameter_value(active,k))
        except Exception as exc:row['active_parameters']['textures'][k]='READBACK_ERROR: '+str(exc)
    row['dirty_maps_after']=[p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(row,indent=2),encoding='utf-8')
    unreal.log('DANA_ACTIVE_SKIN_MATERIAL '+json.dumps(row))
