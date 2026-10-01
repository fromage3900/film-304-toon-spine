# verify_all.ps1 - the project gate. ONE command, ONE exit code.
#
#     powershell -File Tools/verify_all.ps1
#
# Exit 0 = everything below passed. Non-zero = something is wrong; the report
# names which check failed and prints the evidence.
#
# WHY ONE ENTRY POINT: every check here corresponds to a defect found the hard
# way on 2026-09-30, and each was invisible to the others:
#
#   * a self-link made a whole node group evaluate to 0 verts while the build
#     reported success and `link_failures` stayed empty -> Blender verifier
#   * the vendored brutalist copy was 226 lines stale, so probes measured code
#     that was not the code under review                 -> fork sync check
#   * the lookdev level's actors live in World Partition external packages; while
#     those were gitignored a teammate's clone opened an empty level
#                                                        -> .umap externals check
#   * a level was saved to a package named after its own folder and committed as
#     Content/Maps.umap                                  -> package name scan
#   * the README pointed at a builder that cannot import -> doc path check
#
# A report is written to Saved/Audit/ every run, so a run is evidence and not
# just a console scroll.

$ErrorActionPreference = 'Continue'
$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot

$results = @()
function Record {
    param([string]$Check, [bool]$Ok, [string]$Detail)
    $script:results += [pscustomobject]@{
        Check = $Check; Result = $(if ($Ok) { 'PASS' } else { 'FAIL' }); Detail = $Detail
    }
    $colour = $(if ($Ok) { 'Green' } else { 'Red' })
    $tag = $(if ($Ok) { 'PASS' } else { 'FAIL' })
    Write-Host ("[{0}] {1,-42} {2}" -f $tag, $Check, $Detail) -ForegroundColor $colour
}

Write-Host ''
Write-Host '=== MELODIA TOON FILM - PROJECT VERIFY ===' -ForegroundColor Cyan
Write-Host "repo: $repoRoot"
Write-Host ''


# ---------------------------------------------------------------------------
# 1. fork sync - is the vendored brutalist set still the code we think it is?
# ---------------------------------------------------------------------------
Write-Host '-- 1. fork sync' -ForegroundColor Yellow
$forkOut = & python Tools/resync_fork.py 2>&1
$forkCode = $LASTEXITCODE
$syncLine = ($forkOut | Select-String -Pattern '^RESULT:' | Select-Object -First 1)
Record 'fork sync (vendored vs upstream)' ($forkCode -eq 0) `
    "$($syncLine -replace '^RESULT:\s*','')"

# ---------------------------------------------------------------------------
# 2. Blender-side verifier - builders, presets, dials, cycle guard
# ---------------------------------------------------------------------------
Write-Host ''
Write-Host '-- 2. builder verification (Blender, headless)' -ForegroundColor Yellow

$blender = $env:BR_BLENDER
if (-not $blender -or -not (Test-Path $blender)) {
    if (Test-Path 'C:\Program Files\Blender Foundation') {
        $blender = Get-ChildItem 'C:\Program Files\Blender Foundation' -Directory |
            Sort-Object Name -Descending |
            ForEach-Object { Join-Path $_.FullName 'blender.exe' } |
            Where-Object { Test-Path $_ } | Select-Object -First 1
    }
}

if (-not $blender) {
    Record 'Blender available' $false 'no blender.exe found - set $env:BR_BLENDER'
} else {
    Record 'Blender available' $true $blender
    $blog = Join-Path $env:TEMP 'verify_all_blender.txt'
    $blenderScript = Join-Path $repoRoot 'Blender\verify_brutalist_fork.py'
    $bp = Start-Process -FilePath $blender `
        -ArgumentList '--background', '--factory-startup', '--python', $blenderScript `
        -RedirectStandardOutput $blog -RedirectStandardError "$blog.err" `
        -NoNewWindow -PassThru -Wait
    $btxt = (Get-Content $blog -Raw -ErrorAction SilentlyContinue)
    $fails = ([regex]::Matches($btxt, '\[FAIL\]')).Count
    $passes = ([regex]::Matches($btxt, '\[PASS\]')).Count
    Record 'fork verifier (builders/presets/dials)' ($bp.ExitCode -eq 0) `
        "$passes assertions passed, $fails failed"
    foreach ($line in ($btxt -split "`r?`n" | Where-Object { $_ -match '\[FAIL\]' })) {
        Write-Host "        $line" -ForegroundColor Red
    }
}

# ---------------------------------------------------------------------------
# 3. .umap health - external actors and package-name sanity
# ---------------------------------------------------------------------------
Write-Host ''
Write-Host '-- 3. level/package health' -ForegroundColor Yellow

$umaps = Get-ChildItem -Path (Join-Path $repoRoot 'Content') -Recurse -Filter '*.umap' -File
$extHits = @(); $nameHits = @(); $missingExpected = @()
foreach ($u in $umaps) {
    $txt = [System.Text.Encoding]::ASCII.GetString([System.IO.File]::ReadAllBytes($u.FullName))
    $rel = $u.FullName.Substring($repoRoot.Length).TrimStart('\') -replace '\.umap$', ''
    $expected = '/Game/' + ($rel -replace '^Content\\', '' -replace '\\', '/')

    if ($txt -match '__External(Actors|Objects)__') {
        $extHits += ($u.FullName.Substring($repoRoot.Length).TrimStart('\'))
    }
    if ($txt -notmatch [regex]::Escape($expected)) {
        $missingExpected += "$($u.Name) (expected $expected)"
    }
    # A package literally named after its own parent folder - `/Game/Maps.Maps`.
    # That is the signature of new_level() being handed a FOLDER instead of a
    # level path, and how Content/Maps.umap got committed on 2026-09-30.
    foreach ($m in [regex]::Matches($txt, '/Game/([A-Za-z0-9_/]+)\.([A-Za-z0-9_]+)')) {
        $p1 = $m.Groups[1].Value; $p2 = $m.Groups[2].Value
        if (($p1 -split '/')[-1] -eq $p2) { $nameHits += "$($u.Name) contains $($m.Value)" }
    }
}

# POLICY REVERSED 2026-10-01: external actors are TRACKED, not banned. A level
# referencing external packages is fine *if those packages are on disk*. The
# failure that matters is a level whose external actors are MISSING - that is
# how a fresh clone used to open L_Toon_Lookdev empty (audit finding F1).
$extRoot = Join-Path $repoRoot 'Content\__ExternalActors__'
$extFiles = @()
if (Test-Path $extRoot) { $extFiles = @(Get-ChildItem $extRoot -Recurse -File -ErrorAction SilentlyContinue) }
$extOk = ($extHits.Count -eq 0) -or ($extFiles.Count -gt 0)
Record 'external actors in levels are present on disk' $extOk `
    $(if (-not $extOk) { "referenced but Content/__ExternalActors__ is empty: $($extHits -join '; ')" }
      elseif ($extHits.Count -eq 0) { "$($umaps.Count) level(s) checked, none external" }
      else { "$($extHits.Count) level(s) use external actors; $($extFiles.Count) packages on disk" })
Record 'no self-named packages' ($nameHits.Count -eq 0) `
    $(if ($nameHits.Count -eq 0) { 'ok' } else { ($nameHits -join '; ') })
Record 'levels resolve to their own package path' ($missingExpected.Count -eq 0) `
    $(if ($missingExpected.Count -eq 0) { 'ok' } else { ($missingExpected -join '; ') })

# ---------------------------------------------------------------------------
# 4. docs point at things that exist
# ---------------------------------------------------------------------------
Write-Host ''
Write-Host '-- 4. documentation paths' -ForegroundColor Yellow

$docIssues = @()
foreach ($doc in @('README.md', 'Docs\TOON_SPINE.md', 'Docs\FILM_PIPELINE.md')) {
    $p = Join-Path $repoRoot $doc
    if (-not (Test-Path $p)) { continue }
    $body = Get-Content $p -Raw
    foreach ($m in [regex]::Matches($body, '`?((?:Python|Blender|Tools|Docs|Config)[/\\][A-Za-z0-9_\-\./\\]+\.(?:py|md|ps1|ini))`?')) {
        $rel = $m.Groups[1].Value -replace '/', '\'
        if (-not (Test-Path (Join-Path $repoRoot $rel))) {
            $docIssues += "$doc -> $rel"
        }
    }
}
Record 'documented paths exist' ($docIssues.Count -eq 0) `
    $(if ($docIssues.Count -eq 0) { 'ok' } else { ($docIssues -join '; ') })

# ---------------------------------------------------------------------------
# 5. the pre-commit hook still behaves
# ---------------------------------------------------------------------------
Write-Host ''
Write-Host '-- 5. pre-commit hook behaviour' -ForegroundColor Yellow
$hookTest = Join-Path $repoRoot 'Tools\test_precommit.ps1'
if (-not (Test-Path $hookTest)) {
    Record 'pre-commit hook self-test' $false 'Tools/test_precommit.ps1 missing'
} else {
    $hlog = Join-Path $env:TEMP 'verify_all_hook.txt'
    $hp = Start-Process -FilePath 'powershell' `
        -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $hookTest `
        -RedirectStandardOutput $hlog -RedirectStandardError "$hlog.err" `
        -NoNewWindow -PassThru -Wait
    $htxt = (Get-Content $hlog -Raw -ErrorAction SilentlyContinue)
    $hline = ($htxt -split "`r?`n" | Where-Object { $_ -match '^RESULT:' } | Select-Object -First 1)
    Record 'pre-commit hook self-test' ($hp.ExitCode -eq 0) `
        "$($hline -replace '^RESULT:\s*','')"
}

# ---------------------------------------------------------------------------
# report + verdict
# ---------------------------------------------------------------------------
Write-Host ''
$failed = @($results | Where-Object { $_.Result -eq 'FAIL' }).Count
$reportDir = Join-Path $repoRoot 'Saved\Audit'
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$reportPath = Join-Path $reportDir ("verify_all_{0}.txt" -f (Get-Date -Format 'yyyy-MM-dd'))
$lines = @()
$lines += "MELODIA TOON FILM - verify_all"
$lines += "run      : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$lines += "repo     : $repoRoot"
$lines += "bracket  : $($results.Count) checks, $failed failed"
$lines += ""
$lines += ($results | Format-Table -AutoSize | Out-String -Width 200)
$lines += ""
$lines += "RAW FORK SYNC"
$lines += (($forkOut | Out-String))
$lines += ""
$lines += "RESULT: " + $(if ($failed -eq 0) { 'PASS' } else { 'FAIL' })
$lines | Set-Content -Path $reportPath -Encoding UTF8

Write-Host ("{0} of {1} checks passed" -f ($results.Count - $failed), $results.Count)
Write-Host "report: $reportPath"
if ($failed -eq 0) {
    Write-Host 'RESULT: PASS' -ForegroundColor Green
} else {
    Write-Host 'RESULT: FAIL' -ForegroundColor Red
}
Pop-Location
exit $failed

