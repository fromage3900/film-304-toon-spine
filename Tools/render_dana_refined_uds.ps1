param([string]$Shot = '*')
$ErrorActionPreference = 'Stop'
$danaRoot = Split-Path -Parent $PSScriptRoot
$danaBuild = Get-Content -LiteralPath (Join-Path $danaRoot 'Saved/Audit/dana_refined_uds_build.json') -Raw | ConvertFrom-Json
$danaResults = @()
foreach ($danaJob in $danaBuild.jobs | Where-Object stem -Like $Shot) {
    $danaSeqName = ($danaJob.sequence -split '/')[-1]
    $danaCfgName = ($danaJob.config -split '/')[-1]
    $danaLog = Join-Path $danaRoot ('Saved/Logs/' + $danaJob.stem + '.log')
    $danaImage = Join-Path $danaRoot ('Saved/Renders/dana_refined_uds/' + $danaJob.stem + '.png')
    $danaStart = Get-Date
    $danaArgs = @(('"' + (Join-Path $danaRoot 'HumberToonShader.uproject') + '"'), $danaJob.map, '-game', ('-LevelSequence="' + $danaJob.sequence + '.' + $danaSeqName + '"'), ('-MoviePipelineConfig="' + $danaJob.config + '.' + $danaCfgName + '"'), '-windowed', '-unattended', '-NoSound', ('-abslog="' + $danaLog + '"'))
    $danaProcess = Start-Process -FilePath 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe' -ArgumentList $danaArgs -PassThru -Wait -WindowStyle Hidden
    $danaImageInfo = Get-Item -LiteralPath $danaImage -ErrorAction SilentlyContinue
    $danaFresh = $danaImageInfo -and $danaImageInfo.LastWriteTime -ge $danaStart -and $danaImageInfo.Length -gt 0
    $danaRow = [pscustomobject]@{shot=$danaJob.stem; exit_code=$danaProcess.ExitCode; fresh_image=[bool]$danaFresh; image=$danaImage; log=$danaLog; visual_review='pending'}
    $danaResults += $danaRow
    $danaRow | ConvertTo-Json -Compress
    $danaResults | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $danaRoot 'Saved/Audit/dana_refined_uds_render_results.json') -Encoding UTF8
    if ($danaProcess.ExitCode -ne 0 -or -not $danaFresh) { throw ('Render failed: ' + $danaJob.stem) }
}
