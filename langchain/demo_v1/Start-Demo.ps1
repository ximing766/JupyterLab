param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000,
    [switch]$StopOnly
)

$ErrorActionPreference = "Stop"

$Root = $PSScriptRoot
$UiDir = Join-Path $Root "ui"
$LogDir = Join-Path $Root ".runtime_logs"

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

function Get-ListeningPids {
    param([int]$Port)
    $result = @()
    $lines = netstat -ano -p tcp | Select-String -Pattern "LISTENING"
    foreach ($line in $lines) {
        $text = $line.Line.Trim()
        if ($text -match "[:\.]$Port\s+.*LISTENING\s+(\d+)$") {
            $procId = [int]$Matches[1]
            if ($procId -gt 0 -and -not $result.Contains($procId)) {
                $result += $procId
            }
        }
    }
    return $result
}

function Stop-PortProcess {
    param([int]$Port, [string]$ServiceName)
    $pids = Get-ListeningPids -Port $Port
    if ($pids.Count -eq 0) {
        Write-Host "[$ServiceName] port $Port is free."
        return
    }
    foreach ($procId in $pids) {
        try {
            $proc = Get-Process -Id $procId -ErrorAction Stop
            Write-Host "[$ServiceName] killing PID $procId ($($proc.ProcessName)) on port $Port..."
            Stop-Process -Id $procId -Force -ErrorAction Stop
        } catch {
            Write-Host "[$ServiceName] failed to stop PID ${procId}: $($_.Exception.Message)"
        }
    }
    Start-Sleep -Milliseconds 1000
}

function Wait-HttpOk {
    param([string]$Url, [int]$TimeoutSec = 30)
    $start = Get-Date
    while (((Get-Date) - $start).TotalSeconds -lt $TimeoutSec) {
        try {
            $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
                return $true
            }
        } catch {
            Start-Sleep -Milliseconds 700
        }
    }
    return $false
}

Write-Host "== Demo launcher =="
Write-Host "Root: $Root"

Stop-PortProcess -Port $BackendPort -ServiceName "backend"
Stop-PortProcess -Port $FrontendPort -ServiceName "frontend"

if ($StopOnly) {
    Write-Host "Services stopped successfully."
    exit 0
}

$envFile = Join-Path $UiDir ".env.local"
$envContent = @(
    "NEXT_PUBLIC_AGENT_API_URL=http://127.0.0.1:$BackendPort"
)
Set-Content -Path $envFile -Value $envContent -Encoding UTF8
Write-Host "[frontend] wrote $envFile"

$backendLogOut = Join-Path $LogDir "backend.out.log"
$backendLogErr = Join-Path $LogDir "backend.err.log"
$frontendLogOut = Join-Path $LogDir "frontend.out.log"
$frontendLogErr = Join-Path $LogDir "frontend.err.log"
foreach ($f in @($backendLogOut, $backendLogErr, $frontendLogOut, $frontendLogErr)) {
    if (Test-Path $f) { Remove-Item $f -Force -ErrorAction SilentlyContinue }
}

$backendCmd = "`$env:PYTHONPATH='$Root'; Set-Location '$Root'; python -m uvicorn backend.server:app --host 127.0.0.1 --port $BackendPort"
$frontendCmd = "Set-Location '$UiDir'; npx next dev -p $FrontendPort"

$backendProc = Start-Process -FilePath "powershell" `
    -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $backendCmd) `
    -WindowStyle Hidden -RedirectStandardOutput $backendLogOut -RedirectStandardError $backendLogErr -PassThru

Write-Host "[backend] waiting for health check..."
if (-not (Wait-HttpOk -Url "http://127.0.0.1:$BackendPort/health" -TimeoutSec 15)) {
    Write-Host "--- Backend Error Log ---"
    Get-Content $backendLogErr | Write-Host
    throw "Backend failed to start."
}
Write-Host "[backend] health check ok."

$frontendProc = Start-Process -FilePath "powershell" `
    -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $frontendCmd) `
    -WindowStyle Hidden -RedirectStandardOutput $frontendLogOut -RedirectStandardError $frontendLogErr -PassThru

Write-Host "[frontend] waiting for ready check (may take 10-30s)..."
if (-not (Wait-HttpOk -Url "http://127.0.0.1:$FrontendPort" -TimeoutSec 60)) {
    Write-Host "--- Frontend Error Log ---"
    Get-Content $frontendLogErr | Write-Host
    throw "Frontend failed to start."
}
Write-Host "[frontend] ready check ok."

Write-Host "[backend] PID: $($backendProc.Id)"
Write-Host "[frontend] PID: $($frontendProc.Id)"
Write-Host "Opening browser: http://localhost:$FrontendPort"
Start-Process "http://localhost:$FrontendPort"

Write-Host ""
Write-Host "If you want to stop services:"
Write-Host "  powershell -ExecutionPolicy Bypass -File .\Start-Demo.ps1 -StopOnly"
