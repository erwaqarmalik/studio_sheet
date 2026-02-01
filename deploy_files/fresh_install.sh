#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/root/studio_sheet"
REPO_URL="https://github.com/erwaqarmalik/studio_sheet.git"

# Stop services (ignore errors)
systemctl stop passport_app_gunicorn passport_app_celery nginx >/dev/null 2>&1 || true

# Remove old services and nginx site
rm -f /etc/systemd/system/passport_app_gunicorn.service
rm -f /etc/systemd/system/passport_app_celery.service
rm -f /etc/nginx/sites-available/passport_app
rm -f /etc/nginx/sites-enabled/passport_app
systemctl daemon-reload

# Remove old app folder
rm -rf "$APP_DIR"

# Fresh clone
apt-get update -y
apt-get install -y git python3 python3-venv python3-pip nginx redis-server postgresql postgresql-contrib libpq-dev build-essential

git clone "$REPO_URL" "$APP_DIR"
cd "$APP_DIR"

# Create PostgreSQL database and user
sudo -u postgres psql <<'PSQL_EOF'
CREATE DATABASE passport_app;
CREATE USER passport_user WITH PASSWORD 'change-this';
ALTER ROLE passport_user SET client_encoding TO 'utf8';
ALTER ROLE passport_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE passport_user SET default_transaction_deferrable TO on;
GRANT ALL PRIVILEGES ON DATABASE passport_app TO passport_user;
\c passport_app
GRANT ALL PRIVILEGES ON SCHEMA public TO passport_user;
PSQL_EOF

# Create venv and install deps
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip setuptools wheel
"$APP_DIR/venv/bin/pip" install -r requirements.txt
"$APP_DIR/venv/bin/pip" install gunicorn

# Create .env (edit after run)
cat > "$APP_DIR/.env" <<'EOF'
SECRET_KEY=change-this
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
EOF

# Migrate + collectstatic
"$APP_DIR/venv/bin/python" manage.py migrate
"$APP_DIR/venv/bin/python" manage.py collectstatic --noinput

# Install services + Nginx
cp "$APP_DIR/deploy_files/passport_app_gunicorn.service" /etc/systemd/system/
cp "$APP_DIR/deploy_files/passport_app_celery.service" /etc/systemd/system/
cp "$APP_DIR/deploy_files/passport_app_nginx.conf" /etc/nginx/sites-available/passport_app
ln -sf /etc/nginx/sites-available/passport_app /etc/nginx/sites-enabled/passport_app
rm -f /etc/nginx/sites-enabled/default
systemctl daemon-reload
nginx -t

# Start services
systemctl restart passport_app_gunicorn passport_app_celery nginx
systemctl enable passport_app_gunicorn passport_app_celery nginx

cat <<'DONE'

Fresh install complete.
Next steps:
1) Edit /root/studio_sheet/.env and set SECRET_KEY + DB_PASSWORD
2) Restart services: systemctl restart passport_app_gunicorn passport_app_celery
DONE
