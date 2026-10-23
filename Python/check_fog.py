"""Deprecated: use Python/audit_fog_drift.py.

The original version of this script read the `volumetric_fog` property, which resolves
to the FVolumetricFog struct, while every writer in the project set `enable_volumetric_fog`.
It therefore never reported the flag that actually governs volumetric fog, which is
precisely the value this audit exists to verify.

audit_fog_drift.py reads the full reviewed property set, checks fog ownership
(single actor + UDS custom-fog hook bound + sky internal fog hidden), and exits
non-zero when ownership is broken.
"""
import sys

print(__doc__)
print("Run instead:  python Python/audit_fog_drift.py")
print("or in-editor: exec(open(r'<project>/Python/audit_fog_drift.py').read())")
sys.exit(2)