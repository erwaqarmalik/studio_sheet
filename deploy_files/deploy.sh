#!/bin/bash
# Deployment script for Passport App on Ubuntu 24.04
# Run this script as root on your DigitalOcean droplet

set -e

PROJECT_DIR="/root/studio_sheet"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_USER="root"

echo "=== Passport App Deployment Script ==="

# 1. Update system packages
echo "[1/10] Updating system packages..."
apt-get update
apt-get upgrade -y

# 2. Install system dependencies
echo "[2/10] Installing system dependencies..."
apt-get install -y python3 python3-pip python3-venv \
    postgresql postgresql-contrib \
    redis-server \
    nginx \
    git \
    build-essential \
    libpq-dev

# 3. Create PostgreSQL database and user
echo "[3/10] Creating PostgreSQL database..."
sudo -u postgres psql << EOF
CREATE DATABASE passport_app;
CREATE USER passport_user WITH PASSWORD 'your-secure-password-here';
ALTER ROLE passport_user SET client_encoding TO 'utf8';
ALTER ROLE passport_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE passport_user SET default_transaction_deferrable TO on;
ALTER ROLE passport_user SET default_transaction_isolation TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE passport_app TO passport_user;
EOF

# 4. Start and enable Redis
echo "[4/10] Starting Redis service..."
systemctl start redis-server
systemctl enable redis-server

# 5. Install Python requirements
echo "[5/10] Installing Python requirements..."
cd $PROJECT_DIR
$VENV_DIR/bin/pip install --upgrade pip setuptools wheel
$VENV_DIR/bin/pip install -r requirements.txt

# 6. Create .env file from template
echo "[6/10] Creating .env file..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/deploy/.env.example" "$PROJECT_DIR/.env"
    echo "⚠️  Edit $PROJECT_DIR/.env with your configuration before continuing"
fi

# 7. Run Django migrations
echo "[7/10] Running Django migrations..."
cd $PROJECT_DIR
$VENV_DIR/bin/python manage.py migrate
$VENV_DIR/bin/python manage.py collectstatic --noinput

# 8. Install Gunicorn systemd service
echo "[8/10] Installing Gunicorn systemd service..."
cp deploy/passport_app_gunicorn.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable passport_app_gunicorn

# 9. Install Celery worker systemd service
echo "[9/10] Installing Celery worker systemd service..."
cp deploy/passport_app_celery.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable passport_app_celery

# 10. Install Nginx configuration
echo "[10/10] Installing Nginx configuration..."
cp deploy/passport_app_nginx.conf /etc/nginx/sites-available/passport_app
ln -sf /etc/nginx/sites-available/passport_app /etc/nginx/sites-enabled/passport_app
rm -f /etc/nginx/sites-enabled/default  # Remove default site if exists
nginx -t
systemctl enable nginx

# Start services
echo ""
echo "=== Starting Services ==="
systemctl start passport_app_gunicorn
systemctl start passport_app_celery
systemctl start nginx

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit /root/studio_sheet/.env with your SECRET_KEY and database password"
echo "2. Run: systemctl restart passport_app_gunicorn passport_app_celery"
echo "3. Access your app at: http://165.22.214.244"
echo ""
echo "Check service status:"
echo "  systemctl status passport_app_gunicorn"
echo "  systemctl status passport_app_celery"
echo "  systemctl status nginx"
