param(
  [ValidateSet('Version','AttachCdp','AttachExtension','OpenIsolated','Snapshot','Detach')]
  [string]$Action = 'Version',
  [ValidateSet('chrome','msedge')][string]$Browser = 'msedge',
  [ValidatePattern('^[a-zA-Z0-9_-]+$')][string]$Session = 'ppt-chatgpt'
)
$ErrorActionPreference = 'Stop'
$cliArgs = @('--yes','--package','@playwright/cli@0.1.22','playwright-cli')
if ($Action -eq 'Version') { $cliArgs += '--version' }
else {
  $cliArgs += "-s=$Session"
  switch ($Action) {
    'AttachCdp' { $cliArgs += @('attach',"--cdp=$Browser",'--idle-timeout=600000') }
    'AttachExtension' { $cliArgs += @('attach',"--extension=$Browser",'--idle-timeout=600000') }
    'OpenIsolated' { $cliArgs += @('open','https://chatgpt.com',"--browser=$Browser",'--headed','--idle-timeout=600000') }
    'Snapshot' { $cliArgs += 'snapshot' }
    'Detach' { $cliArgs += 'detach' }
  }
}
& npx.cmd @cliArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
