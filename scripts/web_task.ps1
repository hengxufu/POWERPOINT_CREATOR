param(
  [Parameter(Mandatory=$true)][ValidateSet('ReadTask','Submit','Download')][string]$Action,
  [ValidatePattern('^[a-zA-Z0-9_-]+$')][string]$Session = 'ppt-edge-isolated',
  [Parameter(Mandatory=$true)][string]$Job,
  [string]$SessionUrl,
  [string]$DownloadButton = ([string][char]0x4E0B + [char]0x8F7D),
  [string]$OutputFile
)
$ErrorActionPreference = 'Stop'
$jobDir = (Resolve-Path -LiteralPath $Job).Path
$data = Get-Content -LiteralPath (Join-Path $jobDir 'job.json') -Raw -Encoding utf8 | ConvertFrom-Json
$codeFile = Join-Path $jobDir 'ui-action.js'
$resultFile = Join-Path $jobDir ('ui-' + $Action.ToLower() + '-result.txt')
switch ($Action) {
  'ReadTask' {
    $code = "async page => ({url: page.url(), text: await page.locator('main').last().innerText()})"
  }
  'Submit' {
    if ($SessionUrl -notmatch '^https://chatgpt\.com/c/[A-Za-z0-9_-]+$') { throw 'Provide the observed task conversation URL.' }
    $intent = Join-Path $jobDir 'dispatch-intent.json'
    if ((Test-Path -LiteralPath $intent) -or ($data.history.status -contains 'submitted') -or ($data.history.status -contains 'submission_unknown')) {
      throw 'Already dispatched or outcome uncertain. Inspect the original web conversation; do not resend.'
    }
    # .NET read returns a plain string; PowerShell 5.1 Get-Content strings can
    # carry provider metadata which ConvertTo-Json serializes as an object.
    $promptPlain = [IO.File]::ReadAllText((Join-Path $jobDir 'prompt.txt'),[Text.Encoding]::UTF8)
    $literal = ConvertTo-Json -InputObject $promptPlain -Compress
    $urlLiteral = ConvertTo-Json -InputObject $SessionUrl -Compress
    $code = "async page => { if (page.url() !== $urlLiteral) throw new Error('Wrong task conversation'); const box = page.getByRole('textbox', {name: '\u8be2\u95ee ChatGPT', exact: true}); await box.fill($literal); await box.press('Enter'); return {url:page.url(), dispatched:true}; }"
    # Durable marker before sending: even a process crash must not trigger a duplicate.
    @{at=[DateTime]::UtcNow.ToString('o');session=$Session;url=$SessionUrl;state='dispatch_intent'} | ConvertTo-Json | Set-Content -LiteralPath $intent -Encoding utf8
  }
  'Download' {
    if (-not $OutputFile) { throw 'OutputFile is required.' }
    $target = [IO.Path]::GetFullPath($OutputFile)
    if (-not $target.StartsWith($jobDir + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Download must stay inside the job directory.' }
    if (Test-Path -LiteralPath $target) { throw 'Do not overwrite an existing asset.' }
    $pathLiteral = ConvertTo-Json -InputObject $target -Compress
    $buttonLiteral = ConvertTo-Json -InputObject $DownloadButton -Compress
    $code = "async page => { const button = page.getByRole('dialog').getByRole('button', {name:$buttonLiteral,exact:true}); if (await button.count() !== 1) throw new Error('Download button is ambiguous; inspect the visible image first'); const pending = page.waitForEvent('download',{timeout:30000}); await button.click(); const download = await pending; await download.saveAs($pathLiteral); return {path:$pathLiteral, suggestedFilename:download.suggestedFilename()}; }"
  }
}
Set-Content -LiteralPath $codeFile -Value $code -Encoding utf8
$cliArgs = @('--yes','--package','@playwright/cli@0.1.22','playwright-cli',"-s=$Session",'run-code','--filename',$codeFile)
$output = & npx.cmd @cliArgs 2>&1
$exitCode = $LASTEXITCODE
$output | Set-Content -LiteralPath $resultFile -Encoding utf8
$output | Write-Output
if ($exitCode -ne 0) { throw "UI operation failed; inspect $resultFile. Do not automatically resend." }
if ($Action -eq 'ReadTask') {
  $joined = $output -join "`n"
  $match = [regex]::Match($joined,'### Result\s*\r?\n([^\r\n]+)')
  if (-not $match.Success) { throw 'No structured CLI result.' }
  $result = $match.Groups[1].Value | ConvertFrom-Json
  $result.text | Set-Content -LiteralPath (Join-Path $jobDir 'task-text.txt') -Encoding utf8
}
# This helper only handles visible UI. Record state with asset_job.py after checking
# the displayed result; download still requires receive + visual review.
