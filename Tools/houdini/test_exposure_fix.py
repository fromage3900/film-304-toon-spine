import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.EditorLevelLibrary.get_editor_world()

# Temporarily delete or hide Light_Ceiling_Upwash_01..03
for lbl in ["Light_Ceiling_Upwash_01", "Light_Ceiling_Upwash_02", "Light_Ceiling_Upwash_03"]:
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == lbl:
            eas.destroy_actor(a)
            print(f"Destroyed {lbl}")

# Also hide SpotLight if intensity > 0
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SpotLight":
        c = a.get_component_by_class(unreal.LightComponentBase)
        if c: c.set_intensity(0.0)
        print("Zeroed SpotLight")

# Now capture test frame from SESSION_CAM_Cast
cam_actor = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SESSION_CAM_Cast":
        cam_actor = a
        break

rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, format=unreal.TextureRenderTargetFormat.RTF_RGBA8)
cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_actor.get_actor_location(), cam_actor.get_actor_rotation())
comp = cap.get_component_by_class(unreal.SceneCaptureComponent2D)
comp.texture_target = rt
comp.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR

# Bind to PPV_P4_CleanCinematic settings
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "PPV_P4_CleanCinematic":
        ppc = a.get_component_by_class(unreal.PostProcessComponent)
        if ppc:
            comp.post_process_settings = ppc.settings
            print("Bound to PPV_P4_CleanCinematic settings")
        break

comp.capture_scene()
out_dir = "C:/Users/froma/.gemini/antigravity-ide/brain/10d93b13-68af-4057-ae2d-343574ed43dd"
unreal.RenderingLibrary.export_render_target(world, rt, out_dir, "test_exposure_fix.png")
eas.destroy_actor(cap)
print("Rendered test_exposure_fix.png!")
