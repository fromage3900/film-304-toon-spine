        try:
            bpy.ops.object.modifier_apply(modifier=mod.name, keep_shapekeys=False)
        except Exception:
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception:
                pass
        outline_objects.append(dup)