import unreal

try:
    # Check Houdini Engine Subsystem or runtime
    hes = unreal.get_editor_subsystem(unreal.HoudiniPublicAPI)
    unreal.log(f"[HoudiniCheck] HoudiniPublicAPI found: {hes}")
except Exception as e:
    unreal.log(f"[HoudiniCheck] Exception querying public API: {e}")

try:
    # Check HoudiniEngine module
    loaded = unreal.ModuleManager.get().is_module_loaded("HoudiniEngine")
    unreal.log(f"[HoudiniCheck] HoudiniEngine module loaded: {loaded}")
    loaded_ed = unreal.ModuleManager.get().is_module_loaded("HoudiniEngineEditor")
    unreal.log(f"[HoudiniCheck] HoudiniEngineEditor module loaded: {loaded_ed}")
except Exception as e:
    unreal.log(f"[HoudiniCheck] Exception checking module: {e}")
