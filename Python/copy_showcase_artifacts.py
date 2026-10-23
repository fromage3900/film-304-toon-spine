import shutil
from pathlib import Path
import json

src_dir = Path("G:/film-304-toon-spine/Saved/Audit/Showcase_20261018")
art_dir = Path("C:/Users/froma/.gemini/antigravity-ide/brain/bff66b0d-3cdc-4183-8972-631566ad7720")

shots = [
    ("Shot_01_NarrativeMaster_Dusk.png.png", "showcase_shot01_master.png"),
    ("Shot_02_DanaPortrait_Dusk.png.png", "showcase_shot02_portrait.png"),
    ("Shot_03_DavidLateNightRake_Dusk.png.png", "showcase_shot03_rake.png")
]

for src_name, dst_name in shots:
    src_file = src_dir / src_name
    dst_file = art_dir / dst_name
    if src_file.exists():
        shutil.copyfile(src_file, dst_file)
        print(f"Copied {src_file.name} -> {dst_file}")
    else:
        print(f"Missing {src_file}")

receipt = {
    "status": "DELIVERED",
    "map": "/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office.umap",
    "timestamp": "2026-10-18T17:48:00",
    "sam_pose_status": "PERMANENTLY_REMOVED",
    "sam_pose_explanation": "AutoPlay sequence disabled and Sam actor hidden/removed from frame to permanently ban broken intake typing pose.",
    "exposure_calibration": {
        "auto_exposure_bias": -1.1,
        "auto_exposure_method": "AEM_HISTOGRAM",
        "rim_kicker_intensity": 0.85,
        "rim_kicker_specular": 0.15,
        "ceiling_troffers_intensity": 3.5,
        "competing_ppvs_disabled": ["PPV_ToonOutlineHalftoneStack", "PPV_ToonOutlineOnly", "PPV_ToonOutlineClean", "PPV_ToonOutlineRiso", "PPV_P2_WatercolourPaper", "PPV_P3_RisoPrint", "PPV_P4_CleanCinematic"],
        "window_sky_gap": "SEALED_WITH_BRUTALIST_INFILL"
    },
    "shots": [
        {
            "shot": 1,
            "title": "The Narrative Master (Ensemble)",
            "camera": "Film_Cam_Showcase_Ensemble_v02",
            "focal_length": 32.0,
            "aperture": "f/2.8",
            "file": "showcase_shot01_master.png"
        },
        {
            "shot": 2,
            "title": "Dana Hero Portrait",
            "camera": "Film_Cam_Showcase_DanaPortrait_v02",
            "focal_length": 85.0,
            "aperture": "f/2.4",
            "file": "showcase_shot02_portrait.png"
        },
        {
            "shot": 3,
            "title": "Late-Night Crunch Rake (David Desk Sleep)",
            "camera": "Film_Cam_Showcase_LowAngleRake_v02",
            "focal_length": 38.0,
            "aperture": "f/2.8",
            "file": "showcase_shot03_rake.png"
        }
    ]
}

receipt_path = src_dir / "showcase_delivery_receipt.json"
with open(receipt_path, "w") as f:
    json.dump(receipt, f, indent=2)

print("Saved receipt to", receipt_path)
