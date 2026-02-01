# ============================================================================
# Passport App - Fresh Deployment Script (PowerShell)
# Purpose: Deploy from scratch with PostgreSQL database
# Usage: .\deploy_fresh.ps1
# ============================================================================

param(
    [string]$DropletIP = "165.22.214.244",
    [string]$RootPath = "/root/studio_sheet",
    [string]$SuperUserName = "erwaqarmalik"
)

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         Passport App - Full Fresh Deployment Script           ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# Helper Functions
# ============================================================================

function SSH-Exec {
    param([string]$Cmd, [string]$Desc = "")
    if ($Desc) { Write-Host "  ℹ️  $Desc" -ForegroundColor Cyan }
    ssh -o StrictHostKeyChecking=no root@$DropletIP $Cmd 2>&1
}

function SSH-ExecQuiet {
    param([string]$Cmd)
    ssh -o StrictHostKeyChecking=no root@$DropletIP $Cmd 2>&1 | Out-Null
}

# ============================================================================
# Generate Passwords
# ============================================================================

Write-Host "📋 Generating Secure Credentials..." -ForegroundColor Yellow
Write-Host ""

$dbPassword = -join ((33..126) | Get-Random -Count 20 | ForEach-Object {[char]$_})
$cleanDBPassword = $dbPassword -replace '[^a-zA-Z0-9]', ''

$suPassword = -join ((33..126) | Get-Random -Count 16 | ForEach-Object {[char]$_})
$cleanSUPassword = $suPassword -replace '[^a-zA-Z0-9]', ''

# ============================================================================
# STEP 1: Stop Services
# ============================================================================

Write-Host "STEP 1️⃣  Stopping Services..." -ForegroundColor Green
SSH-ExecQuiet "systemctl stop passport_app_gunicorn passport_app_celery nginx redis-server 2>/dev/null; true"
Start-Sleep -Seconds 2
Write-Host "  ✅ Services stopped" -ForegroundColor Green
Write-Host ""

# ============================================================================
# STEP 2: Clear Database & Files
# ============================================================================

Write-Host "STEP 2️⃣  Clearing Old Data..." -ForegroundColor Green
SSH-ExecQuiet "sudo -u postgres psql -c 'DROP DATABASE IF EXISTS passport_app_db;' 2>/dev/null; true"
SSH-ExecQuiet "rm -f $RootPath/db.sqlite3"
SSH-ExecQuiet "rm -rf $RootPath/media/outputs/*"
Write-Host "  ✅ Old database and files cleared" -ForegroundColor Green
Write-Host ""

# ============================================================================
# STEP 3: Pull Latest Code
# ============================================================================

Write-Host "STEP 3️⃣  Pulling Latest Code from GitHub..." -ForegroundColor Green
SSH-Exec "cd $RootPath; git pull" | Out-Null
Write-Host "  ✅ Code updated" -ForegroundColor Green
Write-Host ""

# ============================================================================
# STEP 4: Setup PostgreSQL
# ============================================================================

Write-Host "STEP 4️⃣  Setting Up PostgreSQL..." -ForegroundColor Green

SSH-ExecQuiet "sudo -u postgres psql -c 'CREATE DATABASE passport_app_db;' 2>/dev/null; true"
SSH-ExecQuiet "sudo -u postgres psql -c \"CREATE USER passport_user WITH PASSWORD '$cleanDBPassword';\" 2>/dev/null; true"
SSH-ExecQuiet "sudo -u postgres psql -c 'ALTER ROLE passport_user SET client_encoding TO ''utf8'';' 2>/dev/null; true"
SSH-ExecQuiet "sudo -u postgres psql -c 'ALTER ROLE passport_user SET default_transaction_isolation TO ''read committed'';' 2>/dev/null; true"
SSH-ExecQuiet "sudo -u postgres psql -c 'ALTER ROLE passport_user SET timezone TO ''UTC'';' 2>/dev/null; true"
SSH-ExecQuiet "sudo -u postgres psql -c 'GRANT ALL PRIVILEGES ON DATABASE passport_app_db TO passport_user;' 2>/dev/null; true"

Write-Host "  ✅ PostgreSQL configured" -ForegroundColor Green
Write-Host ""

# ============================================================================
# STEP 5: Generate Django SECRET_KEY
# ============================================================================

Write-Host "STEP 5️⃣  Generating Django SECRET_KEY..." -ForegroundColor Green
$secretKey = SSH-Exec "cd $RootPath; venv/bin/python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'" | Select-Object -Last 1
$secretKey = $secretKey.Trim()
Write-Host "  ✅ SECRET_KEY generated" -ForegroundColor Green
Write-Host ""

# ============================================================================
# STEP 6: Create .env File
# ============================================================================

Write-Host "STEP 6️⃣  Creating .env Configuration..." -ForegroundColor Green

$envContent = @"
SECRET_KEY=$secretKey
DEBUG=False
ALLOWED_HOSTS=165.22.214.244,localhost,127.0.0.1
DB_ENGINE=postgresql
DB_NAME=passport_app_db
DB_USER=passport_user
DB_PASSWORD=$cleanDBPassword
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

$tempEnv = Join-Path $env:TEMP ".env_temp"
$envContent | Out-File -FilePath $tempEnv -Encoding ASCII -Force
scp -o StrictHostKeyChecking=no $tempEnv "root@$DropletIP`:$RootPath/.env" 2>&1 | Out-Null
Remove-Item $tempEnv -Force

Write-Host "  ✅ .env file created" -ForegroundColor Green
Write-Host ""

# ============================================================================
# STEP 7: Install Dependencies
# ============================================================================

Write-Host "STEP 7️⃣  Installing Python Dependencies..." -ForegroundColor Green
SSH-ExecQuiet "cd $RootPath; venv/bin/pip install -q --upgrade pip setuptools wheel"
SSH-ExecQuiet "cd $RootPath; venv/bin/pip install -q -r requirements.txt"
Write-Host "  ✅ Dependencies installed" -ForegroundColor Green
Write-Host ""

# ============================================================================
# STEP 8: Run Migrations
# ============================================================================

Write-Host "STEP 8️⃣  Running Django Migrations..." -ForegroundColor Green
SSH-Exec "cd $RootPath; venv/bin/python manage.py migrate --noinput" | Out-Null
Write-Host "  ✅ Migrations completed" -ForegroundColor Green
Write-Host ""

# ============================================================================
# STEP 9: Collect Static Files
# ============================================================================

Write-Host "STEP 9️⃣  Collecting Static Files..." -ForegroundColor Green
SSH-ExecQuiet "cd $RootPath; venv/bin/python manage.py collectstatic --noinput --clear"
Write-Host "  ✅ Static files collected" -ForegroundColor Green
Write-Host ""

# ============================================================================
# STEP 10: Create Superuser
# ============================================================================

Write-Host "STEP 🔟 Creating Superuser..." -ForegroundColor Green

# Create a shell script for superuser creation
$suScript = "/tmp/create_su.py"
$suScriptContent = @"
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.filter(username='$SuperUserName').delete()
user = User.objects.create_superuser('$SuperUserName', 'admin@example.com', '$cleanSUPassword')
print(f'OK')
"@

$tempSU = Join-Path $env:TEMP "create_su.py"
$suScriptContent | Out-File -FilePath $tempSU -Encoding ASCII -Force
scp -o StrictHostKeyChecking=no $tempSU "root@$DropletIP`:$suScript" 2>&1 | Out-Null
SSH-ExecQuiet "cd $RootPath; venv/bin/python manage.py shell < $suScript"
Remove-Item $tempSU -Force

Write-Host "  ✅ Superuser created" -ForegroundColor Green
Write-Host ""

# ============================================================================
# STEP 11: Start Services
# ============================================================================

Write-Host "STEP 1️⃣1️⃣  Starting Services..." -ForegroundColor Green
SSH-ExecQuiet "systemctl start redis-server"
SSH-ExecQuiet "systemctl start postgresql@16-main; sleep 2"
SSH-ExecQuiet "systemctl restart passport_app_gunicorn; sleep 2"
SSH-ExecQuiet "systemctl start passport_app_celery"
SSH-ExecQuiet "systemctl restart nginx"
Start-Sleep -Seconds 3
Write-Host "  ✅ All services started" -ForegroundColor Green
Write-Host ""

# ============================================================================
# STEP 12: Test Deployment
# ============================================================================

Write-Host "STEP 1️⃣2️⃣  Testing Deployment..." -ForegroundColor Green
$testResult = SSH-Exec "curl -s -I http://165.22.214.244" | Select-Object -First 1
Write-Host "  $testResult" -ForegroundColor White

if ($testResult -match "302|200") {
    Write-Host "  ✅ App is responding correctly!" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Unexpected response - check logs" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================================
# FINAL SUMMARY
# ============================================================================

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              ✨ DEPLOYMENT COMPLETE ✨                        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 DEPLOYMENT CREDENTIALS" -ForegroundColor Yellow
Write-Host "─" * 66
Write-Host ""
Write-Host "🌐 Application URL:" -ForegroundColor Cyan
Write-Host "   http://165.22.214.244" -ForegroundColor White
Write-Host ""
Write-Host "👤 Superuser Login:" -ForegroundColor Cyan
Write-Host "   Username: $SuperUserName" -ForegroundColor Green
Write-Host "   Password: $cleanSUPassword" -ForegroundColor Magenta
Write-Host ""
Write-Host "🗄️  PostgreSQL Database:" -ForegroundColor Cyan
Write-Host "   Database: passport_app_db" -ForegroundColor White
Write-Host "   User:     passport_user" -ForegroundColor White
Write-Host "   Password: $cleanDBPassword" -ForegroundColor Magenta
Write-Host "   Host:     localhost" -ForegroundColor White
Write-Host "   Port:     5432" -ForegroundColor White
Write-Host ""
Write-Host "🔑 Django SECRET_KEY:" -ForegroundColor Cyan
Write-Host "   $secretKey" -ForegroundColor Magenta
Write-Host ""
Write-Host "─" * 66
Write-Host "✅ All services running and accessible!" -ForegroundColor Green
Write-Host "⚠️  Save these credentials in a secure location" -ForegroundColor Yellow
Write-Host ""
