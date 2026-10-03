"""Build the toon texture library from code - PNGs generated, never hand-made.

WHY GENERATED (CONTENT_CONVENTIONS: assets are generated from code)
    The film repo ships zero T_* textures. Melodia's Content/Stylization holds
    the proven set (T_Dither_Bayer, T_Hatch_Cross, T_Hatch_Diagonal,
    T_Ramp_2Band/3Band/4Band/Smooth, T_Noise_White) but copying .uasset files
    between projects is the documented failure - a copied asset keeps its old
    package path and can silently drop its content (AUDIT_2026-09-30 findings,
    spine_lib.py header). So the VALUES are ported and the pixels are
    regenerated here from pure stdlib (zlib/struct), and this builder is the
    source of truth.

    No PIL and no numpy in this Python - hence the inline PNG writer.

WHAT THESE ARE FOR
    T_Dither_Bayer        ordered dither - exact 16-level Bayer, needs nearest
                          filtering and NO BC compression (it would corrupt it)
    T_Hatch_Cross         cross-hatch ink for ToonProfile
                          ShadowHatchingPatternTexture
    T_Hatch_Diagonal      single-direction hatch
    T_HatchPattern        the canonical name referenced by BOTH
                          specs/humber_toon_spine/humber_toon_spine_manifest
                          .v1.json (shading_pipeline.hatching_pattern) and
                          Melodia's specs/toon_profiles/tp_melusina.json.
                          Dangling in both repos - this creates it.
    T_Ramp_*              luminance -> colour LUTs for MF_RampLUT
                          (coloured shadow, never neutral: the manifest's
                          canonical #352D40 warm-violet shadow)
    T_Noise_White         band-breakup noise for DiffuseRampOffsetTexture

SETTINGS THAT MATTER (applied defensively and READ BACK into the report -
enum member names move between engine versions, so nothing is assumed to have
worked):
    dither/hatch  sRGB off (data), nearest/bilinear, no mips, lossless
    ramps         sRGB on (colour), TA_Clamp so lum=0 and lum=1 hit the ends
                  exactly instead of wrapping
    masks         TA_Wrap - they tile across a surface

Output: Content/Materials/Textures/*.uasset  (PNGs under Saved/, gitignored)
Verify: Saved/Audit/texture_build_report.json - assert on the FILE.
"""
from __future__ import annotations

import binascii
import json
import random
import struct
import sys
import zlib
from pathlib import Path

import unreal

# Report + PNG staging live in Saved/, not next to the source. This is not
# cosmetic: .gitignore only re-includes Saved/Audit/*.{json,md,txt}, so a report
# written into Python/ would land in the source tree as an untracked file on
# every regeneration - exactly the "generated output committed by accident" trap
# CONTENT_CONVENTIONS.md warns about.
OUT = (Path(__file__).resolve().parents[1] / "Saved" / "Audit"
       / "texture_build_report.json")
TEX_DIR = "/Game/Materials/Textures"
PNG_DIR = Path(__file__).resolve().parents[1] / "Saved" / "GeneratedTextures"

# The manifest's canonical shadow: warm violet, carries colour, never black.
SHADOW = (53, 45, 64)      # #352D40
LIGHT = (255, 255, 255)
MID = (140, 128, 160)


# ---------------------------------------------------------------------------
# PNG writer - 8-bit RGB (colour type 2), no third-party dependency
# ---------------------------------------------------------------------------

def write_png(path: Path, width: int, height: int, rows) -> None:
    """rows: iterable of bytes, each exactly width*3 long."""
    raw = b"".join(b"\x00" + bytes(r) for r in rows)  # filter byte 0 per scanline

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


# ---------------------------------------------------------------------------
# Pattern generators - each returns (width, height, rows)
# ---------------------------------------------------------------------------

# Standard 4x4 ordered-dither threshold matrix (Bayer). Values 0..15.
BAYER4 = [[0, 8, 2, 10],
          [12, 4, 14, 6],
          [3, 11, 1, 9],
          [15, 7, 13, 5]]


def gen_dither(size: int = 64):
    """Bayer 4x4 tiled to size. Greyscale as RGB, 16 exact levels."""
    rows = []
    for y in range(size):
        row = bytearray()
        for x in range(size):
            v = int(round((BAYER4[y % 4][x % 4] + 0.5) / 16.0 * 255.0))
            row += bytes((v, v, v))
        rows.append(bytes(row))
    return size, size, rows


def gen_hatch(size: int = 128, spacing: int = 16, width_px: int = 3,
              cross: bool = True):
    """Diagonal hatch. White = ink line, black = clear.

    cross=True adds the 135-degree family (engraving / pencil hatch). Lines are
    drawn hard - a cel look wants a step, not an antialiased gradient, which is
    the same reasoning SDF_PATTERN_PIPELINE.md gives for thresholding fields.
    """
    rows = []
    for y in range(size):
        row = bytearray()
        for x in range(size):
            on = (x + y) % spacing < width_px
            if cross:
                on = on or ((x - y) % spacing) < width_px  # python % >= 0
            row += bytes((255, 255, 255)) if on else bytes((0, 0, 0))
        rows.append(bytes(row))
    return size, size, rows


def _lut_colour(t, stops):
    """Piecewise colour along 0..1 against [(pos, (r,g,b)), ...]."""
    if t <= stops[0][0]:
        return stops[0][1]
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        if t <= p1:
            f = 0.0 if p1 == p0 else (t - p0) / (p1 - p0)
            return tuple(int(round(c0[i] + (c1[i] - c0[i]) * f)) for i in range(3))
    return stops[-1][1]


def _snap(t, stops):
    """Quantise t onto plateau centres - flat bands for a hard cel ramp."""
    edges = [p for p, _ in stops]
    best = edges[0]
    for p in edges:
        if t >= p:
            best = p
    idx = edges.index(best)
    if idx + 1 < len(edges):
        return best + (edges[idx + 1] - best) * 0.4
    return best


def gen_ramp(stops, width: int = 256, height: int = 8, hard: bool = False):
    """Horizontal luminance->colour strip. Rows identical (sampled at y=0.5).

    hard=True snaps each segment to a flat plateau with a short transition -
    a band ramp. hard=False is the smooth gradient.
    """
    rows = []
    for _ in range(height):
        row = bytearray()
        for x in range(width):
            t = x / (width - 1)
            if hard:
                t = _snap(t, stops)
            r, g, b = _lut_colour(t, stops)
            row += bytes((r, g, b))
        rows.append(bytes(row))
    return width, height, rows


def gen_noise(size: int = 64, seed: int = 1337):
    """Deterministic white noise - identical pixels on every machine and run."""
    rng = random.Random(seed)
    rows = []
    for _ in range(size):
        row = bytearray()
        for _ in range(size):
            v = rng.randint(0, 255)
            row += bytes((v, v, v))
        rows.append(bytes(row))
    return size, size, rows


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------

# (name, generator, sRGB, filter, address, compression, mips, why)
# sRGB off for masks (they are data, not colour), on for colour ramps.
# Compression must be LOSSLESS for the dither: BC averages 4x4 blocks, which
# would destroy the 16 exact Bayer levels.
CATALOG = [
    ("T_Dither_Bayer", lambda: gen_dither(64), False, "nearest", "wrap",
     "maskless", False,
     "Ordered dither. Needs exact levels + nearest + no mips, or it is garbage."),
    ("T_Hatch_Cross", lambda: gen_hatch(128, cross=True), False, "bilinear",
     "wrap", "maskless", False,
     "Cross-hatch ink for ToonProfile.ShadowHatchingPatternTexture."),
    ("T_Hatch_Diagonal", lambda: gen_hatch(128, cross=False), False, "bilinear",
     "wrap", "maskless", False,
     "Single-direction hatch - lighter than cross for mid-tone shadow."),
    ("T_HatchPattern", lambda: gen_hatch(128, cross=True), False, "bilinear",
     "wrap", "maskless", False,
     "Canonical name referenced by humber_toon_spine_manifest.v1.json "
     "(shading_pipeline.hatching_pattern) and Melodia tp_melusina.json - "
     "dangling in both repos until now."),
    ("T_Ramp_2Band", lambda: gen_ramp(_BAND2, hard=True), True, "bilinear",
     "clamp", "maskless", False,
     "Hard two-tone: violet shadow -> light. For bUsePaintedRamp."),
    ("T_Ramp_3Band", lambda: gen_ramp(_BAND3, hard=True), True, "bilinear",
     "clamp", "maskless", False,
     "Three plateau cel ramp - the stock UE cel shape."),
    ("T_Ramp_4Band", lambda: gen_ramp(_BAND4, hard=True), True, "bilinear",
     "clamp", "maskless", False,
     "Four plateau ramp for richer architecture falloff."),
    ("T_Ramp_Smooth", lambda: gen_ramp(_BAND3, hard=False), True, "bilinear",
     "clamp", "maskless", False,
     "No terminator at all - soft gradient for background/airbrushed depth."),
    ("T_Noise_White", lambda: gen_noise(64), False, "bilinear", "wrap",
     "maskless", True,
     "Band-breakup noise for ToonProfile.DiffuseRampOffsetTexture."),
]

# Coloured-shadow stops. #352D40 warm violet is the manifest's canonical
# shadow (spec/toon_profiles/tp_melusina.json: shadow carries colour).
_BAND2 = [(0.0, SHADOW), (0.5, SHADOW), (0.5, LIGHT), (1.0, LIGHT)]
_BAND3 = [(0.0, SHADOW), (0.30, SHADOW), (0.30, MID),
          (0.70, MID), (0.70, LIGHT), (1.0, LIGHT)]
_BAND4 = [(0.0, SHADOW), (0.25, SHADOW), (0.25, MID),
          (0.50, MID), (0.50, (190, 182, 205)), (0.75, (190, 182, 205)),
          (0.75, LIGHT), (1.0, LIGHT)]


# ---------------------------------------------------------------------------
# Defensive enum resolution - member names move between engine builds, so
# candidates are tried and the one that resolved is RECORDED, not assumed.
# ---------------------------------------------------------------------------

def _pick(candidates, members, upper=True):
    """First candidate present in `members`, trying case variants."""
    for cand in candidates:
        for variant in ({cand, cand.upper(), cand.title()} if upper else {cand}):
            if variant in members:
                return variant
    return None


RESOLVED = {}


def _resolve_all():
    """Resolve each setting enum by direct member probing, and record the result.

    REGRESSION NOTE 2026-10-02: a previous version located the enum CLASS by
    scanning dir(unreal) with a regex and reading cls.__members__. On this build
    that returned empty for all seven, so every setting was silently SKIPPED
    ("unresolved") while the build still reported ok=true - the textures loaded
    at engine defaults. A read-back from the live editor is what caught it
    (filter=TF_DEFAULT when nearest was requested). Enum member names are
    probed directly instead, because that is what actually works here.
    """
    specs = {
        "filter_nearest": ("TextureFilter", ["TF_NEAREST", "TF_Nearest"]),
        "filter_bilinear": ("TextureFilter", ["TF_BILINEAR", "TF_Bilinear"]),
        "addr_wrap": ("TextureAddress", ["TA_WRAP", "TA_Wrap"]),
        "addr_clamp": ("TextureAddress", ["TA_CLAMP", "TA_Clamp"]),
        # TC_VECTOR_DISPLACEMENTMAP is the uncompressed format, and it is the
        # one that MATTERS here: TC_DEFAULT is block compression, which
        # averages 4x4 blocks and would destroy the exact 16-level Bayer
        # matrix T_Dither_Bayer depends on. The name was measured on this build
        # (Saved/Audit/texture_enum_probe.json) after two wrong guesses -
        # TC_Maskless and TC_VectorDisplacementmap do not exist.
        "comp_lossless": ("TextureCompressionSettings",
                          ["TC_VECTOR_DISPLACEMENTMAP", "TC_GRAYSCALE",
                           "TC_DEFAULT"]),
        "mips_off": ("TextureMipGenSettings",
                     ["TMGS_NO_MIPMAPS", "TMGS_NOMIPMAPS", "MOS_NO_MIPMAPS"]),
        "mips_on": ("TextureMipGenSettings",
                    ["TMGS_BILINEAR", "TMGS_SIMPLE_AVERAGE", "MOS_BILINEAR"]),
    }
    for key, (class_name, members) in specs.items():
        enum_cls = getattr(unreal, class_name, None)
        found, value = None, None
        if enum_cls is not None:
            for cand in members:
                if hasattr(enum_cls, cand):
                    found, value = cand, getattr(enum_cls, cand)
                    break
        RESOLVED[key] = {
            "value": value,
            "enum": class_name if enum_cls is not None else None,
            "member": found,
            "available": members,
        }
    return RESOLVED


def _set(tex, prop, value, rep, key):
    """Set one texture property, recording success/failure. Never raises."""
    if value is None:
        rep["skipped"].append(f"{key}: unresolved")
        return
    try:
        tex.set_editor_property(prop, value)
        rep["set"].append(f"{key}={getattr(value, 'name', value)}")
    except Exception as exc:
        rep["failed"].append(f"{key}: {str(exc)[:120]}")


def _readback(tex, props, rep):
    """Read properties back - mtime-style proof the write landed."""
    got = {}
    for prop in props:
        try:
            v = tex.get_editor_property(prop)
            got[prop] = str(getattr(v, "name", v))
        except Exception as exc:
            got[prop] = f"<{str(exc)[:60]}>"
    rep["readback"] = got


def _import_png(name: str, png: Path) -> unreal.Texture2D:
    """Import one PNG into TEX_DIR, replacing any previous copy."""
    task = unreal.AssetImportTask()
    task.filename = str(png)
    task.destination_path = TEX_DIR
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True
    # NOT set: automated_import_should_be_imported - that attribute does not
    # exist on this build (measured 2026-10-02: raising it failed every import).
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return unreal.load_asset(f"{TEX_DIR}/{name}.{name}")


def build() -> dict:
    """Generate every PNG, import it, apply and READ BACK its settings."""
    lib_log = print
    report = {"textures": {}, "errors": [], "resolved_enums": {}}
    resolved = _resolve_all()
    report["resolved_enums"] = {
        k: {"enum": v["enum"], "member": v["member"]}
        for k, v in resolved.items()}

    # HARD GATE, added 2026-10-02. Previously an unresolvable enum was skipped
    # into entry["skipped"] and the build still reported ok=true - so a texture
    # library where NOTHING was configured shipped green and was only caught by
    # reading the live editor back. An unresolved setting is now a build failure.
    unresolved = [k for k, v in resolved.items() if v["value"] is None]
    if unresolved:
        report["errors"].append(
            "unresolved texture settings enums: " + ", ".join(unresolved))

    if not unreal.EditorAssetLibrary.does_directory_exist(TEX_DIR):
        unreal.EditorAssetLibrary.make_directory(TEX_DIR)

    PNG_DIR.mkdir(parents=True, exist_ok=True)

    for (name, gen, srgb, filt, addr, comp, mips, why) in CATALOG:
        entry = {
            "why": why, "set": [], "failed": [], "skipped": [],
            "ok": False,
        }
        try:
            w, h, rows = gen()
            png = PNG_DIR / f"{name}.png"
            write_png(png, w, h, rows)
            entry["png"] = str(png)
            entry["pixels"] = f"{w}x{h}"

            tex = _import_png(name, png)
            if tex is None:
                entry["failed"].append("import returned None")
                report["textures"][name] = entry
                report["errors"].append(f"{name}: import failed")
                continue

            # --- settings, each recorded rather than assumed ---
            _set(tex, "srgb", bool(srgb), entry, "srgb")
            fkey = "filter_nearest" if filt == "nearest" else "filter_bilinear"
            _set(tex, "filter", resolved[fkey]["value"], entry, f"filter({filt})")
            akey = "addr_clamp" if addr == "clamp" else "addr_wrap"
            _set(tex, "address_x", resolved[akey]["value"], entry, "address_x")
            _set(tex, "address_y", resolved[akey]["value"], entry, "address_y")
            _set(tex, "compression_settings",
                 resolved["comp_lossless"]["value"], entry, "compression")
            mkey = "mips_on" if mips else "mips_off"
            _set(tex, "mip_gen_settings", resolved[mkey]["value"], entry,
                 f"mip_gen({mkey})")

            _readback(tex, ("srgb", "filter", "address_x", "address_y",
                            "compression_settings", "mip_gen_settings"), entry)

            # Proof the asset is real: dimensions, not just "no exception".
            try:
                entry["size"] = f"{tex.blueprint_get_size_x()}x{tex.blueprint_get_size_y()}"
            except Exception:
                try:
                    entry["size"] = f"{tex.get_editor_property('sizeX')}x" \
                                    f"{tex.get_editor_property('sizeY')}"
                except Exception as exc:
                    entry["size"] = f"<{str(exc)[:60]}>"

            unreal.EditorAssetLibrary.save_loaded_asset(tex, only_if_is_dirty=False)
            entry["asset"] = f"{TEX_DIR}/{name}.{name}"
            entry["ok"] = not entry["failed"]
            lib_log(f"[TEX] {name} ok={entry['ok']} size={entry['size']}")
        except Exception as exc:
            entry["failed"].append(str(exc)[:300])
            report["errors"].append(f"{name}: {exc}")
        report["textures"][name] = entry

    report["ok"] = not report["errors"] and all(
        e["ok"] for e in report["textures"].values())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lib_log(f"[TEX] wrote {OUT} ok={report['ok']} "
            f"count={len(report['textures'])}")
    return report


def main() -> int:
    rep = build()
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
