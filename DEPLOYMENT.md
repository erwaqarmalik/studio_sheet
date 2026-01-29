# Deployment Scripts

This directory contains scripts to automate deployment to your DigitalOcean server.

## Prerequisites

1. **SSH Access**: Ensure you have SSH key-based authentication set up with your server
2. **Git Repository**: Your server should have the repository cloned at `/var/www/passport_app`
3. **Initial Setup**: Server must already be configured (see [deploy/DO_DROPLET_SETUP.md](deploy/DO_DROPLET_SETUP.md))

## Quick Start

### Windows (PowerShell)
```powershell
.\deploy.ps1 -ServerIP "your.server.ip.address"
```

### Linux/Mac (Bash)
```bash
chmod +x deploy.sh
./deploy.sh your.server.ip.address
```

## What the Script Does

1. ✅ Connects to your server via SSH
2. ✅ Pulls the latest code from GitHub
3. ✅ Installs/updates Python dependencies
4. ✅ Collects static files (CSS, JS, images)
5. ✅ Runs database migrations
6. ✅ Restarts the Gunicorn service
7. ✅ Shows service status

## Examples

### Deploy with default root user
```powershell
.\deploy.ps1 -ServerIP "159.65.123.45"
```

### Deploy with custom user
```powershell
.\deploy.ps1 -ServerIP "159.65.123.45" -User "ubuntu"
```

### Deploy with custom app path
```powershell
.\deploy.ps1 -ServerIP "159.65.123.45" -User "root" -AppPath "/opt/passport_app"
```

## Troubleshooting

### "Permission denied (publickey)"
- Ensure your SSH key is added to the server's `~/.ssh/authorized_keys`
- Test connection: `ssh root@your.server.ip`

### "git pull failed"
- Check if the repository is properly configured on the server
- Verify the server has access to your GitHub repository

### "Service restart failed"
- Check service logs: `ssh root@your.server.ip "journalctl -u passport_app -n 50"`
- Verify the service is configured: `ssh root@your.server.ip "systemctl status passport_app"`

### "collectstatic failed"
- Ensure `STATIC_ROOT` is set in settings.py
- Check write permissions: `ssh root@your.server.ip "ls -la /var/www/passport_app/staticfiles"`

## Manual Deployment

If you prefer to deploy manually:

```bash
# SSH into your server
ssh root@your.server.ip

# Navigate to app directory
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

# Restart service
sudo systemctl restart passport_app

# Check status
sudo systemctl status passport_app
```

## Viewing Logs

### Application logs
```bash
ssh root@your.server.ip "tail -f /var/www/passport_app/logs/django.log"
```

### Service logs
```bash
ssh root@your.server.ip "journalctl -u passport_app -f"
```

### Nginx access logs
```bash
ssh root@your.server.ip "tail -f /var/log/nginx/access.log"
```

### Nginx error logs
```bash
ssh root@your.server.ip "tail -f /var/log/nginx/error.log"
```

## Post-Deployment Verification

After deployment, verify:

1. **Service Status**: Check that `passport_app.service` is active and running
2. **Website Access**: Visit your domain/IP and verify the Bootstrap redesign is visible
3. **Navigation**: Test all navigation links (Home, History, Profile)
4. **Functionality**: Upload a test photo and generate output
5. **Static Files**: Verify CSS and images load correctly

## Rollback

If deployment fails and you need to rollback:

```bash
ssh root@your.server.ip
cd /var/www/passport_app
git log --oneline -10  # Find the previous commit hash
git reset --hard <previous-commit-hash>
sudo systemctl restart passport_app
```

## Security Notes

- **Never commit** `.env` file or secrets to Git
- Keep your SSH keys secure
- Use SSH key authentication (not passwords)
- Consider using a non-root user for deployments
- Regularly update server packages: `sudo apt update && sudo apt upgrade`

## Continuous Deployment (Optional)

For automatic deployments on every push, see GitHub Actions workflow in `.github/workflows/deploy.yml` (if configured).
