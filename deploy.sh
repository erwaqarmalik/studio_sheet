#!/bin/bash
# Automated Deployment Script for Linux/Mac
# Usage: ./deploy.sh your.server.ip [user]

SERVER_IP="${1}"
USER="${2:-root}"
APP_PATH="/var/www/passport_app"

if [ -z "$SERVER_IP" ]; then
    echo "Usage: ./deploy.sh <server-ip> [user]"
    echo "Example: ./deploy.sh 159.65.123.45 root"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║   Passport App Deployment to DigitalOcean    ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "Server: $USER@$SERVER_IP"
echo "Path: $APP_PATH"
echo ""
echo "Starting deployment..."
echo ""

# Execute deployment commands via SSH
ssh "$USER@$SERVER_IP" bash << 'ENDSSH'
cd /var/www/passport_app
echo "1️⃣  Pulling latest code..."
git pull origin main
echo "2️⃣  Activating virtual environment..."
source venv/bin/activate
echo "3️⃣  Installing/updating dependencies..."
pip install -r requirements.txt --quiet
echo "4️⃣  Collecting static files..."
python manage.py collectstatic --noinput
echo "5️⃣  Running migrations..."
python manage.py migrate
echo "6️⃣  Restarting application service..."
sudo systemctl restart passport_app
echo "7️⃣  Checking service status..."
sudo systemctl status passport_app --no-pager -l
echo ""
echo "✅ Deployment completed successfully!"
ENDSSH

if [ $? -eq 0 ]; then
    echo ""
    echo "╔════════════════════════════════════════════════╗"
    echo "║          Deployment Successful! 🎉            ║"
    echo "╚════════════════════════════════════════════════╝"
    echo ""
    echo "Your app should now be running with the latest changes."
    echo "Visit your server to verify the Bootstrap redesign is live!"
    echo ""
else
    echo ""
    echo "❌ Deployment encountered errors. Check the output above."
    echo ""
    exit 1
fi
