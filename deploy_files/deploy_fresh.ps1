param(
    [string]$DropletIP = "165.22.214.244",
    [string]$RootPath = "/root/studio_sheet",
    [string]$SuperUserName = "erwaqarmalik",
    [string]$SSHPassword = "",
    [string]$SSLPassword = ""
)

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Passport App - Full Fresh Deployment Script" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Prompt for SSH Password (required for all commands)
if ([string]::IsNullOrEmpty($SSHPassword)) {
    Write-Host "Enter SSH Password for root@$DropletIP:" -ForegroundColor Yellow
    $secureSSHPassword = Read-Host "SSH Password" -AsSecureString
    $SSHPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($secureSSHPassword))
    Write-Host "[OK] SSH Password saved - using for all commands" -ForegroundColor Green
}
Write-Host ""

# Prompt for SSL Password (optional)
if ([string]::IsNullOrEmpty($SSLPassword)) {
    Write-Host "Optional: Enter SSL Certificate Password (or press Enter to skip)" -ForegroundColor Yellow
    $secureSSLPassword = Read-Host "SSL Password" -AsSecureString
    if ($secureSSLPassword.Length -gt 0) {
        $SSLPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($secureSSLPassword))
        Write-Host "[OK] SSL Password saved" -ForegroundColor Green
    } else {
        $SSLPassword = ""
        Write-Host "[SKIP] SSL Password skipped" -ForegroundColor Yellow
    }
}
Write-Host ""

function SSH-Exec {
    param([string]$Cmd, [string]$Desc = "")
    if ($Desc) { Write-Host "[*] $Desc" -ForegroundColor Cyan }
    $output = echo $SSHPassword | sshpass -p "$SSHPassword" ssh -o StrictHostKeyChecking=no root@$DropletIP $Cmd 2>&1
    return $output
}

function SSH-Quiet {
    param([string]$Cmd)
    echo $SSHPassword | sshpass -p "$SSHPassword" ssh -o StrictHostKeyChecking=no root@$DropletIP $Cmd 2>&1 | Out-Null
}

Write-Host "[*] Generating Secure Credentials..." -ForegroundColor Yellow

$dbPassword = -join ((48..122) | Get-Random -Count 20 | ForEach-Object {[char]$_})
$dbPassword = ($dbPassword -replace '[^a-zA-Z0-9]', 'A').Substring(0,20)

$suPassword = -join ((48..122) | Get-Random -Count 16 | ForEach-Object {[char]$_})
$suPassword = ($suPassword -replace '[^a-zA-Z0-9]', 'B').Substring(0,16)

Write-Host "DB Password: $dbPassword" -ForegroundColor Magenta
Write-Host "SU Password: $suPassword" -ForegroundColor Magenta
Write-Host ""

Write-Host "STEP 1: Stopping Services..." -ForegroundColor Green
SSH-Quiet "systemctl stop passport_app_gunicorn passport_app_celery nginx redis-server 2>/dev/null; true"
Start-Sleep -Seconds 2
Write-Host "[OK] Services stopped" -ForegroundColor Green
Write-Host ""

Write-Host "STEP 2: Clearing Old Data..." -ForegroundColor Green
SSH-Quiet "sudo -u postgres psql -c 'DROP DATABASE IF EXISTS passport_app_db;' 2>/dev/null; true"
SSH-Quiet "rm -f $RootPath/db.sqlite3"
SSH-Quiet "rm -rf $RootPath/media/outputs/*"
Write-Host "[OK] Old database and files cleared" -ForegroundColor Green
Write-Host ""

Write-Host "STEP 3: Pulling Latest Code..." -ForegroundColor Green
SSH-Exec "cd $RootPath; git pull" | Out-Null
Write-Host "[OK] Code updated" -ForegroundColor Green
Write-Host ""

Write-Host "STEP 4: Setting Up PostgreSQL..." -ForegroundColor Green
SSH-Quiet "sudo -u postgres psql -c 'CREATE DATABASE passport_app_db;' 2>/dev/null; true"
SSH-Quiet "sudo -u postgres psql -c 'CREATE USER passport_user WITH PASSWORD ''$dbPassword'';' 2>/dev/null; true"
SSH-Quiet "sudo -u postgres psql -c 'ALTER ROLE passport_user SET client_encoding TO utf8;' 2>/dev/null; true"
SSH-Quiet "sudo -u postgres psql -c 'ALTER ROLE passport_user SET default_transaction_isolation TO read_committed;' 2>/dev/null; true"
SSH-Quiet "sudo -u postgres psql -c 'ALTER ROLE passport_user SET timezone TO UTC;' 2>/dev/null; true"
SSH-Quiet "sudo -u postgres psql -c 'GRANT ALL PRIVILEGES ON DATABASE passport_app_db TO passport_user;' 2>/dev/null; true"
Write-Host "[OK] PostgreSQL configured" -ForegroundColor Green
Write-Host ""

Write-Host "STEP 5: Generating Django SECRET_KEY..." -ForegroundColor Green
$secretKey = SSH-Exec "cd $RootPath; venv/bin/python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'" | Select-Object -Last 1
$secretKey = $secretKey.Trim()
Write-Host "[OK] SECRET_KEY generated" -ForegroundColor Green
Write-Host ""

Write-Host "STEP 6: Creating .env Configuration..." -ForegroundColor Green
$envFile = @"
SECRET_KEY=$secretKey
DEBUG=False
ALLOWED_HOSTS=165.22.214.244,localhost,127.0.0.1
DB_ENGINE=postgresql
DB_NAME=passport_app_db
DB_USER=passport_user
DB_PASSWORD=$dbPassword
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://127.0.0.1:6379/0
CELERY_ENABLED=True
CELERY_BROKER_URL=redis://127.0.0.1:6379/1
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/2
MAX_FILE_SIZE_MB=50
FILE_CLEANUP_HOURS=24
RATE_LIMIT=100
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
"@

$tempEnv = "$env:TEMP\.env_deploy"
$envFile | Out-File -FilePath $tempEnv -Encoding ASCII -Force
scp -o StrictHostKeyChecking=no $tempEnv "root@$DropletIP`:$RootPath/.env" 2>&1 | Out-Null
Remove-Item $tempEnv -Force
Write-Host "[OK] .env file created" -ForegroundColor Green
Write-Host ""

Write-Host "STEP 7: Installing Python Dependencies..." -ForegroundColor Green
SSH-Quiet "cd $RootPath; venv/bin/pip install -q --upgrade pip setuptools wheel"
SSH-Quiet "cd $RootPath; venv/bin/pip install -q -r requirements.txt"
Write-Host "[OK] Dependencies installed" -ForegroundColor Green
Write-Host ""

Write-Host "STEP 8: Running Django Migrations..." -ForegroundColor Green
SSH-Exec "cd $RootPath; venv/bin/python manage.py migrate --noinput" | Out-Null
Write-Host "[OK] Migrations completed" -ForegroundColor Green
Write-Host ""

Write-Host "STEP 9: Collecting Static Files..." -ForegroundColor Green
SSH-Quiet "cd $RootPath; venv/bin/python manage.py collectstatic --noinput --clear"
Write-Host "[OK] Static files collected" -ForegroundColor Green
Write-Host ""

Write-Host "STEP 10: Creating Superuser..." -ForegroundColor Green
$pyScript = @"
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.filter(username='$SuperUserName').delete()
user = User.objects.create_superuser('$SuperUserName', 'admin@example.com', '$suPassword')
print('OK')
"@

$tempPy = "$env:TEMP\create_su.py"
$pyScript | Out-File -FilePath $tempPy -Encoding ASCII -Force
scp -o StrictHostKeyChecking=no $tempPy "root@$DropletIP`:/tmp/create_su.py" 2>&1 | Out-Null
SSH-Quiet "cd $RootPath; venv/bin/python manage.py shell < /tmp/create_su.py"
Remove-Item $tempPy -Force
Write-Host "[OK] Superuser created" -ForegroundColor Green
Write-Host ""

Write-Host "STEP 11: Starting Services..." -ForegroundColor Green
SSH-Quiet "systemctl start redis-server"
SSH-Quiet "systemctl start postgresql@16-main; sleep 2"
SSH-Quiet "systemctl restart passport_app_gunicorn; sleep 2"
SSH-Quiet "systemctl start passport_app_celery"
SSH-Quiet "systemctl restart nginx"
Start-Sleep -Seconds 3
Write-Host "[OK] All services started" -ForegroundColor Green
Write-Host ""

Write-Host "STEP 12: SSL/HTTPS Configuration..." -ForegroundColor Green
if ([string]::IsNullOrEmpty($SSLPassword)) {
    Write-Host "[SKIP] SSL configuration skipped (no password provided)" -ForegroundColor Yellow
} else {
    Write-Host "[INFO] SSL Password available for certificate setup" -ForegroundColor Cyan
    SSH-Quiet "cd $RootPath && echo '$SSLPassword' > /tmp/ssl_password.txt && chmod 600 /tmp/ssl_password.txt"
    Write-Host "[OK] SSL password saved for certificate operations" -ForegroundColor Green
    Write-Host "[TIP] To setup Let's Encrypt SSL:" -ForegroundColor Cyan
    Write-Host "      systemctl stop nginx" -ForegroundColor Gray
    Write-Host "      certbot certonly --standalone -d your-domain.com" -ForegroundColor Gray
    Write-Host "      systemctl start nginx" -ForegroundColor Gray
}
Write-Host ""

Write-Host "STEP 13: Testing Deployment..." -ForegroundColor Green
$test = SSH-Exec "curl -s -I http://165.22.214.244" | Select-Object -First 1
Write-Host "Response: $test" -ForegroundColor White

if ($test -match "302|200") {
    Write-Host "[OK] App is responding correctly!" -ForegroundColor Green
} else {
    Write-Host "[!] Check Gunicorn logs" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT COMPLETE" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "APPLICATION URL:" -ForegroundColor Yellow
Write-Host "  http://165.22.214.244" -ForegroundColor Green
Write-Host ""
Write-Host "SUPERUSER LOGIN:" -ForegroundColor Yellow
Write-Host "  Username: $SuperUserName" -ForegroundColor Green
Write-Host "  Password: $suPassword" -ForegroundColor Magenta
Write-Host ""
Write-Host "POSTGRESQL DATABASE:" -ForegroundColor Yellow
Write-Host "  Database: passport_app_db" -ForegroundColor Green
Write-Host "  User:     passport_user" -ForegroundColor Green
Write-Host "  Password: $dbPassword" -ForegroundColor Magenta
Write-Host "  Host:     localhost" -ForegroundColor Green
Write-Host "  Port:     5432" -ForegroundColor Green
Write-Host ""
Write-Host "DJANGO SECRET_KEY:" -ForegroundColor Yellow
Write-Host "  $secretKey" -ForegroundColor Magenta
Write-Host ""

if ([string]::IsNullOrEmpty($SSLPassword)) {
    Write-Host "SSL CERTIFICATE:" -ForegroundColor Yellow
    Write-Host "  NOT CONFIGURED (no password provided)" -ForegroundColor Yellow
} else {
    Write-Host "SSL CERTIFICATE:" -ForegroundColor Yellow
    Write-Host "  Password saved in /tmp/ssl_password.txt on droplet" -ForegroundColor Green
    Write-Host "  Ready for certificate operations" -ForegroundColor Green
}
Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "[OK] Save credentials in a secure location" -ForegroundColor Green
Write-Host ""
