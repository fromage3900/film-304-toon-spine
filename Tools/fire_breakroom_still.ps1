# Fire one break-room still through the repo's own render harness.
#
# The harness calls AutomationLibrary.take_high_res_screenshot, which BLOCKS the
# editor's game thread for the whole capture - the prototype spec records 258 s
# for the first frame of a session, nearly all shader compilation. Running it
# through Monolith's HTTP transport inside this session would stall the agent
# for minutes and risks the transport dropping mid-request, which is what
# abandoned an HTTP client on 2026-10-01. So it is fired as a detached process
# that writes its response to disk, and the result is polled separately.
param(
  [string]$Shot = "SH090",
  [string]$Spec = "specs/office_spider/breakroom_renders.v1.json",
  [string]$Port = "9316"
)

$ErrorActionPreference = "Stop"
$root = "G:\film-304-toon-spine"
$outDir = Join-Path $root "Saved\Renders\breakroom"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# The request file drives which shot the harness fires; it reads one per call.
# The spec path MUST be absolute: render_prototypes.py resolves req["spec"] with
# a bare Path(...), so a repo-relative path is read against the editor's working
# directory (not the repo root) and comes back FileNotFoundError.
$reqPath = Join-Path $root "Saved\Renders\prototypes\_request.json"
New-Item -ItemType Directory -Force -Path (Split-Path $reqPath) | Out-Null
$specAbs = if ([System.IO.Path]::IsPathRooted($Spec)) { $Spec } else { Join-Path $root $Spec }
$req = @{ mode = "stills"; shots = @($Shot); spec = $specAbs } | ConvertTo-Json -Compress
[System.IO.File]::WriteAllText($reqPath, $req, (New-Object System.Text.UTF8Encoding($false)))

$body = @{
  jsonrpc = "2.0"; id = 1; method = "tools/call"
  params = @{
    name = "editor_query"
    arguments = @{
      action  = "run_python"
      command = "import runpy`nrunpy.run_path('G:/film-304-toon-spine/Python/render_prototypes.py', run_name='__main__')"
    }
  }
} | ConvertTo-Json -Depth 8

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$respFile = Join-Path $outDir ("_mcp_response_{0}.json" -f $stamp)

"fired {0} spec={1} at {2}" -f $Shot, $Spec, (Get-Date -Format "HH:mm:ss") |
  Out-File (Join-Path $outDir "_render_fire.log") -Append -Encoding utf8

try {
  $r = Invoke-WebRequest -Uri ("http://127.0.0.1:{0}/mcp" -f $Port) -Method Post `
        -Body $body -ContentType "application/json" -TimeoutSec 1800 -UseBasicParsing
  [System.IO.File]::WriteAllText($respFile, $r.Content)
  ("completed {0} at {1}; bytes={2}" -f $Shot, (Get-Date -Format "HH:mm:ss"), $r.Content.Length) |
    Out-File (Join-Path $outDir "_render_fire.log") -Append -Encoding utf8
} catch {
  ("FAILED {0}: {1}" -f $Shot, $_.Exception.Message) |
    Out-File (Join-Path $outDir "_render_fire.log") -Append -Encoding utf8
}