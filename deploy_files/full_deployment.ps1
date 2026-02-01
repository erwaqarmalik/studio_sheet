# ============================================================================
# Passport App - Full Fresh Deployment Script (PowerShell)
# Purpose: Deploy from scratch with PostgreSQL database
# Usage: .\full_deployment.ps1 -DropletIP 165.22.214.244
# ============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$DropletIP = "165.22.214.244",
    
    [string]$RootPath = "/root/studio_sheet",
    [string]$SuperUserName = "erwaqarmalik"
)

# Color output functions
function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Cyan
}

function Write-Warning-Msg {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Execute-SSH {
    param(
        [string]$Command,
        [string]$Description = ""
    )
    
    if ($Description) {
        Write-Info $Description
    }
    
    $output = ssh -o StrictHostKeyChecking=no root@$DropletIP $Command 2>&1
    return $output
}

# ============================================================================
# STEP 1: Stop all services
# ============================================================================
Write-Info "=========================================="
Write-Info "STEP 1: Stopping Services"
Write-Info "=========================================="

Execute-SSH "systemctl stop passport_app_gunicorn passport_app_celery nginx redis-server 2>/dev/null; true" "Stopping all services..."
Start-Sleep -Seconds 2
Write-Success "Services stopped"

# ============================================================================
# STEP 2: Clear old database and files
# ============================================================================
Write-Info "=========================================="
Write-Info "STEP 2: Clearing Old Database and Files"
Write-Info "=========================================="

Execute-SSH "sudo -u postgres psql -c 'DROP DATABASE IF EXISTS passport_app_db;' 2>/dev/null; true" "Dropping old PostgreSQL database..."
Write-Success "Old database dropped"

Execute-SSH "rm -f $RootPath/db.sqlite3" "Removing old SQLite database..."
Execute-SSH "rm -rf $RootPath/media/outputs/*" "Clearing old output files..."
Write-Success "Old files cleared"

# ============================================================================
# STEP 3: Update code from git
# ============================================================================
Write-Info "=========================================="
Write-Info "STEP 3: Updating Code from Git"
Write-Info "=========================================="

Execute-SSH "cd $RootPath; git pull" "Pulling latest code from GitHub..."
Write-Success "Code updated"

# ============================================================================
# Generate random passwords
# ============================================================================
$dbPassword = -join ((33..126) | Get-Random -Count 20 | ForEach-Object { [char]$_ })
$cleanDBPassword = $dbPassword -replace '[^a-zA-Z0-9@_]', '_'

$superUserPassword = -join ((33..126) | Get-Random -Count 16 | ForEach-Object { [char]$_ })
$cleanSuperUserPassword = $superUserPassword -replace '[^a-zA-Z0-9@_]', '_'

Write-Info "Generating secure passwords..."
Write-Host "Generated DB Password: $cleanDBPassword" -ForegroundColor Magenta
Write-Host "Generated Superuser Password: $cleanSuperUserPassword" -ForegroundColor Magenta

# ============================================================================
# STEP 4: Create PostgreSQL Database and User
# ============================================================================
Write-Info "=========================================="
Write-Info "STEP 4: Setting Up PostgreSQL"
Write-Info "=========================================="

Execute-SSH "sudo -u postgres psql -c 'CREATE DATABASE passport_app_db;' 2>/dev/null; true" "Creating PostgreSQL database..."
Execute-SSH "sudo -u postgres psql -c 'CREATE USER passport_user WITH PASSWORD ''$cleanDBPassword'';' 2>/dev/null; true" "Creating PostgreSQL user..."
Execute-SSH "sudo -u postgres psql -c 'ALTER ROLE passport_user SET client_encoding TO ''utf8'';' 2>/dev/null; true" "Configuring user encoding..."
Execute-SSH "sudo -u postgres psql -c 'ALTER ROLE passport_user SET default_transaction_isolation TO ''read committed'';' 2>/dev/null; true" "Configuring transaction isolation..."
Execute-SSH "sudo -u postgres psql -c 'ALTER ROLE passport_user SET timezone TO ''UTC'';' 2>/dev/null; true" "Configuring timezone..."
Execute-SSH "sudo -u postgres psql -c 'GRANT ALL PRIVILEGES ON DATABASE passport_app_db TO passport_user;' 2>/dev/null; true" "Granting database privileges..."

Write-Success "PostgreSQL setup complete"

# ============================================================================
# STEP 5: Generate Django SECRET_KEY
# ============================================================================
Write-Info "=========================================="
Write-Info "STEP 5: Generating Django SECRET_KEY"
Write-Info "=========================================="

$secretKeyOutput = Execute-SSH "cd $RootPath; venv/bin/python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'" "Generating Django SECRET_KEY..."
$secretKey = ($secretKeyOutput | Select-Object -Last 1).Trim()
Write-Host "Generated SECRET_KEY: $secretKey" -ForegroundColor Magenta
Write-Success "SECRET_KEY generated"

# ============================================================================
# STEP 6: Update .env file
# ============================================================================
Write-Info "=========================================="
Write-Info "STEP 6: Updating .env Configuration"
Write-Info "=========================================="

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

# Create temp .env file and upload
$tempEnvPath = "$env:TEMP\.env"
$envContent | Out-File -FilePath $tempEnvPath -Encoding ASCII -Force

scp -o StrictHostKeyChecking=no $tempEnvPath "root@$DropletIP`:`$RootPath/.env" | Out-Null
Remove-Item $tempEnvPath -Force

Write-Success ".env file configured"

# ============================================================================
# STEP 7: Install dependencies
# ============================================================================
Write-Info "=========================================="
Write-Info "STEP 7: Installing Python Dependencies"
Write-Info "=========================================="

Execute-SSH "cd $RootPath; venv/bin/pip install -q --upgrade pip setuptools wheel" "Upgrading pip..."
Execute-SSH "cd $RootPath; venv/bin/pip install -q -r requirements.txt" "Installing dependencies..."
Write-Success "Dependencies installed"

# ============================================================================
# STEP 8: Run migrations
# ============================================================================
Write-Info "=========================================="
Write-Info "STEP 8: Running Django Migrations"
Write-Info "=========================================="

Execute-SSH "cd $RootPath; venv/bin/python manage.py migrate --noinput" "Running migrations..."
Write-Success "Migrations completed"

# ============================================================================
# STEP 9: Collect static files
# ============================================================================
Write-Info "=========================================="
Write-Info "STEP 9: Collecting Static Files"
Write-Info "=========================================="

Execute-SSH "cd $RootPath; venv/bin/python manage.py collectstatic --noinput --clear" "Collecting static files..."
Write-Success "Static files collected"

# ============================================================================
# STEP 10: Create superuser
# ============================================================================
Write-Info "=========================================="
Write-Info "STEP 10: Creating Superuser"
Write-Info "=========================================="

Execute-SSH @"
cd $RootPath
venv/bin/python manage.py shell << 'EOFPY'
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.filter(username='$SuperUserName').delete()
user = User.objects.create_superuser('$SuperUserName', 'admin@example.com', '$cleanSuperUserPassword')
print('Superuser created successfully')
EOFPY
"@ "Creating superuser $SuperUserName..."

Write-Success "Superuser created"

# ============================================================================
# STEP 11: Start services
# ============================================================================
Write-Info "=========================================="
Write-Info "STEP 11: Starting Services"
Write-Info "=========================================="

Execute-SSH "systemctl start redis-server" "Starting Redis..."
Write-Success "Redis started"

Execute-SSH "systemctl start postgresql@16-main; sleep 2" "Starting PostgreSQL..."
Write-Success "PostgreSQL started"

Execute-SSH "systemctl restart passport_app_gunicorn; sleep 2" "Starting Gunicorn..."
Write-Success "Gunicorn started"

Execute-SSH "systemctl start passport_app_celery" "Starting Celery..."
Write-Success "Celery started"

Execute-SSH "systemctl restart nginx" "Starting Nginx..."
Write-Success "Nginx started"

# ============================================================================
# STEP 12: Test deployment
# ============================================================================
Write-Info "=========================================="
Write-Info "STEP 12: Testing Deployment"
Write-Info "=========================================="

Start-Sleep -Seconds 3
$testOutput = Execute-SSH "curl -s -I http://165.22.214.244"
Write-Host $testOutput

if ($testOutput -match "302|200") {
    Write-Success "App is responding correctly!"
} else {
    Write-Warning-Msg "Unexpected response. Check Gunicorn logs."
}

# ============================================================================
# FINAL SUMMARY
# ============================================================================
Write-Info "=========================================="
Write-Info "✨ DEPLOYMENT COMPLETE ✨"
Write-Info "=========================================="

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "📋 DEPLOYMENT CREDENTIALS" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Application URL:" -ForegroundColor Yellow
Write-Host "   http://165.22.214.244" -ForegroundColor Green
Write-Host ""
Write-Host "👤 Superuser Login:" -ForegroundColor Yellow
Write-Host "   Username: $SuperUserName" -ForegroundColor Green
Write-Host "   Password: $cleanSuperUserPassword" -ForegroundColor Magenta
Write-Host ""
Write-Host "🗄️  PostgreSQL Database:" -ForegroundColor Yellow
Write-Host "   Database: passport_app_db" -ForegroundColor Green
Write-Host "   User: passport_user" -ForegroundColor Green
Write-Host "   Password: $cleanDBPassword" -ForegroundColor Magenta
Write-Host "   Host: localhost" -ForegroundColor Green
Write-Host "   Port: 5432" -ForegroundColor Green
Write-Host ""
Write-Host "🔑 Django Secret Key:" -ForegroundColor Yellow
Write-Host "   $secretKey" -ForegroundColor Magenta
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ All services running and accessible!" -ForegroundColor Green
Write-Host "ℹ️  Save these credentials in a secure location" -ForegroundColor Cyan
Write-Host ""
