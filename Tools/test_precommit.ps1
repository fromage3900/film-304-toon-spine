# test_precommit.ps1 - prove the pre-commit hook actually blocks what it claims.
#
# WHY: a guard nobody has seen fail is decoration. This builds a throwaway git
# repo in %TEMP%, installs the hook into it, and stages the exact shapes the hook
# is written against. It never touches this project's index or history.
#
# Run from anywhere:  powershell -File Tools/test_precommit.ps1
# Exit 0 = every rule behaved as documented.

$ErrorActionPreference = 'Continue'
$repoRoot = Split-Path -Parent $PSScriptRoot
$hookSrc  = Join-Path $repoRoot '.githooks\pre-commit'

if (-not (Test-Path $hookSrc)) { Write-Host "FAIL: hook not found at $hookSrc"; exit 2 }

$sandbox = Join-Path $env:TEMP ('melodia_hooktest_' + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Force -Path (Join-Path $sandbox '.githooks') | Out-Null
Copy-Item $hookSrc (Join-Path $sandbox '.githooks\pre-commit') -Force

# git writes progress to stderr; capture everything to a file so PowerShell does
# not raise a NativeCommandError on a *successful* command.
#
# NOTE the parameter is $GitArgs, not $Args: `$Args` is an automatic PowerShell
# variable, and shadowing it makes `& git @Args` pass NOTHING - every command then
# exits 1 and the harness reports all-FAIL. Cost one debugging round, 2026-09-30.
function Run-Git {
    param([string[]]$GitArgs, [string]$Tag)
    $out = Join-Path $sandbox ($Tag + '.txt')
    Push-Location $sandbox
    & git @GitArgs *> $out
    $code = $LASTEXITCODE
    Pop-Location
    return @{ Code = $code; Text = (Get-Content $out -Raw -ErrorAction SilentlyContinue) }
}

$results = @()
function Check {
    param([string]$Name, [bool]$Passed, [string]$Detail)
    $script:results += [pscustomobject]@{ Test = $Name; Result = if ($Passed) { 'PASS' } else { 'FAIL' }; Detail = $Detail }
}

$null = Run-Git @('init', '-q') 'init'
$null = Run-Git @('config', 'user.email', 'hooktest@example.com') 'cfg1'
$null = Run-Git @('config', 'user.name', 'hooktest') 'cfg2'
$null = Run-Git @('config', 'core.hooksPath', '.githooks') 'cfg3'
$null = Run-Git @('config', 'commit.gpgsign', 'false') 'cfg4'

# 1. baseline - a clean commit must be ALLOWED
Set-Content (Join-Path $sandbox 'ok.txt') 'hello'
$null = Run-Git @('add', 'ok.txt') 'a1'
$r = Run-Git @('commit', '-m', 'baseline') 'c1'
Check 'clean commit allowed' ($r.Code -eq 0) "exit=$($r.Code)"

# 2. Blender backup file must be BLOCKED
Set-Content (Join-Path $sandbox 'model.blend1') 'x'
$null = Run-Git @('add', '-f', 'model.blend1') 'a2'
$r = Run-Git @('commit', '-m', 'bad blend1') 'c2'
Check 'forbidden type .blend1 blocked' ($r.Code -ne 0 -and $r.Text -match 'Forbidden') "exit=$($r.Code)"
$null = Run-Git @('rm', '--cached', '-q', 'model.blend1') 'rm2'

# 3. World Partition external actors must be ALLOWED (policy reversed 2026-10-01).
#    They are the actor data for a WP level; blocking them made a clone open the
#    level empty (audit F1). The gate, not the hook, now checks they are present.
$ext = Join-Path $sandbox 'Content\__ExternalActors__\Maps\L_Toon_Lookdev\A\DK'
New-Item -ItemType Directory -Force -Path $ext | Out-Null
Set-Content (Join-Path $ext 'MEU0CIRDQGAYMGVWZ9X3I6.uasset') 'fake'
$null = Run-Git @('add', '-f', 'Content/__ExternalActors__') 'a3'
$r = Run-Git @('commit', '-m', 'tracked external actors') 'c3'
Check 'external actors allowed (policy 2026-10-01)' ($r.Code -eq 0) "exit=$($r.Code)"
$null = Run-Git @('rm', '-r', '--cached', '-q', 'Content/__ExternalActors__') 'rm3'

# 4. zero-byte file must be BLOCKED
New-Item -ItemType File -Force -Path (Join-Path $sandbox 'empty.txt') | Out-Null
$null = Run-Git @('add', '-f', 'empty.txt') 'a4'
$r = Run-Git @('commit', '-m', 'bad zero byte') 'c4'
Check 'zero-byte file blocked' ($r.Code -ne 0 -and $r.Text -match 'Zero-byte') "exit=$($r.Code)"
$null = Run-Git @('rm', '--cached', '-q', 'empty.txt') 'rm4'

# 5. protected file must be BLOCKED, and allowed with SKIP_PROTECTION=1
Set-Content (Join-Path $sandbox '.gitattributes') '*.txt text eol=lf'
$null = Run-Git @('add', '-f', '.gitattributes') 'a5'
$r = Run-Git @('commit', '-m', 'bad protected') 'c5'
Check 'protected file blocked' ($r.Code -ne 0 -and $r.Text -match 'Protected files') "exit=$($r.Code)"
$env:SKIP_PROTECTION = '1'
$r = Run-Git @('commit', '-m', 'deliberate protected change') 'c6'
Remove-Item Env:\SKIP_PROTECTION -ErrorAction SilentlyContinue
Check 'SKIP_PROTECTION=1 override works' ($r.Code -eq 0) "exit=$($r.Code)"

# 6. a build artifact must be BLOCKED while Audit evidence is ALLOWED
New-Item -ItemType Directory -Force -Path (Join-Path $sandbox 'Saved\Audit') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $sandbox 'Intermediate') | Out-Null
Set-Content (Join-Path $sandbox 'Saved\Audit\report.json') '{"ok":true}'
Set-Content (Join-Path $sandbox 'Intermediate\junk.uasset') 'x'
$null = Run-Git @('add', '-f', 'Saved/Audit/report.json') 'a6'
$r = Run-Git @('commit', '-m', 'evidence allowed') 'c7'
Check 'Saved/Audit/*.json evidence allowed' ($r.Code -eq 0) "exit=$($r.Code)"
$null = Run-Git @('add', '-f', 'Intermediate/junk.uasset') 'a7'
$r = Run-Git @('commit', '-m', 'bad artifact') 'c8'
Check 'build artifact blocked' ($r.Code -ne 0 -and $r.Text -match 'build artifacts') "exit=$($r.Code)"

Remove-Item -Recurse -Force $sandbox -ErrorAction SilentlyContinue

Write-Host ''
Write-Host '=== pre-commit hook behaviour ==='
$results | Format-Table -AutoSize | Out-String -Width 160 | Write-Host
$failed = ($results | Where-Object { $_.Result -eq 'FAIL' }).Count
Write-Host ("RESULT: {0}  ({1} passed, {2} failed)" -f `
    $(if ($failed -eq 0) { 'PASS' } else { 'FAIL' }), ($results.Count - $failed), $failed)
exit $failed
