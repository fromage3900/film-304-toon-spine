"""Read-only DoF + cinematic polish probe for tonight's hero renders.
No saves, no mutations. Writes Saved/Audit/HeroLock20261018/dof_polish.json."""
import json, os
import unreal

OUT = r"G:\film-304-toon-spine\Saved\Audit\HeroLock20261018\dof_polish.json"
LABELS = ["HERO01_Wide_Establishing", "HERO02_Medium_TwoShot",
          "HERO03_Close_Portrait", "HERO04_Macro_Insert"]

def all_actors():
    try:
        return unreal.EditorLevelLibrary.get_all_level_actors()
    except Exception:
        return []

actors = all_actors()
by_label = {}
for a in actors:
    try:
        by_label[a.get_actor_label()] = a
    except Exception:
        pass

def snap(v):
    try:
        return [round(float(v.x), 2), round(float(v.y), 2), round(float(v.z), 2)]
    except Exception:
        return str(v)[:120]

def snap_rot(r):
    try:
        return [round(float(r.pitch), 3), round(float(r.yaw), 3), round(float(r.roll), 3)]
    except Exception:
        return str(r)[:120]

cams = []
for lab in LABELS:
    a = by_label.get(lab)
    if a is None:
        cams.append({"label": lab, "found": False})
        continue
    cc = None
    try:
        cc = a.get_cine_camera_component()
    except Exception as e:
        cams.append({"label": lab, "found": True, "error": "no cine comp: %s" % str(e)[:200]})
        continue
    rec = {"label": lab, "found": True, "class": a.get_class().get_name()}
    try:
        rec["loc"] = snap(a.get_actor_location())
        rec["rotation"] = snap_rot(a.get_actor_rotation())
    except Exception:
        pass
    # focal / aperture
    for attr in ("current_focal_length", "current_aperture", "current_focus_distance"):
        try:
            rec[attr] = round(float(getattr(cc, attr)), 3)
        except Exception as e:
            rec[attr] = "ERR %s" % str(e)[:120]
    # focus_settings struct dump
    try:
        fs = cc.focus_settings
        rec["focus_settings"] = {}
        for f in ("focus_method", "manual_focus_distance", "focus_offset",
                  "b_draw_debug_focus_plane", "debug_focus_plane_color",
                  "b_smooth_focus_changes", "focus_smoothing_interp_speed",
                  "focus_offset_x", "focus_offset_y"):
            try:
                v = getattr(fs, f)
                rec["focus_settings"][f] = str(v)[:160]
            except Exception:
                pass
    except Exception as e:
        rec["focus_settings_error"] = str(e)[:200]
    # filmback
    try:
        fb = cc.filmback
        rec["filmback"] = {}
        for f in ("sensor_width", "sensor_height", "sensor_aspect_ratio",
                  "sensor_fit", "filmback_preset_name"):
            try:
                rec["filmback"][f] = str(getattr(fb, f))[:120]
            except Exception:
                pass
    except Exception as e:
        rec["filmback_error"] = str(e)[:200]
    # lens
    try:
        rec["lens_settings"] = str(cc.lens_settings)[:300]
    except Exception as e:
        rec["lens_error"] = str(e)[:200]
    cams.append(rec)

# PPV probe
ppv_rec = {"label": "PPV_ToonOutlineClean", "found": False}
ppa = by_label.get("PPV_ToonOutlineClean")
if ppa is not None:
    ppv_rec["found"] = True
    try:
        comp = ppa.get_component_by_class(unreal.PostProcessComponent)
        s = comp.settings if comp is not None else None
        keys = [k for k in dir(s) if any(t in k.lower() for t in
                ("depth", "dof", "focal", "fstop", "bloom", "vignette",
                 "grain", "exposure", "chromatic", "lens", "flair", "flare",
                 "tonemap", "color_grading", "filmgrain"))]
        ppv_rec["keys"] = keys
        ppv_rec["values"] = {}
        for k in keys:
            try:
                ppv_rec["values"][k] = str(getattr(s, k))[:200]
            except Exception:
                pass
    except Exception as e:
        ppv_rec["error"] = str(e)[:300]

out = {"read_only": True, "saved_anything": False,
       "current_world": str(unreal.EditorLevelLibrary.get_editor_world().get_name()),
       "cameras": cams, "ppv": ppv_rec}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as fh:
    json.dump(out, fh, indent=2)
print(json.dumps(out, indent=2))
