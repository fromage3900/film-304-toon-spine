# V02 pass: the two window-heavy hero shots at camera bias 0.8 (was 1.4).
$ErrorActionPreference = 'Continue'
$ue    = 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$proj  = 'G:/film-304-toon-spine/HumberToonShader.uproject'
$level = 'L_Film_HeroTonight_20261018'
$outDir = 'G:/film-304-toon-spine/Saved/Audit/EveningExecution_20261018/hero_render_logs'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$jobs = @(
    @{ stem = 'HERO01_V02'; seq = '/Game/Sequences/Film304Hero_20261018/LS_HERO01_WideDiagonal.LS_HERO01_WideDiagonal';  cfg = '/Game/MoviePipelines/Hero20261018/CFG_HERO01_WideDiagonal.CFG_HERO01_WideDiagonal' },
    @{ stem = 'HERO03_V02'; seq = '/Game/Sequences/Film304Hero_20261018/LS_HERO03_EntryArrival.LS_HERO03_EntryArrival';   cfg = '/Game/MoviePipelines/Hero20261018/CFG_HERO03_EntryArrival.CFG_HERO03_EntryArrival' }
)

foreach ($j in $jobs) {
    $logFile = Join-Path $outDir ($j.stem + '_render.log')
    Write-Output ("START " + $j.stem + " " + (Get-Date -Format 'HH:mm:ss'))
    & $ue $proj $level -game -LevelSequence="$($j.seq)" -MoviePipelineConfig="$($j.cfg)" -windowed -log -unattended *>> $logFile
    Write-Output ("EXIT " + $j.stem + " code=$LASTEXITCODE " + (Get-Date -Format 'HH:mm:ss'))
}
Write-Output ("ALL_DONE " + (Get-Date -Format 'HH:mm:ss'))
