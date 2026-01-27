# DigitalOcean Droplet Deployment (Ubuntu 22.04)

This guide sets up the Django app on a DigitalOcean Droplet with Nginx + Gunicorn.

## 1) Create Droplet
- Image: Ubuntu 22.04 LTS
- Plan: Basic (choose CPU/Memory per traffic)
- Datacenter: nearest to users
- Add SSH key for secure access
- Optional: Attach Floating IP and configure DNS

## 2) Connect and install dependencies

```bash
# Update & install packages
sudo apt update && sudo apt -y upgrade
sudo apt -y install python3.10 python3.10-venv python3-pip git nginx

# Optional: use UFW firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

## 3) Create app directory and clone code

```bash
sudo mkdir -p /var/www/passport_app
sudo chown $USER:$USER /var/www/passport_app
cd /var/www/passport_app

# Option A: Clone from your Git repo
# git clone https://github.com/<you>/<repo>.git .

# Option B: Upload files via scp (from local machine)
# scp -r ./passport_app/* root@your_droplet_ip:/var/www/passport_app/
```

## 4) Python virtualenv & dependencies

```bash
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt
```

## 5) Environment config

```bash
cp .env.example .env
# Edit .env with your values
nano .env
# SECRET_KEY=...
# DEBUG=False
# ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
# MAX_FILE_SIZE_MB=10
# FILE_CLEANUP_HOURS=24
# RATE_LIMIT=100
```

## 6) Django setup

```bash
# Make sure media and logs directories exist
mkdir -p logs media/uploads media/outputs

# Migrate and collect static
python manage.py migrate
python manage.py collectstatic --noinput
```

## 7) Systemd service for Gunicorn

```bash
# Copy service file
sudo cp deploy/gunicorn.service /etc/systemd/system/passport_app.service

# Create runtime dir for socket
sudo mkdir -p /run

# Start and enable service
sudo systemctl daemon-reload
sudo systemctl start passport_app
sudo systemctl enable passport_app

# Check status
sudo systemctl status passport_app
```

## 8) Nginx configuration

```bash
# Copy Nginx conf
sudo cp deploy/nginx_passport_app.conf /etc/nginx/sites-available/passport_app

# Link it and test
sudo ln -s /etc/nginx/sites-available/passport_app /etc/nginx/sites-enabled/
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

Update `server_name` in the Nginx config with your domain or droplet IP.

## 9) Domain & HTTPS (optional but recommended)

```bash
# Point your domain A/AAAA record to the Droplet IP
# Then use Certbot for TLS
sudo apt -y install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## 10) Permissions

```bash
# Ensure Nginx and Gunicorn can read/write required folders
sudo chown -R www-data:www-data /var/www/passport_app/media
sudo chown -R www-data:www-data /var/www/passport_app/logs
```

## 11) Maintenance

- Logs: `journalctl -u passport_app -f`
- App logs: `/var/www/passport_app/logs/django.log`
- Restart service: `sudo systemctl restart passport_app`
- Update code: pull changes, re-install requirements, `collectstatic`, restart service

## Notes on SQLite & Media
- SQLite is fine for small deployments; consider Managed PostgreSQL for production.
- Media is stored under `/var/www/passport_app/media`. For multi-droplet or CDN, use DigitalOcean Spaces.

## Optional: Schedule cleanup of old files

```bash
# Delete generated files older than configured hours
sudo bash -c 'cat > /etc/cron.d/passport_cleanup <<\EOF
0 2 * * * www-data cd /var/www/passport_app && /var/www/passport_app/venv/bin/python manage.py cleanup_old_files >> /var/www/passport_app/logs/cleanup.log 2>&1
EOF'
```
