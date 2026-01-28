# Deployment Guide

## Quick Deployment

To deploy updates to the server, simply run:

```powershell
.\deploy.ps1 -ServerIP "165.22.214.244"
```

This will:
1. Pull latest code from GitHub
2. Activate virtual environment
3. Install/update dependencies
4. Collect static files
5. Run database migrations
6. Restart Gunicorn service
7. Verify service status

## Server Information

- **Server IP**: 165.22.214.244
- **Site URL**: http://165.22.214.244
- **Admin URL**: http://165.22.214.244/admin/
- **Admin Credentials**: 
  - Username: `admin`
  - Password: `admin123`

## Server Configuration

- **Application Path**: `/var/www/passport_app`
- **Python Environment**: `/var/www/passport_app/venv`
- **Service**: `passport_app.service` (Gunicorn)
- **Web Server**: Nginx (reverse proxy on port 80)
- **Gunicorn**: Runs on `127.0.0.1:8000` with 3 workers

## Manual Deployment Steps

If you prefer manual deployment:

```bash
# SSH into the server
ssh root@165.22.214.244

# Navigate to application directory
cd /var/www/passport_app

# Pull latest code
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Restart Gunicorn
sudo systemctl restart passport_app

# Check service status
sudo systemctl status passport_app
```

## Environment Variables

The server uses environment variables from `/var/www/passport_app/.env`:

```
SECRET_KEY=<django-secret-key>
DEBUG=False
ALLOWED_HOSTS=165.22.214.244,localhost,127.0.0.1
MAX_FILE_SIZE_MB=10
FILE_CLEANUP_HOURS=24
RATE_LIMIT=100
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

## SSL/HTTPS Configuration

Currently, the site runs on HTTP. To enable HTTPS:

1. Install Let's Encrypt certificate:
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

2. Update `.env` on server:
   ```
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   ```

3. Restart services:
   ```bash
   sudo systemctl restart passport_app
   sudo systemctl restart nginx
   ```

## Troubleshooting

### Check Service Status
```bash
sudo systemctl status passport_app
sudo systemctl status nginx
```

### View Logs
```bash
# Gunicorn logs
sudo journalctl -u passport_app -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Restart Services
```bash
sudo systemctl restart passport_app
sudo systemctl restart nginx
```

### Check Port Usage
```bash
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :80
```

## Firewall

UFW is enabled with the following rules:
- Port 22 (SSH) - ALLOW
- Port 80 (HTTP) - ALLOW  
- Port 443 (HTTPS) - ALLOW

## Development Workflow

1. Make changes locally
2. Test locally
3. Commit to Git: `git add . && git commit -m "Description"`
4. Push to GitHub: `git push origin main`
5. Deploy to server: `.\deploy.ps1 -ServerIP "165.22.214.244"`

## Notes

- The deployment script uses SSH with password authentication
- All commands are executed sequentially; if one fails, deployment stops
- Static files are automatically collected during deployment
- Database migrations are automatically applied
- Gunicorn service is automatically restarted after deployment
