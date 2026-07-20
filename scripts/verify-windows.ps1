param()

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $projectRoot 'config.json'

function Report([string]$Name, [bool]$Passed, [string]$Detail) {
    $color = if ($Passed) { 'Green' } else { 'Red' }
    $mark = if ($Passed) { '[PASS]' } else { '[FAIL]' }
    Write-Host "$mark $Name - $Detail" -ForegroundColor $color
    return $Passed
}

if (-not (Test-Path -LiteralPath $configPath)) {
    Write-Host '[FAIL] config.json is missing. Run configure-windows.ps1.' -ForegroundColor Red
    exit 1
}

$config = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
$results = @()
$applioPython = Join-Path $config.applio_root 'env\python.exe'
$core = Join-Path $config.applio_root 'core.py'
$ffmpegA = Join-Path $config.applio_root 'ffmpeg.exe'
$ffmpegB = Join-Path $config.applio_root 'env\Library\bin\ffmpeg.exe'
$results += Report 'Applio Python' (Test-Path -LiteralPath $applioPython) $applioPython
$results += Report 'Applio core' (Test-Path -LiteralPath $core) $core
$results += Report 'FFmpeg' ((Test-Path -LiteralPath $ffmpegA) -or (Test-Path -LiteralPath $ffmpegB)) $config.applio_root

if ($config.gpt_sovits_root) {
    $gptPython = Join-Path $config.gpt_sovits_root 'runtime\python.exe'
    $weight = Join-Path $config.gpt_sovits_root "tools\uvr5\uvr5_weights\$($config.separator_model)"
    $results += Report 'GPT-SoVITS Python' (Test-Path -LiteralPath $gptPython) $gptPython
    $results += Report 'BS-RoFormer model' (Test-Path -LiteralPath $weight) $weight
} else {
    Write-Host '[INFO] GPT-SoVITS is optional and not configured. Automatic song separation is disabled.' -ForegroundColor Yellow
}

try {
    $gpu = & nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>$null
    $results += Report 'NVIDIA GPU' ([bool]$gpu) ($gpu -join ', ')
} catch {
    $results += Report 'NVIDIA GPU' $false 'nvidia-smi was not available'
}

if ($results -contains $false) {
    exit 1
}
Write-Host 'All required checks passed.' -ForegroundColor Green
