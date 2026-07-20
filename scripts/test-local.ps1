param()

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = 'python'
if (Test-Path -LiteralPath (Join-Path $projectRoot 'config.json')) {
    $config = Get-Content -LiteralPath (Join-Path $projectRoot 'config.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $candidate = Join-Path $config.applio_root 'env\python.exe'
    if (Test-Path -LiteralPath $candidate) { $python = $candidate }
}

& $python -m compileall -q (Join-Path $projectRoot 'workbench') (Join-Path $projectRoot 'tests')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Push-Location $projectRoot
try {
    & $python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

$parseErrors = @()
Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.ps1' | ForEach-Object {
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($_.FullName, [ref]$tokens, [ref]$errors) | Out-Null
    $parseErrors += $errors
}
if ($parseErrors.Count) {
    $parseErrors | Format-List
    exit 1
}
Write-Host 'All local checks passed.' -ForegroundColor Green
