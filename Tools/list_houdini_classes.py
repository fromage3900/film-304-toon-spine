import unreal

hou_classes = [attr for attr in dir(unreal) if "Houdini" in attr]
unreal.log(f"[HoudiniClasses] Count: {len(hou_classes)}")
unreal.log(f"[HoudiniClasses] Sample: {hou_classes[:25]}")
