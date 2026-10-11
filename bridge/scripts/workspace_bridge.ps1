[CmdletBinding()]
param(
  [ValidateSet("Plan", "Prepare", "Connect", "Disconnect", "Status", "Doctor")]
  [string]$Action = "Plan",

  [string]$WorkspacePath = (Get-Location).Path,

  [ValidateSet("Auto", "none", "cloudflare", "external", "cloudflare-worker")]
  [string]$Tunnel = "Auto",

  [string]$PublicBaseUrl,

  [ValidateRange(1, 65535)]
  [int]$Port = 7676,

  [ValidateSet("Reasoning", "ImageQuality", "ImageFast", "Auto")]
  [string]$Capability = "Auto",

  [switch]$AllowPublicTunnel,

  [switch]$InstallCloudflared,

  [string]$StateDir = (Join-Path $env:LOCALAPPDATA "devspace-bridge"),

  [string]$ControllerScript
)

$ErrorActionPreference = "Stop"
try {
  [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false
} catch { }

if (-not $ControllerScript) {
  $ControllerScript = Join-Path $PSScriptRoot "bridge_controller.ps1"
}

$ProfilePath = Join-Path $StateDir "controller-profile.json"
$SessionPath = Join-Path $StateDir "workspace-session.json"
$PowerShellExe = (Get-Command powershell.exe -ErrorAction Stop).Source

function Read-JsonFile([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return $null }
  $utf8 = New-Object System.Text.UTF8Encoding $false
  [System.IO.File]::ReadAllText($Path, $utf8) | ConvertFrom-Json
}

function Write-JsonFileAtomic($Value, [string]$Path) {
  $directory = Split-Path -Parent $Path
  New-Item -ItemType Directory -Force -Path $directory | Out-Null
  $temp = "$Path.$([Guid]::NewGuid().ToString('n')).tmp"
  $utf8 = New-Object System.Text.UTF8Encoding $false
  [System.IO.File]::WriteAllText($temp, ($Value | ConvertTo-Json -Depth 10), $utf8)
  if (Test-Path -LiteralPath $Path) {
    Remove-Item -LiteralPath $Path -Force
  }
  [System.IO.File]::Move($temp, $Path)
}

function Write-Json($Value) {
  [Console]::Out.WriteLine(($Value | ConvertTo-Json -Depth 12))
}

function Test-AbsoluteHttpsUrl([string]$Url) {
  if (-not $Url) { return $false }
  $parsed = $null
  if (-not [Uri]::TryCreate($Url, [UriKind]::Absolute, [ref]$parsed)) { return $false }
  return (
    $parsed.Scheme -eq "https" -and
    -not [string]::IsNullOrWhiteSpace($parsed.Host) -and
    [string]::IsNullOrWhiteSpace($parsed.UserInfo) -and
    [string]::IsNullOrWhiteSpace($parsed.Query) -and
    [string]::IsNullOrWhiteSpace($parsed.Fragment)
  )
}

function Resolve-SafeWorkspace([string]$Path) {
  if (-not $Path) { throw "WorkspacePath is required." }
  $item = Get-Item -LiteralPath (Resolve-Path -LiteralPath $Path).Path
  if (-not $item.PSIsContainer) { throw "WorkspacePath must be a directory: $Path" }

  $full = [System.IO.Path]::GetFullPath($item.FullName).TrimEnd("\", "/")
  $drive = [System.IO.Path]::GetPathRoot($full).TrimEnd("\", "/")
  $userProfilePath = [System.IO.Path]::GetFullPath($env:USERPROFILE).TrimEnd("\", "/")
  $unsafe = @(
    $drive,
    $userProfilePath,
    [Environment]::GetFolderPath("Desktop"),
    [Environment]::GetFolderPath("MyDocuments")
  ) | Where-Object { $_ } | ForEach-Object {
    [System.IO.Path]::GetFullPath($_).TrimEnd("\", "/")
  }
  foreach ($candidate in $unsafe) {
    if ($full.Equals($candidate, [System.StringComparison]::OrdinalIgnoreCase)) {
      throw "Refusing broad or sensitive workspace root: $full"
    }
  }
  return $full
}

function Invoke-Controller([string[]]$Arguments) {
  if (-not (Test-Path -LiteralPath $ControllerScript)) {
    throw "Bridge controller not found: $ControllerScript"
  }
  $output = & $PowerShellExe -NoProfile -ExecutionPolicy Bypass -File $ControllerScript @Arguments 2>&1 | Out-String
  $exit = $LASTEXITCODE
  if ($exit -ne 0) {
    throw "Bridge controller failed (exit $exit): $($output.Trim())"
  }
  return $output.Trim()
}

function Resolve-TunnelPlan($ExistingProfile) {
  $effectiveTunnel = $Tunnel
  $effectiveBase = if ($PublicBaseUrl) { $PublicBaseUrl.TrimEnd("/") } else { $null }
  $reusedStableProfile = $false

  if ($effectiveTunnel -eq "Auto") {
    if ($ExistingProfile -and $ExistingProfile.tunnel -in @("cloudflare-worker", "external") -and $ExistingProfile.publicBaseUrl) {
      $effectiveTunnel = [string]$ExistingProfile.tunnel
      $effectiveBase = ([string]$ExistingProfile.publicBaseUrl).TrimEnd("/")
      $reusedStableProfile = $true
    } elseif ($effectiveBase) {
      $effectiveTunnel = "external"
    } else {
      $effectiveTunnel = "cloudflare"
    }
  }

  if ($effectiveTunnel -in @("cloudflare-worker", "external") -and -not (Test-AbsoluteHttpsUrl $effectiveBase)) {
    throw "$effectiveTunnel requires PublicBaseUrl as a clean absolute HTTPS URL."
  }
  if ($effectiveTunnel -in @("cloudflare", "cloudflare-worker", "external") -and -not $AllowPublicTunnel -and $Action -in @("Prepare", "Connect")) {
    throw "This action would expose a public bridge endpoint. Re-run only after the current user request explicitly authorizes connection, with -AllowPublicTunnel."
  }

  return [ordered]@{
    tunnel = $effectiveTunnel
    publicBaseUrl = $effectiveBase
    reusedStableProfile = $reusedStableProfile
    browserAppUpdateExpected = ($effectiveTunnel -eq "cloudflare" -and -not $reusedStableProfile)
  }
}

function Get-ModelRoute([string]$RequestedCapability) {
  $route = switch ($RequestedCapability) {
    "Reasoning" { "reasoning" }
    "ImageQuality" { "image-quality" }
    "ImageFast" { "image-fast" }
    default { "intent-dependent" }
  }
  return [ordered]@{
    route = $route
    preferredTextModel = "gpt-6-astra"
    balancedTextFallback = "gpt-6.1-sol"
    efficientTextFallback = "gpt-6-luna"
    preferredImageModel = "gpt-image-2.5-sunburst"
    fastImageModel = "gpt-image-2.5-flare"
    webSelectionRule = "Select the exact visible ChatGPT model/tool when available; never claim an exact backend when the web UI does not expose it."
  }
}

function Get-Plan([string]$Workspace) {
  $profile = Read-JsonFile $ProfilePath
  $tunnelPlan = Resolve-TunnelPlan $profile
  $modelRoute = Get-ModelRoute $Capability
  return [ordered]@{
    action = $Action
    workspace = $Workspace
    allowedRoots = @($Workspace)
    stateDir = $StateDir
    tunnelPlan = $tunnelPlan
    modelRoute = $modelRoute
    zeroTouchEligible = [bool]($profile -and $tunnelPlan.reusedStableProfile)
    firstRunLimit = if ($profile -and $tunnelPlan.reusedStableProfile) { $null } else { "A first ChatGPT App/OAuth authorization or a changing Quick Tunnel URL may still require browser work. Codex should automate browser navigation when available, but must not bypass sign-in, account entitlement, or authorization consent." }
  }
}

try {
  if ($Action -eq "Disconnect") {
    $raw = Invoke-Controller @("-Action", "Off", "-StateDir", $StateDir)
    Write-Json ([ordered]@{ status = "success"; action = "Disconnect"; controller = $raw })
    exit 0
  }
  if ($Action -in @("Status", "Doctor")) {
    $raw = Invoke-Controller @("-Action", $Action, "-StateDir", $StateDir)
    Write-Json ([ordered]@{ status = "success"; action = $Action; controller = $raw; session = Read-JsonFile $SessionPath })
    exit 0
  }

  $workspace = Resolve-SafeWorkspace $WorkspacePath
  $plan = Get-Plan $workspace
  if ($Action -eq "Plan") {
    Write-Json $plan
    exit 0
  }

  $configureArgs = @(
    "-Action", "Configure",
    "-ProjectRoot", $workspace,
    "-AllowedRoots", $workspace,
    "-Tunnel", [string]$plan.tunnelPlan.tunnel,
    "-Port", [string]$Port,
    "-StateDir", $StateDir
  )
  if ($plan.tunnelPlan.publicBaseUrl) {
    $configureArgs += @("-PublicBaseUrl", [string]$plan.tunnelPlan.publicBaseUrl)
  }
  if ($InstallCloudflared) { $configureArgs += "-InstallCloudflared" }

  $configureRaw = Invoke-Controller $configureArgs
  $session = [ordered]@{
    schemaVersion = 1
    workspace = $workspace
    allowedRoots = @($workspace)
    capability = $Capability
    modelRoute = $plan.modelRoute
    tunnel = $plan.tunnelPlan.tunnel
    publicBaseUrl = $plan.tunnelPlan.publicBaseUrl
    browserAppUpdateExpected = $plan.tunnelPlan.browserAppUpdateExpected
    preparedAt = (Get-Date).ToString("o")
  }
  Write-JsonFileAtomic $session $SessionPath

  if ($Action -eq "Prepare") {
    Write-Json ([ordered]@{ status = "success"; action = "Prepare"; plan = $plan; configure = $configureRaw; sessionPath = $SessionPath })
    exit 0
  }

  $onRaw = Invoke-Controller @("-Action", "On", "-StateDir", $StateDir)
  $doctorRaw = Invoke-Controller @("-Action", "Doctor", "-StateDir", $StateDir)
  Write-Json ([ordered]@{
    status = "success"
    action = "Connect"
    plan = $plan
    configure = $configureRaw
    on = $onRaw
    doctor = $doctorRaw
    sessionPath = $SessionPath
    next = if ($plan.tunnelPlan.browserAppUpdateExpected) { "Use browser automation to create or update the ChatGPT App to the reported MCP URL, then complete the read-only smoke test." } else { "Reuse the existing ChatGPT App/OAuth connection and run a read-only smoke test." }
  })
} catch {
  Write-Json ([ordered]@{ status = "failed"; action = $Action; message = $_.Exception.Message })
  exit 1
}
