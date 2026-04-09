# Deploy Samsung TV Max to Home Assistant via scp (Windows).
# Usage: from repo root, run the VS Code task "Deploy to HA" or call directly.

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$EnvFile  = Join-Path $RepoRoot ".env.ha"

if (-not (Test-Path -LiteralPath $EnvFile)) {
    Write-Error @"
.env.ha not found at $EnvFile
Copy .env.ha.example to .env.ha and fill in values.
"@
    exit 1
}

# Load .env.ha
Get-Content -LiteralPath $EnvFile | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) { return }
    $eq = $line.IndexOf("=")
    if ($eq -lt 1) { return }
    $name = $line.Substring(0, $eq).Trim()
    $val = $line.Substring($eq + 1).Trim()
    if (($val.StartsWith('"') -and $val.EndsWith('"')) -or ($val.StartsWith("'") -and $val.EndsWith("'"))) {
        $val = $val.Substring(1, $val.Length - 2)
    }
    Set-Item -Path "Env:$name" -Value $val
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
$TargetParent = "/config/custom_components/"
$Dst = "${HA_USER}@${HA_HOST}:${TargetParent}"

$ManifestPath = Join-Path $Src "manifest.json"
$Version = ""
if (Test-Path -LiteralPath $ManifestPath) {
    try {
        $Version = (Get-Content -Raw -LiteralPath $ManifestPath | ConvertFrom-Json).version
    } catch {
        $Version = ""
    }
}
$DestDisplay = "${HA_USER}@${HA_HOST}:${TargetParent}samsungtv_max/"
if ($Version) {
    Write-Host "Deploying Samsung TV Max v$Version to $DestDisplay"
} else {
    Write-Host "Deploying Samsung TV Max to $DestDisplay"
}

# Ensure remote directory exists
& ssh @SshOpts "${HA_USER}@${HA_HOST}" "mkdir -p /config/custom_components/samsungtv_max"

# Stage and deploy (avoid copying __pycache__/pyc, caches, etc.)
$StageRoot = Join-Path $env:TEMP ("ha_scp_stage_" + [Guid]::NewGuid().ToString("N"))
$StagePkg = Join-Path $StageRoot "samsungtv_max"
try {
    New-Item -ItemType Directory -Path $StagePkg -Force | Out-Null
    $null = robocopy $Src $StagePkg /E `
        /XD __pycache__ .pytest_cache .mypy_cache .ruff_cache `
        /XF *.pyc `
        /NFL /NDL /NJH /NJS /NC /NS /NP
    $RobocopyRc = $LASTEXITCODE
    if ($RobocopyRc -ge 8) {
        Write-Error "Staging file copy failed (robocopy exit $RobocopyRc)."
        exit 1
    }

    & scp @SshOpts -r $StagePkg "${Dst}"
}
finally {
    Remove-Item -LiteralPath $StageRoot -Recurse -Force -ErrorAction SilentlyContinue
}

if ($LASTEXITCODE -ne 0) { Write-Error "scp failed."; exit 1 }
Write-Host "OK: Deploy complete."

# Optional restart
$HA_HTTP_URL = $env:HA_HTTP_URL
$HA_TOKEN = $env:HA_TOKEN
if ($HA_HTTP_URL -and $HA_TOKEN) {
    $HA_HTTP_URL = $HA_HTTP_URL.TrimEnd("/")
    $Uri = "$HA_HTTP_URL/api/services/homeassistant/restart"
    $headers = @{
        Authorization = "Bearer $HA_TOKEN"
        "Content-Type" = "application/json"
    }

    try {
        Write-Host "Restarting Home Assistant Core via $Uri ..."
        Invoke-RestMethod -Uri $Uri -Method POST -Headers $headers -Body "{}" | Out-Null
        Write-Host "OK: Restart requested."
    } catch {
        $httpCode = $null
        if ($_.Exception.Response) {
            $httpCode = [int]$_.Exception.Response.StatusCode
        }
        $msg = $_.Exception.Message
        $benign = ($httpCode -eq 504 -or $httpCode -eq 502) -or
            ($msg -match "504|502|Gateway Timeout|Bad Gateway|forcibly closed|Connection reset|underlying connection")
        if ($benign) {
            Write-Host "Restart likely started (HA or proxy closed the request while restarting). Give it a minute."
        } else {
            Write-Warning "Deploy succeeded but HA restart failed: $msg. Edit HA_HTTP_URL / HA_TOKEN in .env.ha or restart manually."
            exit 1
        }
    }
} elseif ($HA_HTTP_URL -or $HA_TOKEN) {
    Write-Warning "Set both HA_HTTP_URL and HA_TOKEN in .env.ha for automatic restart after deploy."
}
