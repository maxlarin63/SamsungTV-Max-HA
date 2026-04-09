# Deploy Samsung TV Max to Home Assistant via scp (Windows).
# Usage: from repo root, run the VS Code task "Deploy to HA" or call directly.

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvFile  = Join-Path $RepoRoot ".env.ha"

if (-not (Test-Path $EnvFile)) {
    Write-Error "ERROR: .env.ha not found. Copy .env.ha.example and fill in your values."
    exit 1
}

# Load .env.ha
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([A-Z_]+)\s*=\s*(.+)$') {
        [System.Environment]::SetEnvironmentVariable($Matches[1], $Matches[2].Trim(), "Process")
    }
}

$HA_HOST = $env:HA_HOST
$HA_USER = if ($env:HA_USER) { $env:HA_USER } else { "root" }

if (-not $HA_HOST) { Write-Error "HA_HOST must be set in .env.ha"; exit 1 }

# SSH identity
$DefaultKey = Join-Path $env:USERPROFILE ".ssh\ha_deploy"
$HA_SSH_IDENTITY = if ($env:HA_SSH_IDENTITY) { $env:HA_SSH_IDENTITY } `
                   elseif (Test-Path $DefaultKey)   { $DefaultKey }         `
                   else                             { $null }

$SshOpts = @("-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes")
if ($HA_SSH_IDENTITY) { $SshOpts += @("-i", $HA_SSH_IDENTITY) }

$Src = Join-Path $RepoRoot "custom_components\samsungtv_max"
$Dst = "${HA_USER}@${HA_HOST}:/config/custom_components/"

$ManifestPath = Join-Path $Src "manifest.json"
$Version = (Get-Content $ManifestPath | ConvertFrom-Json).version
Write-Host "→ Deploying samsungtv_max v$Version to ${HA_USER}@${HA_HOST}"

# Ensure remote directory exists
& ssh @SshOpts "${HA_USER}@${HA_HOST}" "mkdir -p /config/custom_components/samsungtv_max"

# Deploy with scp -r (excludes handled by .scpignore workaround — just copy the folder)
& scp @SshOpts -r $Src "${Dst}"

if ($LASTEXITCODE -ne 0) { Write-Error "scp failed."; exit 1 }
Write-Host "✓ Deploy complete."

# Optional restart
if ($env:HA_HTTP_URL -and $env:HA_TOKEN) {
    Write-Host "→ Restarting Home Assistant..."
    $headers = @{ "Authorization" = "Bearer $($env:HA_TOKEN)"; "Content-Type" = "application/json" }
    Invoke-RestMethod -Uri "$($env:HA_HTTP_URL)/api/services/homeassistant/restart" `
                      -Method POST -Headers $headers -Body "{}" | Out-Null
    Write-Host "✓ Restart triggered."
}
