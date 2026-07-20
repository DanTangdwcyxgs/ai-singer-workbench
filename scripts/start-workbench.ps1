param(
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $projectRoot 'config.json'
$appScript = Join-Path $projectRoot 'workbench\app.py'
$logDir = Join-Path $projectRoot 'runtime-logs'

if (-not (Test-Path -LiteralPath $configPath)) {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show('Run scripts\configure-windows.ps1 first.', 'AI Singer Workbench', 'OK', 'Error') | Out-Null
    exit 1
}
$config = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
$python = Join-Path $config.applio_root 'env\python.exe'
$url = "http://$($config.server_host):$($config.server_port)/"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

try {
    $ready = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 2
    if ($ready.StatusCode -eq 200) {
        if (-not $NoBrowser) { Start-Process $url }
        exit 0
    }
} catch {}

$stdout = Join-Path $logDir 'workbench-out.log'
$stderr = Join-Path $logDir 'workbench-error.log'
$arguments = '"{0}" --config "{1}" --no-browser' -f $appScript, $configPath
Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory (Split-Path $appScript) -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr | Out-Null

$started = $false
for ($i = 0; $i -lt 45; $i++) {
    Start-Sleep -Seconds 1
    try {
        $ready = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 2
        if ($ready.StatusCode -eq 200) { $started = $true; break }
    } catch {}
}
if (-not $started) {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show("Startup failed. Check $stderr", 'AI Singer Workbench', 'OK', 'Error') | Out-Null
    exit 1
}
if (-not $NoBrowser) { Start-Process $url }
