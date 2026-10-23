"""Read-only full PPV settings dump (DoF-relevant). No saves."""
import json, os, unreal
OUT = r"G:\film-304-toon-spine\Saved\Audit\HeroLock20261018\dof_ppv_full.json"
def find(label):
    subs = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in subs.get_all_level_actors():
        try:
            if a.get_actor_label() == label:
                return a
        except Exception:
            pass
    return None
ppa = find("PPV_ToonOutlineClean")
rec = {"found": ppa is not None}
if ppa is not None:
    rec["actor_class"] = ppa.get_class().get_name()
    names = [n for n in dir(ppa) if not n.startswith("_")]
    dof_names = [n for n in names if any(t in n.lower() for t in
        ("dof", "depth", "focal", "fstop", "aperture", "bloom", "vignette",
         "grain", "exposure", "chromatic", "tonemap", "lens", "flare",
         "flair", "ambient_occlusion", "settings"))]
    rec["candidate_names"] = dof_names
    rec["values"] = {}
    for n in dof_names:
        try:
            v = getattr(ppa, n)
            rec["values"][n] = str(v)[:300]
        except Exception as e:
            rec["values"][n] = "ERR " + str(e)[:150]
    # also dump .settings if present
    try:
        s = ppa.settings
        rec["has_settings_attr"] = True
        snames = [n for n in dir(s)]
        rec["n_settings"] = len(snames)
        rec["dof_settings"] = {n: str(getattr(s, n))[:300] for n in snames
            if any(t in n.lower() for t in ("dof", "depth", "focal", "fstop",
               "aperture", "bloom", "vignette", "grain", "exposure",
               "chromatic", "tonemap", "lens", "flare", "flair"))}
    except Exception as e:
        rec["has_settings_attr"] = False
        rec["settings_error"] = str(e)[:200]
with open(OUT, "w") as fh:
    json.dump(rec, fh, indent=2)
print(json.dumps(rec, indent=2)[:6000])
print("KEYS:", len(rec.get("all_setting_names", [])))
