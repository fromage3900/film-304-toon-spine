# Sequential bedtime hero renders (3 stills, 1920x1080, dusk).
# Fixed 2026-10-18: paths must be "/Game/<Folder>/<Asset>.<Asset>" (folder segment!).
# Exact paths pulled from Saved/Audit/EveningExecution_20261018/hero_shots_commands.json.
$ErrorActionPreference = 'Continue'
$ue    = 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$proj  = 'G:/film-304-toon-spine/HumberToonShader.uproject'
$level = 'L_Film_HeroTonight_20261018'
$outDir = 'G:/film-304-toon-spine/Saved/Audit/EveningExecution_20261018/hero_render_logs'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$jobs = @(
    @{ stem = 'HERO01_WideDiagonal'; seq = '/Game/Sequences/Film304Hero_20261018/LS_HERO01_WideDiagonal.LS_HERO01_WideDiagonal';     cfg = '/Game/MoviePipelines/Hero20261018/CFG_HERO01_WideDiagonal.CFG_HERO01_WideDiagonal' },
    @{ stem = 'HERO02_DeskInsert';   seq = '/Game/Sequences/Film304Hero_20261018/LS_HERO02_DeskInsert.LS_HERO02_DeskInsert';         cfg = '/Game/MoviePipelines/Hero20261018/CFG_HERO02_DeskInsert.CFG_HERO02_DeskInsert' },
    @{ stem = 'HERO03_EntryArrival'; seq = '/Game/Sequences/Film304Hero_20261018/LS_HERO03_EntryArrival.LS_HERO03_EntryArrival';      cfg = '/Game/MoviePipelines/Hero20261018/CFG_HERO03_EntryArrival.CFG_HERO03_EntryArrival' }
)

foreach ($j in $jobs) {
    $logFile = Join-Path $outDir ($j.stem + '_render.log')
    $marker  = Join-Path $outDir ($j.stem + '_DONE')
    if (Test-Path $marker) { Remove-Item $marker | Out-Null }
    Write-Output ("START " + $j.stem + " " + (Get-Date -Format 'HH:mm:ss'))
    & $ue $proj $level -game -LevelSequence="$($j.seq)" -MoviePipelineConfig="$($j.cfg)" -windowed -log -unattended *>> $logFile
    $code = $LASTEXITCODE
    if ($code -eq 0) { New-Item -ItemType File -Path $marker | Out-Null }
    Write-Output ("EXIT " + $j.stem + " code=" + $code + " " + (Get-Date -Format 'HH:mm:ss'))
}
Write-Output ("ALL_DONE " + (Get-Date -Format 'HH:mm:ss'))
