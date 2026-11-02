"""One-look-per-process Dana portrait render; temporary test driver."""
import json, math, struct, time, traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir())
OUT=ROOT/'Showcase/Dana/Meeting_20261023/Renders'
REPORT=ROOT/'Saved/Audit/DanaMeeting/capture_report.json'
REQUEST=ROOT/'Saved/Audit/DanaMeeting/render_request.json'
CAMERA_PROBE=ROOT/'Saved/Audit/DanaMeeting/camera_probe.json'
MAP='/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office'
SEQ='/Game/Sequences/Film304Closeout_20261018/LS_MainOffice_Dana_Neutral_48f_v01'
SKIN='Film_Subject_Dana_v08_CleanSkin';CAM_DEFAULT='Film_Cam_Showcase_DanaPortrait_v02'
W,H=2560,1440
try:unreal.PyAutomationTest.set_py_latent_command_timeout(600.0)
except Exception:pass

def png_dims(path):
    try:
        with open(path,'rb') as f:h=f.read(24)
        if h[:8]!=b'\x89PNG\r\n\x1a\n':return None
        return list(struct.unpack('>II',h[16:24]))
    except:return None
def find_actor(label):
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if a.get_actor_label()==label:return a
    raise RuntimeError('Missing actor: '+label)
def asset(path):
    v=unreal.load_asset(path)
    if not v:raise RuntimeError('Missing asset: '+path)
    return v
def path(v):
    try:return v.get_path_name() if v else None
    except Exception:return None

def face_target(component, actor):
    points=[]
    for name in ('Eye_L','Eye_R'):
        try:
            xf=component.get_bone_transform(name,unreal.RelativeTransformSpace.RTS_WORLD)
            points.append(xf.translation)
        except Exception:pass
    if points:
        return unreal.Vector(sum(p.x for p in points)/len(points),
          sum(p.y for p in points)/len(points),sum(p.z for p in points)/len(points)),'Eye_L/Eye_R'
    try:
        xf=component.get_bone_transform('Head_M',unreal.RelativeTransformSpace.RTS_WORLD)
        return xf.translation,'Head_M'
    except Exception:
        center,extent=actor.get_actor_bounds(False)
        return unreal.Vector(center.x,center.y,center.z+extent.z*.72),'bounds fallback'

def texture_asset(req):
    texture_path=req['texture_path']
    texture=unreal.load_asset(texture_path)
    if texture:return texture
    unreal.EditorAssetLibrary.make_directory(req['texture_destination'])
    task=unreal.AssetImportTask()
    task.set_editor_properties({'filename':req['texture_file'],
      'destination_path':req['texture_destination'],'destination_name':req['texture_name'],
      'automated':True,'replace_existing':False,'save':True})
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture=asset(texture_path)
    if req.get('data_texture',False):
        texture.set_editor_property('srgb',False)
        texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_MASKS)
        texture.set_editor_property('address_x',unreal.TextureAddress.TA_CLAMP)
        texture.set_editor_property('address_y',unreal.TextureAddress.TA_CLAMP)
        texture.set_editor_property('filter',unreal.TextureFilter.TF_BILINEAR)
        unreal.EditorAssetLibrary.save_loaded_asset(texture,False)
    return texture

def face_sdf_instance(req):
    tools=unreal.AssetToolsHelpers.get_asset_tools()
    instance_path=req['instance_path']
    instance=unreal.load_asset(instance_path)
    if not instance:
        unreal.EditorAssetLibrary.make_directory(req['instance_destination'])
        instance=tools.create_asset(req['instance_name'],req['instance_destination'],
          unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
    if not instance:raise RuntimeError('Could not create face-SDF prototype instance')
    parent=asset(req['parent_path'])
    instance.modify()
    result=unreal.MaterialEditingLibrary.set_material_instance_parent(instance,parent)
    if result is False:
        raise RuntimeError('Unreal rejected prototype parent assignment: '+req['parent_path'])
    unreal.MaterialEditingLibrary.update_material_instance(instance)
    try:actual_parent=instance.get_editor_property('parent')
    except Exception:actual_parent=None
    if not actual_parent or actual_parent.get_path_name()!=parent.get_path_name():
        # A direct reflected-property fallback is restricted to this additive
        # meeting prototype and is followed by a save/readback gate.
        instance.set_editor_property('parent',parent)
        unreal.MaterialEditingLibrary.update_material_instance(instance)
    for k,v in req.get('scalars',{}).items():
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance,k,float(v))
    for k,v in req.get('vectors',{}).items():
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
          instance,k,unreal.LinearColor(float(v[0]),float(v[1]),float(v[2]),float(v[3])))
    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
      instance,'PatternSDFMap',texture_asset(req))
    unreal.MaterialEditingLibrary.update_material_instance(instance)
    if not unreal.EditorAssetLibrary.save_loaded_asset(instance,False):
        raise RuntimeError('Could not save face-SDF prototype instance')
    readback={'asset_path':instance.get_path_name()}
    try:
        parent=instance.get_editor_property('parent')
        readback['parent']=parent.get_path_name() if parent else None
    except Exception as exc:readback['parent_error']=str(exc)
    if readback.get('parent')!=parent.get_path_name():
        raise RuntimeError('Prototype parent readback mismatch: requested '+
          parent.get_path_name()+' got '+str(readback.get('parent')))
    readback['scalars']={}
    for k in req.get('scalars',{}):
        try:readback['scalars'][k]=float(unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(instance,k))
        except Exception as exc:readback['scalars'][k]='READBACK_ERROR: '+str(exc)
    readback['vectors']={}
    for k in req.get('vectors',{}):
        try:
            v=unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(instance,k)
            readback['vectors'][k]=[float(v.r),float(v.g),float(v.b),float(v.a)]
        except Exception as exc:readback['vectors'][k]='READBACK_ERROR: '+str(exc)
    try:
        tex=unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(instance,'PatternSDFMap')
        readback['PatternSDFMap']=tex.get_path_name() if tex else None
    except Exception as exc:readback['PatternSDFMap']='READBACK_ERROR: '+str(exc)
    return instance,readback

def universal_skin_instance(req):
    source=asset(req['source_instance_path'])
    instance_path=req['instance_path']
    if unreal.EditorAssetLibrary.does_asset_exist(instance_path):
        raise RuntimeError('Refusing overwrite of Universal skin prototype: '+instance_path)
    instance=unreal.EditorAssetLibrary.duplicate_asset(
        source.get_path_name().split('.')[0],instance_path)
    if not instance:raise RuntimeError('Could not duplicate Dana Universal skin instance')
    source_parent=source.get_editor_property('parent')
    instance.modify()
    me=unreal.MaterialEditingLibrary
    for k,v in req.get('scalars',{}).items():
        me.set_material_instance_scalar_parameter_value(instance,k,float(v))
    for k,v in req.get('vectors',{}).items():
        me.set_material_instance_vector_parameter_value(
          instance,k,unreal.LinearColor(float(v[0]),float(v[1]),float(v[2]),float(v[3])))
    for k,v in req.get('static_switches',{}).items():
        me.set_material_instance_static_switch_parameter_value(instance,k,bool(v))
    me.update_material_instance(instance)
    if not unreal.EditorAssetLibrary.save_loaded_asset(instance,False):
        raise RuntimeError('Could not save Dana Universal skin prototype')
    instance=asset(instance_path)
    readback={'asset_path':instance.get_path_name(),
      'parent':path(instance.get_editor_property('parent')),
      'source_instance':source.get_path_name(),
      'source_parent':path(source_parent),'scalars':{},'vectors':{},
      'static_switches':{},'textures':{}}
    if readback['parent']!=readback['source_parent']:
        raise RuntimeError('Universal prototype parent drifted from Dana source instance')
    for k,wanted in req.get('scalars',{}).items():
        got=float(me.get_material_instance_scalar_parameter_value(instance,k))
        readback['scalars'][k]=got
        if abs(got-float(wanted))>1e-4:raise RuntimeError('Universal scalar readback mismatch: '+k)
    for k,wanted in req.get('vectors',{}).items():
        v=me.get_material_instance_vector_parameter_value(instance,k)
        got=[float(v.r),float(v.g),float(v.b),float(v.a)]
        readback['vectors'][k]=got
        if any(abs(got[i]-float(wanted[i]))>1e-4 for i in range(4)):
            raise RuntimeError('Universal vector readback mismatch: '+k)
    for k,wanted in req.get('static_switches',{}).items():
        got=bool(me.get_material_instance_static_switch_parameter_value(instance,k))
        readback['static_switches'][k]=got
        if got!=bool(wanted):raise RuntimeError('Universal switch readback mismatch: '+k)
    for k in ['BaseColorTile1001','BaseColorTile1002','BaseColorTile1003','NormalMap']:
        try:
            tex=me.get_material_instance_texture_parameter_value(instance,k)
            readback['textures'][k]=tex.get_path_name() if tex else None
        except Exception as exc:readback['textures'][k]='READBACK_ERROR: '+str(exc)
    readback['inherited_static_switches']={}
    for k in ['bFilmUseUDIM','bFilmPrintActive','bTriplanar_Active','bLayerA_Active','bLayerB_Active','bLayerC_Active']:
        try:readback['inherited_static_switches'][k]=bool(me.get_material_instance_static_switch_parameter_value(instance,k))
        except Exception as exc:readback['inherited_static_switches'][k]='READBACK_ERROR: '+str(exc)
    readback['vectors_readback']={}
    for k in ['BaseTint','FilmGradeTint','PaletteRampLow','PaletteRampMid','PaletteRampHigh']:
        try:
            v=me.get_material_instance_vector_parameter_value(instance,k)
            readback['vectors_readback'][k]=[float(v.r),float(v.g),float(v.b),float(v.a)]
        except Exception as exc:readback['vectors_readback'][k]='READBACK_ERROR: '+str(exc)
    return instance,readback

@unreal.AutomationScheduler.add_latent_command
def render_one():
    yield
    OUT.mkdir(parents=True,exist_ok=True)
    req=json.loads(REQUEST.read_text(encoding='utf-8-sig'))
    camera_label=req.get('camera',CAM_DEFAULT)
    width,height=[int(v) for v in req.get('resolution',[W,H])]
    before=[p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
    if before:raise RuntimeError('Dirty maps before load: '+str(before))
    pre_capture_console_commands=req.get('pre_capture_console_commands',[])
    if pre_capture_console_commands:
        startup_world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        for command in pre_capture_console_commands:
            unreal.SystemLibrary.execute_console_command(startup_world,str(command))
    if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP):raise RuntimeError('Could not load map')
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actor=find_actor(SKIN);component=actor.get_component_by_class(unreal.SkeletalMeshComponent)
    camera=find_actor(camera_label);camera_target=None;target_source=None;temporary_camera=None
    original=component.get_material(0)
    sequence_editor=unreal.LevelSequenceEditorBlueprintLibrary
    if not sequence_editor.open_level_sequence(asset(SEQ)):raise RuntimeError('Could not open sequence')
    sequence_editor.set_current_time(20)
    if req.get('temporary_face_camera'):
        guide=find_actor(req.get('guide_camera',CAM_DEFAULT))
        target,target_source=face_target(component,actor)
        right=guide.get_actor_right_vector()
        target.x+=right.x*float(req.get('face_camera_horizontal_offset_cm',5.0))
        target.y+=right.y*float(req.get('face_camera_horizontal_offset_cm',5.0))
        target.z+=float(req.get('face_camera_aim_offset_cm',-5.0))
        guide_location=guide.get_actor_location()
        dx,dy,dz=guide_location.x-target.x,guide_location.y-target.y,guide_location.z-target.z
        length=max(1e-4,math.sqrt(dx*dx+dy*dy+dz*dz))
        distance=float(req.get('face_camera_distance_cm',150.0))
        location=unreal.Vector(target.x+dx*distance/length,target.y+dy*distance/length,
          target.z+dz*distance/length)
        temporary_camera=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
          unreal.CineCameraActor,location,unreal.MathLibrary.find_look_at_rotation(location,target),True)
        if not temporary_camera:raise RuntimeError('Could not spawn temporary face camera')
        temporary_camera.set_actor_label('SESSION_DanaMeeting_FaceRender')
        camera=temporary_camera;camera_label='SESSION_DanaMeeting_FaceRender'
        camera_target={'bone_source':target_source,'world_cm':[round(target.x,3),round(target.y,3),round(target.z,3)],
          'camera_world_cm':[round(location.x,3),round(location.y,3),round(location.z,3)],'distance_cm':distance,
          'guide_camera':req.get('guide_camera',CAM_DEFAULT)}
        cine=camera.get_cine_camera_component()
        cine.set_editor_property('current_focal_length',float(req.get('focal_length_mm',70.0)))
        cine.set_editor_property('filmback',unreal.CameraFilmbackSettings(sensor_width=36.0,sensor_height=20.25))
        focus=cine.get_editor_property('focus_settings')
        focus.set_editor_property('focus_method',unreal.CameraFocusMethod.DISABLE)
        cine.set_editor_property('focus_settings',focus)
        exposure_probe={}
        try:
            post_process=cine.get_editor_property('post_process_settings')
            exposure_bias=float(req.get('temporary_exposure_bias',-1.0))
            post_process.set_editor_property('override_auto_exposure_bias',True)
            post_process.set_editor_property('auto_exposure_bias',exposure_bias)
            cine.set_editor_property('post_process_settings',post_process)
            cine.set_editor_property('post_process_blend_weight',1.0)
            exposure_probe={'override_auto_exposure_bias':True,
              'auto_exposure_bias':exposure_bias,'post_process_blend_weight':1.0}
        except Exception as exc:
            exposure_probe={'error':str(exc)}
        camera_probe={'map':MAP,'sequence':SEQ,'frame':20,'subject':actor.get_actor_label(),
          'actor_location_cm':[round(v,3) for v in actor.get_actor_location().to_tuple()],
          'camera_target':camera_target,'focus_method':str(focus.get_editor_property('focus_method')),
          'temporary_exposure':exposure_probe,
          'focal_length_mm':float(cine.get_editor_property('current_focal_length')),
          'aperture':float(cine.get_editor_property('current_aperture'))}
        bone_rows=[]
        for name in ('Head_M','Neck_M','Eye_L','Eye_R'):
            row={'bone':name}
            for space in (unreal.RelativeTransformSpace.RTS_WORLD,unreal.RelativeTransformSpace.RTS_COMPONENT):
                try:
                    xf=component.get_bone_transform(name,space)
                    row[str(space)]=[round(v,3) for v in xf.translation.to_tuple()]
                except Exception as exc:row[str(space)]='ERROR: '+str(exc)
            bone_rows.append(row)
        camera_probe['bone_transforms']=bone_rows
        center,extent=actor.get_actor_bounds(False)
        camera_probe['bounds']={'origin_cm':[round(v,3) for v in center.to_tuple()],
          'extent_cm':[round(v,3) for v in extent.to_tuple()]}
        CAMERA_PROBE.write_text(json.dumps(camera_probe,indent=2),encoding='utf-8')
    try:camera_focal_length=float(camera.get_cine_camera_component().get_editor_property('current_focal_length'))
    except Exception:camera_focal_length=None
    material_path=req.get('material_path')
    if req.get('kind')=='asset_sdf':
        material,material_readback=face_sdf_instance(req)
        material_label=material.get_path_name()
    elif req.get('kind')=='universal_skin_instance':
        material,material_readback=universal_skin_instance(req)
        material_label=material.get_path_name()
    elif req.get('kind')=='dynamic_sdf':
        parent=asset(req['parent_path'])
        material=component.create_dynamic_material_instance(0,parent,req['stem'])
        if not material:raise RuntimeError('Could not create transient SDF material instance')
        for k,v in req.get('scalars',{}).items():material.set_scalar_parameter_value(k,float(v))
        for k,v in req.get('vectors',{}).items():material.set_vector_parameter_value(
            k,unreal.LinearColor(float(v[0]),float(v[1]),float(v[2]),float(v[3])))
        material.set_texture_parameter_value('PatternSDFMap',texture_asset(req))
        material_label='DMI('+req['parent_path']+' + '+req['texture_path']+')'
        material_readback={}
    else:
        material=asset(material_path)
        scalar_overrides=req.get('scalars',{})
        vector_overrides=req.get('vectors',{})
        if scalar_overrides or vector_overrides:
            material=component.create_dynamic_material_instance(0,material,req['stem']+'_DMI')
            if not material:raise RuntimeError('Could not create transient Dana material instance')
            for k,v in scalar_overrides.items():material.set_scalar_parameter_value(k,float(v))
            for k,v in vector_overrides.items():material.set_vector_parameter_value(
                k,unreal.LinearColor(float(v[0]),float(v[1]),float(v[2]),float(v[3])))
        material_label=req.get('material_path') or material.get_path_name()
        material_readback={}
    component.set_material(0,material)
    material_readback['component_slot0_after_assignment']=component.get_material(0).get_path_name()
    mesh=component.get_skeletal_mesh_asset()
    slot_rows=[]
    mesh_slots=mesh.get_editor_property('materials') if mesh else []
    for index in range(component.get_num_materials()):
        slot_name='UNKNOWN'
        try:slot_name=str(mesh_slots[index].get_editor_property('material_slot_name'))
        except Exception:pass
        slot_material=component.get_material(index)
        slot_rows.append({'index':index,'slot':slot_name,
          'material':slot_material.get_path_name() if slot_material else None})
    out_path=OUT/(req['stem']+'.png')
    if out_path.exists():raise RuntimeError('Refusing overwrite: '+str(out_path))
    report={}
    if REPORT.exists():
        try:report=json.loads(REPORT.read_text(encoding='utf-8-sig'))
        except:report={}
    report.update({'state':'partial_visual_review','map':MAP,'sequence':SEQ,'frame':20,'camera':camera_label,'camera_focal_length_mm':camera_focal_length,
      'pose_and_camera':'Sequence frame 20 supplies the held pose; capture uses an existing camera actor; no map/camera/light/exposure save',
      'resolution_requested':[width,height],'camera_target':camera_target,
      'session_console_commands':pre_capture_console_commands,
      'face_sdf_status':'Dedicated face-shadow SDF input is not implemented. Shadow SDF experiments use PatternSDFMap.',
      'material_readback':material_readback,
      'material_slots_after_assignment':slot_rows,
      'visual_gate':'Capture exists; manual review required. Warm-brown/golden complexion is not accepted until verified in the actual Dana render.',
      'renders':report.get('renders',[])})
    report['renders']=[r for r in report['renders'] if r.get('stem')!=req['stem']]
    REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8')
    try:
        yield
        t0=time.time()
        task=unreal.AutomationLibrary.take_high_res_screenshot(width,height,str(OUT/req['stem']),camera=camera,mask_enabled=False,capture_hdr=False,force_game_view=True)
        if task is None or not task.is_valid_task():raise RuntimeError('Invalid screenshot task')
        while not task.is_task_done():yield
        yield
        dims=png_dims(out_path)
        if not dims:raise RuntimeError('Screenshot task completed without a readable image')
        rec={'label':req['label'],'stem':req['stem'],'material':material_label,'camera':camera_label,
             'camera_focal_length_mm':camera_focal_length,
             'capture_seconds':round(time.time()-t0,2),'exists':True,'requested_resolution':[width,height],
             'path':str(out_path),'bytes':out_path.stat().st_size,'resolution':dims,
             'material_readback':material_readback,'material_slots_after_assignment':slot_rows,
             'temporary_overrides':{'scalars':req.get('scalars',{}),'vectors':req.get('vectors',{})}}
        report['renders'].append(rec)
        report['last_completed']=req['stem']
        report['state']='partial_visual_review'
        REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8')
        unreal.log('DANA_MEETING_RENDER '+json.dumps(rec))
    except Exception as exc:
        report['state']='failed';report['error']=str(exc);report['traceback']=traceback.format_exc()
        REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8');raise
    finally:
        component.set_material(0,original)
        if temporary_camera:
            try:unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(temporary_camera)
            except Exception:pass
        try:sequence_editor.close_level_sequence()
        except:pass
        report['dirty_maps_after_restore']=[p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
        REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8')
