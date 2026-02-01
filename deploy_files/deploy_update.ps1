# Deploy script to update server with latest git changes

# Configuration
$DropletIP = "165.22.214.244"
$RootPath = "/root/studio_sheet"
$Branch = "main"  # Change to your branch name

# Helper functions
function Invoke-SSH {
    param([string]$Command)
    ssh root@$DropletIP $Command
}

function Invoke-SSHQuiet {
    param([string]$Command)
    ssh root@$DropletIP $Command 2>&1 | Out-Null
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deploying Latest Changes to Server" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Pull latest code
Write-Host "STEP 1: Pulling latest code from git..." -ForegroundColor Green
Invoke-SSH "cd $RootPath && git pull origin $Branch"
Write-Host "[OK] Code updated" -ForegroundColor Green
Write-Host ""

# Step 2: Install/update dependencies
Write-Host "STEP 2: Installing dependencies..." -ForegroundColor Green
Invoke-SSHQuiet "cd $RootPath && source venv/bin/activate && pip install -r requirements.txt --quiet"
Write-Host "[OK] Dependencies updated" -ForegroundColor Green
Write-Host ""

# Step 3: Run migrations
Write-Host "STEP 3: Running database migrations..." -ForegroundColor Green
Invoke-SSH "cd $RootPath && source venv/bin/activate && python manage.py migrate"
Write-Host "[OK] Migrations applied" -ForegroundColor Green
Write-Host ""

# Step 4: Collect static files
Write-Host "STEP 4: Collecting static files..." -ForegroundColor Green
Invoke-SSH "cd $RootPath && source venv/bin/activate && python manage.py collectstatic --noinput"
Write-Host "[OK] Static files collected" -ForegroundColor Green
Write-Host ""

# Step 5: Restart services
Write-Host "STEP 5: Restarting services..." -ForegroundColor Green
Invoke-SSHQuiet "sudo systemctl restart passport_app_gunicorn"
Invoke-SSHQuiet "sudo systemctl restart passport_app_celery"
Invoke-SSHQuiet "sudo systemctl reload nginx"
Start-Sleep -Seconds 3
Write-Host "[OK] Services restarted" -ForegroundColor Green
Write-Host ""

# Step 6: Test deployment
Write-Host "STEP 6: Testing deployment..." -ForegroundColor Green
$httpStatus = Invoke-SSH "curl -s -o /dev/null -w '%{http_code}' http://$DropletIP" | Select-Object -Last 1
$httpStatus = $httpStatus.Trim()
if ($httpStatus -eq "200" -or $httpStatus -eq "302") {
    Write-Host "[OK] Application is responding (HTTP $httpStatus)" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Application returned HTTP $httpStatus" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Server: http://$DropletIP" -ForegroundColor White
Write-Host ""
Write-Host "To view logs:" -ForegroundColor Yellow
Write-Host "  ssh root@$DropletIP 'tail -f $RootPath/logs/django.log'" -ForegroundColor Gray
Write-Host ""
