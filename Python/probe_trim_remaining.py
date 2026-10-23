# Probe: where do the surviving Melodia parameters actually live?
import unreal

MAT = "/Game/Materials/Masters/Film/M_Film_Toon_Universal_Trimmed"
lib = unreal.MaterialEditingLibrary
mat = unreal.load_asset(MAT)


def log(m):
    unreal.log("[TrimProbe] " + str(m))


for n in ["MadokaGlowAmount", "SparkleScale", "IttoInkStrength"]:
    try:
        log("scalar %s -> %s" % (n, str(lib.get_scalar_parameter_source(mat, n))[:160]))
    except Exception as e:                                   # noqa: BLE001
        log("scalar %s ERR %s" % (n, e))

for n in ["MadokaRampLow", "SparkleColor"]:
    try:
        log("vector %s -> %s" % (n, str(lib.get_vector_parameter_source(mat, n))[:160]))
    except Exception as e:                                   # noqa: BLE001
        log("vector %s ERR %s" % (n, e))

# is the parameter coming from a material function instance?
try:
    fns = lib.get_material_functions_referencing(mat)
    log("functions referencing material: %s" % [str(f) for f in fns][:8])
except Exception as e:                                       # noqa: BLE001
    log("functions probe ERR %s" % e)

# does the material own expressions whose parameter_name matches, if we compare
# case/whitespace-insensitively? (rules out a spelling mismatch)
found = {}
for e in lib.get_material_expressions(mat):
    try:
        nm = str(e.get_editor_property("parameter_name") or "")
    except Exception:                                        # noqa: BLE001
        continue
    if any(k in nm for k in ("Madoka", "Itto", "Sparkle", "WitchBarrier")):
        found[nm] = e.get_class().get_name()
log("expressions in material graph matching: %s" % found)
