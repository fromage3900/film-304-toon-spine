# mcp_exec.ps1 - run a Python file inside the LIVE Unreal Editor via Claireon MCP.
#
#     powershell -File Tools/mcp_exec.ps1 -Path Python\audit_x.py
#
# Why: the editor is already open on the production level. A second
# UnrealEditor-Cmd instance would fight it for package writes, so operational
# scripts are executed through the editor's own python_execute bridge.
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [int]$TimeoutSec = 900
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$file = if ([System.IO.Path]::IsPathRooted($Path)) { $Path } else { Join-Path $repo $Path }
$code = [System.IO.File]::ReadAllText($file)

$payload = @{
    jsonrpc = '2.0'
    id      = 1
    method  = 'tools/call'
    params  = @{
        name      = 'python_execute'
        arguments = @{ code = $code; quiet = $true }
    }
} | ConvertTo-Json -Depth 8 -Compress

$r = Invoke-WebRequest -Uri 'http://127.0.0.1:62468/mcp' -Method Post `
    -ContentType 'application/json' `
    -Headers @{ Accept = 'application/json, text/event-stream' } `
    -Body $payload -TimeoutSec $TimeoutSec -UseBasicParsing

$raw = $r.Content
# Streamable HTTP may answer as SSE frames; keep the last JSON data line.
if ($raw -match '(?m)^data:\s*(\{.*\})\s*$') { $raw = $matches[1] }
$j = $raw | ConvertFrom-Json

if ($j.error) {
    Write-Output ('MCP_ERROR: ' + ($j.error | ConvertTo-Json -Depth 6 -Compress))
    exit 2
}
if ($j.result.isError) {
    Write-Output 'TOOL_ERROR:'
}
$text = @()
foreach ($c in $j.result.content) {
    if ($c.type -eq 'text') { $text += $c.text }
}
$text -join "`n"
