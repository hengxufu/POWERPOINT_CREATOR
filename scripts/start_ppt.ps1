[CmdletBinding()]
param(
 [string]$ProjectRoot=(Get-Location).Path,
 [string]$Workspace,
 [string]$Title,
 [ValidateSet('scholarship','research','challenge','innovation')][string]$Profile,
 [string]$Request,
 [string]$Audience,
 [int]$DurationMin,
 [ValidateSet('beihang-blue','beihang-green','beihang-ginkgo','none')][string]$ThemeProfile,
 [string]$ThemeReason
)
$ErrorActionPreference='Stop'
$bundled=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$python=if(Test-Path -LiteralPath $bundled){$bundled}else{(Get-Command python -ErrorAction Stop).Source}
$arguments=@((Join-Path $PSScriptRoot 'auto_workflow.py'),'prepare','--project-root',$ProjectRoot)
foreach($pair in @(@('--workspace',$Workspace),@('--title',$Title),@('--profile',$Profile),@('--request',$Request),@('--audience',$Audience),@('--theme-profile',$ThemeProfile),@('--theme-reason',$ThemeReason))){
 if($pair[1]){$arguments+=@($pair[0],$pair[1])}
}
if($PSBoundParameters.ContainsKey('DurationMin')){$arguments+=@('--duration',[string]$DurationMin)}
$prepared=& $python @arguments
if($LASTEXITCODE -ne 0){throw 'Automatic brief/workspace preparation failed'}
$context=$prepared | ConvertFrom-Json
$Workspace=$context.workspace
Write-Host "Planning packet: $($context.planning_packet)"
& (Join-Path $PSScriptRoot 'ppt_bridge.ps1') -Action Prepare -ProjectRoot $ProjectRoot -Workspace $Workspace
if($LASTEXITCODE -ne 0){throw 'Startup failed; retain draft state'}
Write-Host 'NEXT REQUIRED: observe the task browser, verify login/model/image entry, record evidence via bridge_session observe, run ppt_bridge Check. Do not skip directly to deck generation.'
