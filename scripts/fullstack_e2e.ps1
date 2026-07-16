# Full-stack integration E2E: start backend Compose stack, poll health, run Playwright integration tests.
#
# Usage (from repo root):
#   .\scripts\fullstack_e2e.ps1

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ComposeDir = Join-Path $RepoRoot "backend\docker"
$BackendUrl = if ($env:BACKEND_API_URL) { $env:BACKEND_API_URL } else { "http://localhost:8000" }
$HealthUrl = "$($BackendUrl.TrimEnd('/'))/health"

Write-Host "== bringing up api, worker, redis, postgres =="
Push-Location $ComposeDir
try {
    docker compose up --build -d api worker redis postgres
} finally {
    Pop-Location
}

Write-Host "== waiting for API health =="
$ready = $false
for ($i = 1; $i -le 60; $i++) {
    try {
        $response = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {
        # retry
    }
    Start-Sleep -Seconds 2
}

if (-not $ready) {
    Write-Error "health never returned 200 at $HealthUrl"
}

Write-Host "PASS  health 200"

Write-Host "== running Playwright integration tests =="
Push-Location (Join-Path $RepoRoot "frontend")
try {
    npm run test:integration
} finally {
    Pop-Location
}
