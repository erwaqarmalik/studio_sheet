# Passport App - Quick Reference

## One-Command Fresh Deployment

```powershell
.\deploy_files\deploy_fresh.ps1
```

This will:
✅ Stop all services
✅ Clear old database
✅ Pull latest code from GitHub
✅ Setup PostgreSQL database
✅ Generate secure credentials
✅ Create Django superuser
✅ Run migrations
✅ Collect static files
✅ Start all services
✅ Test connectivity

**Output:** Complete credentials (DB password, superuser password, SECRET_KEY)

---

## Post-Deployment

### Access the App
- **URL:** http://165.22.214.244
- **Admin:** http://165.22.214.244/admin
- **Username:** erwaqarmalik
- **Password:** Check script output

### SSH Into Droplet
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

### View Logs
```bash
journalctl -xeu passport_app_gunicorn -n 50
```

---

## Credentials Generated

| Item | Type | Where to Find |
|------|------|---------------|
| Superuser Username | Static | `erwaqarmalik` (or custom param) |
| Superuser Password | Random | Script output |
| Database Password | Random | Script output |
| PostgreSQL User | Static | `passport_user` |
| DATABASE | Static | `passport_app_db` |
| SECRET_KEY | Random | Script output & `.env` file |

---

## Database Access

### From Droplet
```bash
psql -h localhost -U passport_user -d passport_app_db
```

### From Local Machine
```bash
psql -h 165.22.214.244 -U passport_user -d passport_app_db
```

---

## File Locations on Droplet

```
/root/studio_sheet/
├── .env                          # Configuration file
├── db.sqlite3                    # SQLite database (if used)
├── manage.py                     # Django management script
├── requirements.txt              # Python dependencies
├── venv/                         # Python virtual environment
├── staticfiles/                  # Collected static files (Nginx serves)
├── media/                        # User uploads
│   ├── uploads/                  # Uploaded files
│   └── outputs/                  # Generated outputs
├── logs/
│   └── django.log               # Application logs
├── generator/                    # Main Django app
│   ├── views.py
│   ├── models.py
│   ├── urls.py
│   └── ...
└── passport_app/                 # Django config
    ├── settings.py
    ├── wsgi.py
    └── celery.py
```

---

## Common Commands

### Restart Gunicorn
```bash
systemctl restart passport_app_gunicorn
```

### Restart Celery
```bash
systemctl restart passport_app_celery
```

### Restart Nginx
```bash
systemctl restart nginx
```

### Run Migrations
```bash
cd /root/studio_sheet
venv/bin/python manage.py migrate
```

### Collect Static Files
```bash
cd /root/studio_sheet
venv/bin/python manage.py collectstatic --noinput
```

### Create Another Superuser
```bash
cd /root/studio_sheet
venv/bin/python manage.py createsuperuser
```

### Access Django Shell
```bash
cd /root/studio_sheet
venv/bin/python manage.py shell
```

---

## Environment Variables (.env)

```
SECRET_KEY=...                          # Django secret key
DEBUG=False                             # Disable debug mode
ALLOWED_HOSTS=165.22.214.244,...       # Allowed hostnames
DB_ENGINE=postgresql                   # Database engine
DB_NAME=passport_app_db                # Database name
DB_USER=passport_user                  # Database user
DB_PASSWORD=...                        # Database password
DB_HOST=localhost                      # Database host
DB_PORT=5432                           # Database port
REDIS_URL=redis://127.0.0.1:6379/0    # Redis connection
CELERY_ENABLED=True                    # Enable async tasks
CELERY_BROKER_URL=redis://...         # Celery broker
CELERY_RESULT_BACKEND=redis://...     # Celery results
```

---

## Troubleshooting Checklist

- [ ] SSH access works: `ssh root@165.22.214.244`
- [ ] Services running: `systemctl status passport_app_gunicorn`
- [ ] App responds: `curl http://127.0.0.1:8000`
- [ ] Nginx working: `curl http://165.22.214.244`
- [ ] Database exists: `psql -U passport_user -d passport_app_db -c "\dt"`
- [ ] .env file exists: `ls -la /root/studio_sheet/.env`
- [ ] Check error logs: `journalctl -xeu passport_app_gunicorn -n 100`

---

## Security Reminders

1. 🔐 Save credentials immediately after deployment
2. 🔑 Change superuser password after first login
3. 🛡️  Setup SSL certificate (Let's Encrypt)
4. 🚪 Enable firewall rules
5. 📋 Regular database backups
6. 🔄 Keep dependencies updated

---

## Need Help?

- View deployment logs: `tail -f /root/studio_sheet/logs/django.log`
- Check Gunicorn status: `systemctl status passport_app_gunicorn --no-pager`
- Read full documentation: See [DEPLOYMENT.md](./DEPLOYMENT.md)
