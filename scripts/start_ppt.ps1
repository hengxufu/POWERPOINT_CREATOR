[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$ProjectRoot,
 [Parameter(Mandatory=$true)][string]$Workspace,
 [Parameter(Mandatory=$true)][string]$Title,
 [ValidateSet('scholarship','research','challenge','innovation')][string]$Profile='research'
)
$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath (Join-Path $Workspace 'session.json')){
 & (Join-Path $PSScriptRoot 'ppt_bridge.ps1') -Action Prepare -ProjectRoot $ProjectRoot -Workspace $Workspace
} else {
 & (Join-Path $PSScriptRoot 'init_ppt_session.ps1') -ProjectRoot $ProjectRoot -Workspace $Workspace -Title $Title -Profile $Profile
}
if($LASTEXITCODE -ne 0){throw 'Startup failed; retain draft state'}
Write-Host 'NEXT REQUIRED: observe the task browser, verify login/model/image entry, record evidence via bridge_session observe, run ppt_bridge Check. Do not skip directly to deck generation.'
