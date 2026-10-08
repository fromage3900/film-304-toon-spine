# Laptop driver fix — the black-render repair path — 2026-10-08

> **2026-10-08 PM UPDATE:** the desktop control render DISPROVED the
> machine-only theory — the same black Substrate renders reproduce on the
> RTX 3080 Ti / driver 610.88 under the MRQ `-game` path. See
> `Docs/SESSION_2026-10-08_DESKTOP_BLACK_RENDER_HUNT.md` for the afternoon
> session's findings (headless render harness landed; office stage lighting
> rig FIXED; master-instance direct-light check is the open thread). The
> driver upgrade below is still worth doing for laptop-side lookdev, but it
> is NOT the black-render cure.

**Read alongside:** `Docs/TOON_SPINE.md` (2026-10-08 render-path state),
`Saved/Audit/render_test_20261008.json` (the black stills + light bisect),
`Saved/Audit/controls_verdict_20261008.json` (the A/B/C control verdict,
fired on the desktop the same day).

## The defect, in one paragraph

On the laptop (GTX 1050 Ti, NVIDIA driver **527.56**), the Substrate toon
masters compile and execute but render **BLACK** — geometry silhouettes with
no light response, unaffected by re-aiming/strengthening the key (sun int 6,
skylight 2.0 + recapture; see the BISECT still in the audit). Non-Substrate
content (sky/atmosphere/engine-grid ground) lights correctly on the same
machine, and the SAME harness produced real reads on the desktop
(`COMP_SH020/SH030_proto_v01.png`, 2026-10-05). The laptop driver is from the
SM5-era 527 branch — nearly four years old by 2026 — and NVIDIA has since
ENDED Pascal Game Ready support entirely.

## The fix (in priority order)

1. **Upgrade the laptop driver to the newest release that still lists the
   GTX 1050 Ti.** Pascal (GTX 10-series) support ended with the **R580
   branch** — the 590+ branches drop Pascal; security-only updates for
   Pascal continue through October 2028 on the legacy branch. So:
   - Uninstall/overlay 527.56 with the latest **580.xx** driver (or any
     newer legacy-branch release that still lists the 1050 Ti).
   - Source: NVIDIA's driver page → Legacy/GeForce 10-Series → GTX 1050 Ti
     (pick Windows 11 64-bit, the newest version offered).
   - Reboot after install.
2. **Re-fire the acceptance control on the laptop** (same test the desktop
   ran — no code changes needed):

   ```powershell
   & "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" `
     "HumberToonShader.uproject" `
     -ExecutePythonScript="Python/render_headless_driver.py" `
     -nosplash -unattended -stdout
   ```

   with `Saved/Renders/_headless_request.json` set to `{"mode": "controls"}`.
   The verdict JSON (`Saved/Audit/controls_verdict_<date>.json`) must read
   `TOON_PATH_HEALTHY` — red reads on all three control cubes (plain lit,
   Substrate Toon without profile, Substrate Toon with TP_Default).

3. **Then re-fire one exterior still** (`Saved/Renders/_request_exterior.json`,
   SH010) and confirm the buildings/ground are no longer black
   (`COMP_SH010_proto_v02.png`).

## If the upgraded driver still renders black

Then the machine theory is exhausted: record the control verdict from the
laptop beside the desktop's, and the black is an in-repo defect for BOTH
machines — the Toon BSDF/profile pipeline itself. That outcome would be a
material-core bug to bisect with the same control matrix (control C bound
profile data is the suspect class), not an environment issue. Do NOT ship
stills from a machine that fails the control matrix; the desktop path is
the presentation source for tomorrow regardless.

## Presentation guidance for tomorrow (2026-10-09)

- Render the shot stills on the **desktop** (this machine) — the control
  verdict gates the batch; see `Saved/Audit/render_batch_desktop_20261008.json`.
- The laptop is fine for **editing/builder work**; only the Substrate lookdev
  render path is driver-blocked there.
