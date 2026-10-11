[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$ProjectRoot,
 [Parameter(Mandatory=$true)][string]$Workspace,
 [Parameter(Mandatory=$true)][string]$Title,
 [string]$Scenario='科研工作汇报',
 [string]$Audience='课题组与同行专家',
 [int]$DurationMin=20,
 [ValidateSet('scholarship','research','challenge','innovation')][string]$Profile='research',
 [switch]$SkipWebConnection
)
$ErrorActionPreference='Stop'
$bundled=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$python=if(Test-Path -LiteralPath $bundled){$bundled}else{(Get-Command python -ErrorAction Stop).Source}
& $python (Join-Path $PSScriptRoot 'init_ppt_session.py') --out $Workspace --title $Title --scenario $Scenario --audience $Audience --duration-min $DurationMin --profile $Profile --project-root $ProjectRoot
if($LASTEXITCODE -ne 0){throw 'PPT initialization failed'}
if($SkipWebConnection){
 Write-Warning 'Explicit test/offline mode only. Session is not web-connected; final web delivery gate will fail.'
 exit 0
}
& (Join-Path $PSScriptRoot 'ppt_bridge.ps1') -Action Prepare -ProjectRoot $ProjectRoot -Workspace $Workspace
if($LASTEXITCODE -ne 0){throw 'Connection preparation failed'}
Write-Host 'Local workspace and fresh bridge profile prepared. Browser observation and model verification are required next; no model connection is claimed yet.'
