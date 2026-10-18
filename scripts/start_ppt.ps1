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
$runtimeJson=& $python (Join-Path $PSScriptRoot 'ensure_runtime.py') --project-root $ProjectRoot --python-executable $python
if($LASTEXITCODE -ne 0){throw 'Project-local PPT Python runtime preparation failed'}
$runtime=$runtimeJson | ConvertFrom-Json
if($runtime.python_path){
 $env:PYTHONPATH=$runtime.python_path + $(if($env:PYTHONPATH){[IO.Path]::PathSeparator + $env:PYTHONPATH}else{''})
}
$arguments=@((Join-Path $PSScriptRoot 'auto_workflow.py'),'prepare','--project-root',$ProjectRoot)
foreach($pair in @(@('--workspace',$Workspace),@('--title',$Title),@('--profile',$Profile),@('--request',$Request),@('--audience',$Audience),@('--theme-profile',$ThemeProfile),@('--theme-reason',$ThemeReason))){
 if($pair[1]){$arguments+=@($pair[0],$pair[1])}
}
if($PSBoundParameters.ContainsKey('DurationMin')){$arguments+=@('--duration',[string]$DurationMin)}
$previousPythonEncoding=$env:PYTHONIOENCODING
try {
 $env:PYTHONIOENCODING='utf-8'
 $prepared=& $python @arguments
 if($LASTEXITCODE -ne 0){throw 'Automatic brief/workspace preparation failed'}
} finally {
 if($null -eq $previousPythonEncoding){Remove-Item Env:\PYTHONIOENCODING -ErrorAction SilentlyContinue}else{$env:PYTHONIOENCODING=$previousPythonEncoding}
}
$context=$prepared | ConvertFrom-Json
$Workspace=$context.workspace
Write-Host "Planning packet: $($context.planning_packet)"
Write-Host "Material selection: $($context.material_selection). Inspect and supply necessary content to BOTH GPT and Image before dispatch. Paths alone are not materials."
& (Join-Path $PSScriptRoot 'ppt_bridge.ps1') -Action Prepare -ProjectRoot $ProjectRoot -Workspace $Workspace
if($LASTEXITCODE -ne 0){throw 'Startup failed; retain draft state'}
Write-Host 'NEXT REQUIRED: prefer the built-in browser; on verified failure use the official Playwright CLI. Verify login/model/image entry, record actual route via bridge_session observe, run ppt_bridge Check. Prepare and transfer necessary material packets before planning/generation.'
