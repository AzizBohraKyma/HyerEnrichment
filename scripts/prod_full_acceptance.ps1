#Requires -Version 5.1
param(
    [ValidateSet("--local", "--prod")]
    [string]$Mode = "--local"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot "backend"
$ResultsDir = Join-Path $BackendDir ".e2e-results"
$Report = Join-Path $ResultsDir "prod-acceptance-report.json"
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null

$Failures = 0
$Started = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

function Run-Step($Name, [scriptblock]$Block) {
    Write-Host "== $Name =="
    try {
        & $Block
        Write-Host "PASS  $Name"
    } catch {
        Write-Host "FAIL  $Name" -ForegroundColor Red
        $script:Failures++
    }
}

if ($Mode -eq "--local") {
    if (-not $env:BASE_URL) { $env:BASE_URL = "http://127.0.0.1:8000" }
    if (-not $env:API_TOKEN) { $env:API_TOKEN = "change-me" }
    $E2eMode = "--ci"
    $RunFullstack = $true
} else {
    if (-not $env:BASE_URL -or -not $env:API_TOKEN) {
        throw "BASE_URL and API_TOKEN are required for --prod"
    }
    $env:SMOKE_PROD = "1"
    $E2eMode = if ($env:E2E_MODE) { $env:E2E_MODE } else { "--live" }
    $RunFullstack = $false
}

Push-Location $RepoRoot
try {
    if ($Mode -eq "--local") {
        Run-Step "setup" { wsl make setup }
        Run-Step "compose_up" { wsl make up }
        Run-Step "wait_ready" {
            $ready = $false
            for ($i = 0; $i -lt 60; $i++) {
                try {
                    $r = Invoke-WebRequest -Uri "$($env:BASE_URL)/ready" -TimeoutSec 5 -UseBasicParsing
                    if ($r.StatusCode -eq 200) { $ready = $true; break }
                } catch {}
                Start-Sleep -Seconds 2
            }
            if (-not $ready) { throw "/ready not ready" }
        }
    }

    Run-Step "smoke_prod" { wsl env BASE_URL=$env:BASE_URL API_TOKEN=$env:API_TOKEN SMOKE_PROD=$env:SMOKE_PROD make smoke-prod }
    Run-Step "boundary_checks" { wsl make boundary-checks }

    $FullPath = Join-Path $BackendDir "scripts/e2e_full_path.sh"
    if (Test-Path $FullPath) {
        Run-Step "full_path_e2e" { wsl bash "backend/scripts/e2e_full_path.sh" $E2eMode }
    }

    if ($RunFullstack -and (Test-Path (Join-Path $RepoRoot "scripts/fullstack_e2e.sh"))) {
        Run-Step "frontend_integration" { wsl bash scripts/fullstack_e2e.sh }
    }
} finally {
    Pop-Location
}

$Completed = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$Status = if ($Failures -eq 0) { "pass" } else { "fail" }
@{
    mode = $Mode
    base_url = $env:BASE_URL
    started_at = $Started
    completed_at = $Completed
    failures = $Failures
    status = $Status
} | ConvertTo-Json | Set-Content -Path $Report -Encoding UTF8

Write-Host "report: $Report"
if ($Failures -ne 0) { exit 1 }
Write-Host "prod full acceptance ok"
