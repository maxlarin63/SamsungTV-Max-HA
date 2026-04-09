# Deploy using rsync from WSL (Windows) — requires rsync on the HA SSH server.
# Bootstraps WSL SSH key via deploy-ha-wsl-bootstrap.sh on first run.

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvFile  = Join-Path $RepoRoot ".env.ha"

if (-not (Test-Path $EnvFile)) {
    Write-Error ".env.ha not found."
    exit 1
}

# Bootstrap SSH key into WSL ~/.ssh if needed
$BootstrapScript = Join-Path $PSScriptRoot "deploy-ha-wsl-bootstrap.sh"
wsl bash (wsl wslpath -u $BootstrapScript)

# Run the rsync deploy script inside WSL
$RsyncScript = Join-Path $PSScriptRoot "deploy-ha-rsync.sh"
wsl bash (wsl wslpath -u $RsyncScript)
