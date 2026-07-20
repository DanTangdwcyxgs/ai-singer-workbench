param(
    [Parameter(Mandatory = $true)]
    [string]$ApplioRoot,
    [string]$GPTSoVITSRoot = '',
    [int]$Port = 9875
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot

function Find-Root([string]$Candidate, [string]$Marker) {
    $resolved = (Resolve-Path -LiteralPath $Candidate).Path
    if (Test-Path -LiteralPath (Join-Path $resolved $Marker)) {
        return $resolved
    }
    $leaf = Split-Path -Leaf $Marker
    $match = Get-ChildItem -LiteralPath $resolved -Recurse -File -Filter $leaf -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName.EndsWith($Marker, [StringComparison]::OrdinalIgnoreCase) } |
        Select-Object -First 1
    if (-not $match) {
        throw "Cannot find $Marker under $resolved"
    }
    $root = $match.FullName.Substring(0, $match.FullName.Length - $Marker.Length).TrimEnd('\')
    return $root
}

$applio = Find-Root $ApplioRoot 'core.py'
$applioPython = Join-Path $applio 'env\python.exe'
if (-not (Test-Path -LiteralPath $applioPython)) {
    throw "Applio Python not found: $applioPython"
}

$gpt = ''
if ($GPTSoVITSRoot) {
    $gpt = Find-Root $GPTSoVITSRoot 'tools\uvr5\bsroformer.py'
    $gptPython = Join-Path $gpt 'runtime\python.exe'
    if (-not (Test-Path -LiteralPath $gptPython)) {
        throw "GPT-SoVITS Python not found: $gptPython"
    }
}

$config = [ordered]@{
    applio_root = $applio
    gpt_sovits_root = $gpt
    server_host = '127.0.0.1'
    server_port = $Port
    separator_model = 'model_bs_roformer_ep_317_sdr_12.9755.ckpt'
    device = '0'
}
$json = $config | ConvertTo-Json
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText((Join-Path $projectRoot 'config.json'), $json, $utf8NoBom)

foreach ($name in @('recordings', 'songs', 'separated', 'models', 'outputs', 'logs')) {
    New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot "data\$name") | Out-Null
}

Write-Host 'Configuration completed.' -ForegroundColor Green
Write-Host (Join-Path $projectRoot 'config.json')
Write-Host 'Run scripts\verify-windows.ps1 next.'
