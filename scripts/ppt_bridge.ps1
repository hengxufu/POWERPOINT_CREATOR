[CmdletBinding()]
param(
  [ValidateSet('Prepare','Check','Off')][string]$Action='Prepare',
  [Parameter(Mandatory=$true)][string]$ProjectRoot,
  [Parameter(Mandatory=$true)][string]$Workspace
)
$ErrorActionPreference='Stop'
$python=(Get-Command python -ErrorAction SilentlyContinue).Source
$bundled=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if(Test-Path -LiteralPath $bundled){$python=$bundled}
if(-not $python){throw 'Python runtime is required'}
$contract=Join-Path $PSScriptRoot 'bridge_session.py'
$controller=Join-Path $PSScriptRoot '..\bridge\scripts\bridge_controller.ps1'
$project=[IO.Path]::GetFullPath($ProjectRoot)
$work=[IO.Path]::GetFullPath($Workspace)
$record=Join-Path $work 'bridge-connect.json'
if($Action -eq 'Prepare'){
  & $python $contract prepare --workspace $work --project-root $project
  if($LASTEXITCODE -ne 0){throw 'Unsafe root or invalid workspace'}
} else {
  $existing=Get-Content -LiteralPath $record -Raw -Encoding utf8 | ConvertFrom-Json
  if($existing.project_root -ne $project -or @($existing.allowed_roots).Count -ne 1 -or $existing.allowed_roots[0] -ne $project){throw 'Connection root mismatch'}
}
$sha=[Security.Cryptography.SHA256]::Create()
try{$id=([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($project.ToLowerInvariant())))).Replace('-','').Substring(0,12)}finally{$sha.Dispose()}
$state=Join-Path $env:LOCALAPPDATA "devspace-ppt-$id"
if($Action -eq 'Prepare'){
  # A fresh exact profile, no remembered tunnel and no public endpoint.
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $controller -Action Configure -ProjectRoot $project -AllowedRoots $project -Tunnel none -StateDir $state
  if($LASTEXITCODE -ne 0){throw 'Embedded bridge configuration failed'}
  $data=Get-Content -LiteralPath $record -Raw -Encoding utf8 | ConvertFrom-Json
  $data.local_profile_configured=$true
  $data.status='requires_browser_observation'
  $data | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $record -Encoding utf8
  Write-Host 'Profile prepared. Now use browser tools to verify ChatGPT login, GPT-6 selector and image creation entry; record actual observations. This is not a connected-model claim.'
} elseif($Action -eq 'Off'){
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $controller -Action Off -StateDir $state
  if($LASTEXITCODE -ne 0){throw 'Bridge Off failed; do not claim cleanup succeeded'}
  & $python $contract close --workspace $work
  exit $LASTEXITCODE
} else {
  & $python $contract check --workspace $work
  exit $LASTEXITCODE
}
