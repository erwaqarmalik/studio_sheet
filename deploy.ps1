# Automated Deployment Script for Passport App
# Usage: .\deploy.ps1 -ServerIP "your.server.ip" [-User "root"]

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIP,
    
    [Parameter(Mandatory=$false)]
    [string]$User = "root",
    
    [Parameter(Mandatory=$false)]
    [string]$AppPath = "/var/www/passport_app"
)

Write-Host "`n╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Passport App Deployment to DigitalOcean    ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "Server: " -NoNewline -ForegroundColor Yellow
Write-Host "$User@$ServerIP" -ForegroundColor White
Write-Host "Path: " -NoNewline -ForegroundColor Yellow
Write-Host "$AppPath`n" -ForegroundColor White

Write-Host "Starting deployment...`n" -ForegroundColor Green

try {
    # Execute deployment commands via SSH
    $result = ssh "$User@$ServerIP" @'
cd /var/www/passport_app && 
echo "1️⃣  Pulling latest code..." && 
git pull origin main && 
echo "2️⃣  Activating virtual environment..." && 
source venv/bin/activate && 
echo "3️⃣  Installing/updating dependencies..." && 
pip install -r requirements.txt --quiet && 
echo "4️⃣  Collecting static files..." && 
python manage.py collectstatic --noinput && 
echo "5️⃣  Running migrations..." && 
python manage.py migrate && 
echo "6️⃣  Restarting application service..." && 
sudo systemctl restart passport_app && 
sleep 2 && 
echo "7️⃣  Checking service status..." && 
sudo systemctl status passport_app --no-pager && 
echo "" && 
echo "✅ Deployment completed successfully!"
'@
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n╔════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "║          Deployment Successful! 🎉            ║" -ForegroundColor Green
        Write-Host "╚════════════════════════════════════════════════╝`n" -ForegroundColor Green
        
        Write-Host "Your app should now be running with the latest changes." -ForegroundColor White
        Write-Host "Visit your server to verify the Bootstrap redesign is live!`n" -ForegroundColor White
    } else {
        Write-Host "`n❌ Deployment encountered errors. Check the output above.`n" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "`n❌ Error connecting to server: $_`n" -ForegroundColor Red
    Write-Host "Make sure:" -ForegroundColor Yellow
    Write-Host "  • SSH is installed and configured" -ForegroundColor White
    Write-Host "  • You have SSH key access to the server" -ForegroundColor White
    Write-Host "  • The server IP is correct`n" -ForegroundColor White
    exit 1
}
