[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ProjectRoot,
    [Parameter(Mandatory = $true)][string]$Workspace,
    [Parameter(Mandatory = $true)][string]$Title,
    [string]$Scenario = '科研工作汇报',
    [string]$Audience = '课题组与同行专家',
    [int]$DurationMin = 20,
    [switch]$SkipWebConnection
)

$ErrorActionPreference = 'Stop'
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$initializer = Join-Path $scriptRoot 'init_ppt_session.py'
$projectPath = [System.IO.Path]::GetFullPath($ProjectRoot)
$workspacePath = [System.IO.Path]::GetFullPath($Workspace)
$bundledPython = 'C:\Users\21797\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$pythonExe = if (Test-Path -LiteralPath $bundledPython) { $bundledPython } else { (Get-Command python3 -ErrorAction Stop).Source }

& $pythonExe $initializer --out $workspacePath --title $Title --scenario $Scenario --audience $Audience --duration-min $DurationMin --project-root $projectPath
if ($LASTEXITCODE -ne 0) { throw 'Local PPT workspace initialization failed.' }

$connectionRecord = Join-Path $workspacePath 'bridge-connect.json'
if ($SkipWebConnection) {
    $record = [ordered]@{
        schema = 'ppt_bridge_connection_v1'
        status = 'skipped_for_test_or_explicit_offline_mode'
        connected = $false
        warning = 'Do not claim that GPT-6 or GPT Image 2.5 is connected.'
        created_at = [DateTimeOffset]::UtcNow.ToString('o')
    }
    $record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $connectionRecord -Encoding utf8
    Write-Warning 'Web connection skipped. This switch is test/offline-only and must not be used for a real web-assisted deck.'
    exit 0
}

$bridge = 'C:\Users\21797\.codex\skills\codex-chatgpt-bridge\scripts\workspace_bridge.ps1'
if (-not (Test-Path -LiteralPath $bridge)) {
    $record = [ordered]@{
        schema = 'ppt_bridge_connection_v1'
        status = 'failed'
        connected = $false
        error = "Bridge wrapper not found: $bridge"
        created_at = [DateTimeOffset]::UtcNow.ToString('o')
    }
    $record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $connectionRecord -Encoding utf8
    throw $record.error
}

try {
    $bridgeOutput = & $bridge -Action Connect -WorkspacePath $projectPath -Capability Auto -AllowPublicTunnel 2>&1
    $exitCode = $LASTEXITCODE
    $record = [ordered]@{
        schema = 'ppt_bridge_connection_v1'
        status = if ($exitCode -eq 0) { 'connected' } else { 'failed' }
        connected = ($exitCode -eq 0)
        workspace = $projectPath
        capability = 'Auto'
        output = @($bridgeOutput | ForEach-Object { $_.ToString() })
        created_at = [DateTimeOffset]::UtcNow.ToString('o')
    }
    $record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $connectionRecord -Encoding utf8
    if ($exitCode -ne 0) { throw "Bridge connection failed with exit code $exitCode." }
} catch {
    if (-not (Test-Path -LiteralPath $connectionRecord)) {
        [ordered]@{
            schema = 'ppt_bridge_connection_v1'
            status = 'failed'
            connected = $false
            error = $_.Exception.Message
            created_at = [DateTimeOffset]::UtcNow.ToString('o')
        } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $connectionRecord -Encoding utf8
    }
    Write-Error 'The local workspace was preserved, but the web bridge did not connect. Do not claim GPT-6 or GPT Image 2.5 is connected.'
    exit 1
}

Write-Host 'Workspace initialized and bridge connected.'
Write-Host 'Next: send planning/gpt6_task_packet.md to the visible GPT-6 chat, then create one GPT Image 2.5 job per accepted element request.'
