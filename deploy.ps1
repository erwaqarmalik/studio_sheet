# PowerShell Deployment Script for Passport App
# Usage: .\deploy.ps1 -ServerIP "165.22.214.244"

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIP,
    
    [Parameter(Mandatory=$false)]
    [string]$User = "root",
    
    [Parameter(Mandatory=$false)]
    [string]$AppPath = "/var/www/passport_app"
)

Write-Host "Starting deployment to $ServerIP..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

try {
    # Define deployment commands as an array
    $commands = @(
        "cd $AppPath",
        "echo '1. Pulling latest code from GitHub...'",
        "git pull origin main",
        "echo '2. Activating virtual environment...'",
        "source venv/bin/activate",
        "echo '3. Installing/updating dependencies...'",
        "pip install -r requirements.txt",
        "echo '4. Collecting static files...'",
        "python manage.py collectstatic --noinput",
        "echo '5. Running database migrations...'",
        "python manage.py migrate",
        "echo '6. Restarting Gunicorn service...'",
        "sudo systemctl restart passport_app",
        "echo '7. Checking service status...'",
        "sudo systemctl status passport_app --no-pager -l",
        "echo 'Deployment completed successfully!'"
    )
    
    # Join commands with && for sequential execution
    $deployScript = $commands -join ' && '
    
    Write-Host "Connecting to server..." -ForegroundColor Yellow
    
    # Execute deployment via SSH
    ssh "$User@$ServerIP" $deployScript
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "Deployment successful!" -ForegroundColor Green
        Write-Host "Site should be live at: http://$ServerIP" -ForegroundColor Green
    } else {
        throw "Deployment command returned error code: $LASTEXITCODE"
    }
}
catch {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Deployment failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
