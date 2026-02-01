param(
    [string]$DropletIP = "165.22.214.244",
    [string]$DropletUser = "root"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Full Fresh Install on Droplet ===" -ForegroundColor Cyan

# Path to local bash script
$localScript = Join-Path (Split-Path $MyInvocation.MyCommand.Path) "full_fresh_install_remote.sh"

if (-not (Test-Path $localScript)) {
    Write-Host "ERROR: $localScript not found!" -ForegroundColor Red
    exit 1
}

Write-Host "Uploading install script to droplet..." -ForegroundColor Yellow

# Upload via SCP
& scp $localScript "${DropletUser}@${DropletIP}:/tmp/install.sh"

Write-Host "Executing on droplet..." -ForegroundColor Yellow

# Execute via SSH
& ssh "${DropletUser}@${DropletIP}" "chmod +x /tmp/install.sh; bash /tmp/install.sh; rm /tmp/install.sh"

Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "App is running at: http://${DropletIP}" -ForegroundColor Green
Write-Host ""
Write-Host "SSH to droplet to check status:" -ForegroundColor Cyan
Write-Host "  ssh ${DropletUser}@${DropletIP}" -ForegroundColor Gray
Write-Host ""
Write-Host "View logs:" -ForegroundColor Cyan
Write-Host "  systemctl status passport_app_gunicorn" -ForegroundColor Gray
Write-Host "  journalctl -xeu passport_app_gunicorn --no-pager" -ForegroundColor Gray


