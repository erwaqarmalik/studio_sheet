$ErrorActionPreference = "Stop"

# PowerShell helper to run fresh_install.sh on the droplet via SSH/SCP
# Requirements: OpenSSH client installed (ssh/scp available in PATH)

$HostIp = "165.22.214.244"
$User = "root"
$RemotePath = "/root/studio_sheet/deploy_files/fresh_install.sh"
$LocalScript = Join-Path $PSScriptRoot "fresh_install.sh"

if (-not (Test-Path $LocalScript)) {
	throw "Missing $LocalScript. Make sure deploy_files/fresh_install.sh exists."
}

Write-Host "Uploading fresh install script to $User@$HostIp..."
& scp $LocalScript "${User}@${HostIp}:${RemotePath}"

Write-Host "Running fresh install on droplet..."
& ssh "${User}@${HostIp}" "chmod +x $RemotePath; bash $RemotePath"

Write-Host "Done. Edit /root/studio_sheet/.env on the droplet to set SECRET_KEY + DB_PASSWORD."
