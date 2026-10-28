$ErrorActionPreference = 'Stop'
$engineRoot = Join-Path $PSScriptRoot '../vendor/dom-to-pptx'
Push-Location $engineRoot
try {
    & npm.cmd install --ignore-scripts --legacy-peer-deps
    if ($LASTEXITCODE -ne 0) { throw 'HTML engine dependency installation failed' }
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'HTML engine build failed' }
} finally { Pop-Location }
