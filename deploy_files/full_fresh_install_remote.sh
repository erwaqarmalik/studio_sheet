#!/usr/bin/env bash
set -euo pipefail

echo "=== Stopping all services ==="
systemctl stop nginx postgresql redis-server passport_app_gunicorn passport_app_celery 2>/dev/null || true

echo "=== Killing processes on ports 80, 8000, 5432, 6379 ==="
fuser -k 80/tcp 2>/dev/null || true
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 5432/tcp 2>/dev/null || true
fuser -k 6379/tcp 2>/dev/null || true

echo "=== Removing systemd services ==="
rm -f /etc/systemd/system/passport_app_gunicorn.service
rm -f /etc/systemd/system/passport_app_celery.service
systemctl daemon-reload

echo "=== Removing Nginx configs ==="
rm -f /etc/nginx/sites-available/passport_app
rm -f /etc/nginx/sites-enabled/passport_app
rm -f /etc/nginx/sites-enabled/default

echo "=== Removing old app folders ==="
rm -rf /root/studio_sheet
rm -rf /var/lib/postgresql/16/main

echo "=== Restarting PostgreSQL to recreate data directory ==="
systemctl restart postgresql

echo "=== Waiting for PostgreSQL to be ready (max 30 seconds) ==="
for i in {1..30}; do
    if sudo -u postgres pg_isready -q 2>/dev/null; then
        echo "PostgreSQL is ready!"
        break
    fi
    echo -n "."
    sleep 1
done

echo ""
echo "=== Creating fresh PostgreSQL database and user ==="
sudo -u postgres psql << 'PSQL_EOF'
DROP DATABASE IF EXISTS passport_app;
DROP USER IF EXISTS passport_user;
CREATE DATABASE passport_app;
CREATE USER passport_user WITH PASSWORD 'change-this';
ALTER ROLE passport_user SET client_encoding TO 'utf8';
ALTER ROLE passport_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE passport_user SET default_transaction_deferrable TO on;
GRANT ALL PRIVILEGES ON DATABASE passport_app TO passport_user;
\c passport_app
GRANT ALL PRIVILEGES ON SCHEMA public TO passport_user;
PSQL_EOF

echo "=== Cloning fresh repository ==="
git clone https://github.com/erwaqarmalik/studio_sheet.git /root/studio_sheet
cd /root/studio_sheet

echo "=== Creating Python venv ==="
python3 -m venv /root/studio_sheet/venv
/root/studio_sheet/venv/bin/pip install --upgrade pip setuptools wheel
/root/studio_sheet/venv/bin/pip install -r requirements.txt
/root/studio_sheet/venv/bin/pip install gunicorn

echo "=== Creating .env file ==="
cat > /root/studio_sheet/.env << 'ENV_EOF'
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=False
ALLOWED_HOSTS=165.22.214.244,localhost,127.0.0.1
DB_ENGINE=postgresql
DB_NAME=passport_app
DB_USER=passport_user
DB_PASSWORD=change-this
DB_HOST=127.0.0.1
DB_PORT=5432
REDIS_URL=redis://127.0.0.1:6379/0
CELERY_ENABLED=True
CELERY_BROKER_URL=redis://127.0.0.1:6379/1
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/2
ENV_EOF

echo "=== Running Django migrations ==="
/root/studio_sheet/venv/bin/python manage.py migrate

echo "=== Collecting static files ==="
/root/studio_sheet/venv/bin/python manage.py collectstatic --noinput --clear

echo "=== Installing systemd services ==="
cp /root/studio_sheet/deploy_files/passport_app_gunicorn.service /etc/systemd/system/
cp /root/studio_sheet/deploy_files/passport_app_celery.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable passport_app_gunicorn passport_app_celery

echo "=== Installing Nginx configuration ==="
cp /root/studio_sheet/deploy_files/passport_app_nginx.conf /etc/nginx/sites-available/passport_app
ln -sf /etc/nginx/sites-available/passport_app /etc/nginx/sites-enabled/passport_app
rm -f /etc/nginx/sites-enabled/default
nginx -t

echo "=== Starting all services ==="
systemctl restart redis-server
systemctl restart postgresql
sleep 3
systemctl restart passport_app_gunicorn
systemctl restart passport_app_celery
systemctl restart nginx
systemctl enable nginx redis-server postgresql

echo ""
echo "=== INSTALLATION COMPLETE ==="
echo ""
echo "App deployed at: /root/studio_sheet"
echo "Database: passport_app"
echo "Services: gunicorn, celery, nginx, postgresql, redis"
echo ""
echo "Access app at: http://165.22.214.244"
echo ""
