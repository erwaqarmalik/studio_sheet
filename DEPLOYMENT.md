# Passport App - Fresh Deployment Script

## Overview

The `deploy_fresh.ps1` script provides a complete, automated fresh deployment of the Passport App to a DigitalOcean droplet from scratch. It includes:

- **PostgreSQL Database Setup** - Creates database and user with secure credentials
- **Automatic Credential Generation** - Generates random passwords for superuser and database
- **Auto-Generated SECRET_KEY** - Django secret key generated during deployment
- **Full Clean Slate** - Drops old database, clears output files, pulls latest code
- **Service Configuration** - Starts Gunicorn, Celery, Redis, Nginx, and PostgreSQL
- **Migrations & Static Files** - Runs all Django migrations and collects static files
- **Testing** - Tests endpoint connectivity and reports status

## Prerequisites

- PowerShell 5.0 or higher (Windows)
- SSH access to droplet (key-based preferred, password auth works)
- Git credentials configured locally
- Droplet must have:
  - Ubuntu 20.04+ LTS
  - Python 3.10+ with venv
  - PostgreSQL 16
  - Redis
  - Nginx
  - Gunicorn/Celery service files already installed

## Usage

### Basic Usage

```powershell
.\deploy_files\deploy_fresh.ps1
```

This uses default parameters:
- Droplet IP: `165.22.214.244`
- Superuser: `erwaqarmalik`
- App Path: `/root/studio_sheet`

### Custom Parameters

```powershell
.\deploy_files\deploy_fresh.ps1 -DropletIP 192.168.1.100 -SuperUserName admin -RootPath /opt/app
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `DropletIP` | `165.22.214.244` | IP address of the DigitalOcean droplet |
| `RootPath` | `/root/studio_sheet` | Deployment directory on droplet |
| `SuperUserName` | `erwaqarmalik` | Django superuser username |

## Execution Steps

### STEP 1: Stop Services
- Stops all running services gracefully (Gunicorn, Celery, Nginx, Redis)
- Ensures clean deployment

### STEP 2: Clear Old Data
- Drops existing PostgreSQL database
- Removes old SQLite database file (if exists)
- Clears media output directory

### STEP 3: Pull Latest Code
- Fetches latest code from GitHub repository
- Ensures you're deploying current version

### STEP 4: Setup PostgreSQL
- Creates new `passport_app_db` database
- Creates `passport_user` with randomly generated password
- Configures PostgreSQL role settings (encoding, isolation, timezone)
- Grants all privileges to user on database

### STEP 5: Generate Django SECRET_KEY
- Creates cryptographically secure SECRET_KEY
- Displayed in credentials output

### STEP 6: Create .env Configuration
- Generates `.env` file with all configuration
- Sets DEBUG=False for production
- Configures PostgreSQL, Redis, and Celery settings
- Sets ALLOWED_HOSTS to include droplet IP

### STEP 7: Install Python Dependencies
- Upgrades pip, setuptools, wheel
- Installs all packages from requirements.txt
- Quiet installation (no verbose output)

### STEP 8: Run Django Migrations
- Executes all pending Django migrations
- Creates database schema
- Initializes tables

### STEP 9: Collect Static Files
- Runs Django collectstatic
- Gathers CSS, JS, images for Nginx serving

### STEP 10: Create Superuser
- Creates Django superuser account
- Uses `--noinput` flag with provided credentials
- Username: `erwaqarmalik` (or custom via parameter)
- Password: Randomly generated (shown at end)

### STEP 11: Start Services
- Starts Redis server
- Starts PostgreSQL cluster
- Restarts Gunicorn with 2 workers
- Starts Celery worker
- Restarts Nginx reverse proxy

### STEP 12: Test Deployment
- Tests HTTP connectivity to app
- Verifies 200 or 302 response (redirect to login)
- Confirms all services are operational

## Output

At the end of deployment, you'll see:

```
========================================================
DEPLOYMENT COMPLETE
========================================================

APPLICATION URL:
  http://165.22.214.244

SUPERUSER LOGIN:
  Username: erwaqarmalik
  Password: PTBNBBUiAj7xMr3h

POSTGRESQL DATABASE:
  Database: passport_app_db
  User:     passport_user
  Password: AprBAFJhnlLuAOkKAHCd
  Host:     localhost
  Port:     5432

DJANGO SECRET_KEY:
  django-insecure-z9k!@#$%^&*()_+{}:"|<>?[];\,./

========================================================
[OK] Save credentials in a secure location
```

**IMPORTANT:** Save these credentials immediately in a secure location (password manager, encrypted file, etc.)

## Connection Details After Deployment

### Access the Application
- **URL:** http://165.22.214.244
- **Admin Panel:** http://165.22.214.244/admin
- **Login:** Use superuser credentials from deployment output

### SSH into Droplet
```bash
ssh root@165.22.214.244
```

### Check Service Status
```bash
systemctl status passport_app_gunicorn
systemctl status passport_app_celery
systemctl status nginx
systemctl status postgresql@16-main
systemctl status redis-server
```

### View Application Logs
```bash
journalctl -xeu passport_app_gunicorn -n 50
journalctl -xeu passport_app_celery -n 50
tail -f /root/studio_sheet/logs/django.log
```

### PostgreSQL Connection
```bash
psql -h localhost -U passport_user -d passport_app_db
```

## Troubleshooting

### Script Hangs at Password Prompt
- If SSH asks for password repeatedly, set up key-based auth:
  ```bash
  ssh-copy-id root@165.22.214.244
  ```

### PostgreSQL Connection Failed
- Check if PostgreSQL is running:
  ```bash
  systemctl status postgresql@16-main
  ```
- Verify database exists:
  ```bash
  sudo -u postgres psql -l | grep passport_app_db
  ```

### Gunicorn Not Responding
- Check logs:
  ```bash
  journalctl -xeu passport_app_gunicorn -n 100
  ```
- Restart service:
  ```bash
  systemctl restart passport_app_gunicorn
  ```

### 500 Errors After Deployment
- Check Gunicorn error logs
- Verify .env file exists and is readable:
  ```bash
  cat /root/studio_sheet/.env | grep DB_
  ```
- Ensure migrations ran:
  ```bash
  python manage.py showmigrations
  ```

## Security Notes

1. **Change Superuser Password** - After first login, change the auto-generated password
2. **Store Credentials Safely** - Use password manager or encrypted storage
3. **Enable HTTPS** - Set up SSL certificate with Let's Encrypt:
   ```bash
   apt install certbot python3-certbot-nginx
   certbot --nginx -d your-domain.com
   ```
4. **Firewall Rules** - Configure UFW or iptables to restrict access
5. **Regular Backups** - Set up automated PostgreSQL backups

## Rollback/Redeploy

To redeploy from scratch again:

1. Run the script again - it will:
   - Drop the existing database
   - Clear old files
   - Pull latest code
   - Start fresh

2. Or manually reset:
   ```bash
   systemctl stop passport_app_gunicorn passport_app_celery
   sudo -u postgres psql -c "DROP DATABASE passport_app_db;"
   rm /root/studio_sheet/db.sqlite3
   ```

## Performance Tuning (Optional)

### Increase Gunicorn Workers
Edit `/etc/systemd/system/passport_app_gunicorn.service`:
```
ExecStart=/root/studio_sheet/venv/bin/gunicorn \
  --workers 4 \
  --worker-class sync \
  --bind 127.0.0.1:8000 \
  passport_app.wsgi:application
```

### PostgreSQL Configuration
Edit `/etc/postgresql/16/main/postgresql.conf`:
- Increase `shared_buffers` for more RAM allocation
- Adjust `work_mem` for query optimization
- Set `effective_cache_size` to 3/4 of available RAM

### Celery Worker Concurrency
Edit `/etc/systemd/system/passport_app_celery.service`:
```
--concurrency=4
```

## Notes

- Script uses `echo` and `systemctl` compatible with bash
- All credentials are randomly generated and unique per deployment
- Script is idempotent - safe to run multiple times
- No credentials are stored in git or logs
- Static files served by Nginx from `/root/studio_sheet/staticfiles/`
- Media files stored in `/root/studio_sheet/media/`

## Support

If issues occur:
1. Check service logs: `journalctl -xeu SERVICE_NAME`
2. Verify SSH access: `ssh root@165.22.214.244 "whoami"`
3. Test SSH key setup: `ssh-keygen -t ed25519`
4. Enable verbose output in script if needed
