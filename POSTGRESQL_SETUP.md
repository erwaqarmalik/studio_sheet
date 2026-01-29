# PostgreSQL Migration Setup Guide

## Overview

This guide walks you through migrating from SQLite to PostgreSQL on your DigitalOcean server and applying enhanced database improvements.

## Prerequisites

- DigitalOcean Droplet at 165.22.214.244
- SSH access as root
- Existing Django application running with SQLite

## Step 1: Install PostgreSQL on Server

SSH into your server:

```powershell
ssh root@165.22.214.244
```

Install PostgreSQL and Python driver:

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib python3-psycopg2 -y
```

Start PostgreSQL service:

```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

## Step 2: Create Database and User

Connect to PostgreSQL:

```bash
sudo -u postgres psql
```

Inside PostgreSQL shell, create database and user:

```sql
CREATE DATABASE passport_app_db;
CREATE USER passport_user WITH PASSWORD 'SecurePassword123!';

-- Set user encoding and transaction settings
ALTER ROLE passport_user SET client_encoding TO 'utf8';
ALTER ROLE passport_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE passport_user SET default_transaction_deferrable TO on;
ALTER ROLE passport_user SET timezone TO 'UTC';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE passport_app_db TO passport_user;

-- Exit
\q
```

## Step 3: Update Local Development Environment

### Install PostgreSQL Driver

```bash
pip install psycopg2-binary>=2.9.9
```

Or update requirements.txt (already done):

```
psycopg2-binary>=2.9.9
```

### Test Connection Locally

```bash
python manage.py dbshell
# Should connect to your local SQLite
# Type: .quit to exit
```

## Step 4: Update Server Environment

SSH to server and update `.env`:

```bash
ssh root@165.22.214.244
cd /var/www/passport_app
nano .env
```

Add these lines:

```
DB_ENGINE=postgresql
DB_NAME=passport_app_db
DB_USER=passport_user
DB_PASSWORD=SecurePassword123!
DB_HOST=localhost
DB_PORT=5432
```

## Step 5: Create and Run Migrations

On your local machine, create migrations for the new models:

```bash
python manage.py makemigrations generator
python manage.py migrate --plan  # Preview changes
python manage.py migrate
```

This creates migration files for:
- Enhanced UserProfile (new fields: street_address, landmark, city, state, postal_code, country)
- UserRateLimit (rate limiting model)
- GenerationAudit (audit trail model)
- FeatureUsage (analytics model)

Commit the migrations:

```bash
git add generator/migrations/
git commit -m "Add PostgreSQL migration and enhanced database models"
git push origin main
```

## Step 6: Deploy to Server

Run the deployment script:

```powershell
.\deploy.ps1 -ServerIP "165.22.214.244"
```

The script will:
1. Pull latest code (including migrations)
2. Install psycopg2-binary
3. Run migrations (creates new PostgreSQL tables)
4. Collect static files
5. Restart Gunicorn service

## Step 7: Verify Migration Success

SSH to server and verify database:

```bash
ssh root@165.22.214.244
cd /var/www/passport_app
source venv/bin/activate

# Check database connection
python manage.py dbshell
# Inside PostgreSQL:
\dt  # List all tables
\d generator_userprofile  # Show UserProfile schema
\q   # Exit

# Run migrations check
python manage.py migrate --check

# Verify data (if migrating from SQLite):
python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.count()
>>> exit()
```

## Step 8: Backup SQLite Database (Optional)

Keep backup of old SQLite database:

```bash
sudo cp /var/www/passport_app/db.sqlite3 /var/www/passport_app/db.sqlite3.backup
```

Or download locally:

```powershell
# From local machine
scp root@165.22.214.244:/var/www/passport_app/db.sqlite3.backup ./db.sqlite3.backup
```

## Migration Data (If Needed)

If you need to migrate existing data from SQLite:

1. On local machine, export data:

```bash
python manage.py dumpdata auth.user > users.json
python manage.py dumpdata generator > generator.json
```

2. Deploy to server

3. On server, import data:

```bash
cd /var/www/passport_app
source venv/bin/activate
python manage.py loaddata users.json
python manage.py loaddata generator.json
```

## Troubleshooting

### Connection Refused

```bash
sudo systemctl restart postgresql
sudo ufw allow 5432/tcp
```

### Permission Denied

```bash
sudo -u postgres psql
GRANT CONNECT ON DATABASE passport_app_db TO passport_user;
\q
```

### Check PostgreSQL Logs

```bash
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### Django Migration Errors

```bash
# Check migration status
python manage.py showmigrations

# Unapply migrations (if needed)
python manage.py migrate generator 0001

# Check for conflicting migrations
python manage.py migrate --plan
```

## Performance Tuning

### Create Indexes for Better Performance

Connect to PostgreSQL and add indexes:

```bash
sudo -u postgres psql passport_app_db

CREATE INDEX idx_user_email ON auth_user(email);
CREATE INDEX idx_generation_user_date ON generator_photogeneration(user_id, created_at DESC);
CREATE INDEX idx_audit_timestamp ON generator_generationaudit(timestamp DESC);

\q
```

### Vacuum and Analyze

```bash
sudo -u postgres psql passport_app_db

VACUUM ANALYZE;

\q
```

## Monitoring Disk Usage

```bash
# Check database size
sudo -u postgres psql passport_app_db -c "SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) FROM pg_database ORDER BY pg_database_size(pg_database.datname) DESC;"
```

## Rollback Plan

If you need to rollback to SQLite:

1. Restore SQLite backup:

```bash
sudo cp /var/www/passport_app/db.sqlite3.backup /var/www/passport_app/db.sqlite3
```

2. Update `.env` to use SQLite:

```
DB_ENGINE=sqlite
```

3. Or delete `DB_*` variables and the code will default to SQLite

4. Restart service:

```bash
sudo systemctl restart passport_app
```

## Maintenance

### Weekly Tasks

```bash
# Backup database
sudo -u postgres pg_dump passport_app_db | gzip > /var/www/passport_app/backups/db_$(date +%Y%m%d).sql.gz

# Vacuum and analyze
sudo -u postgres psql passport_app_db -c "VACUUM ANALYZE;"
```

### Monthly Tasks

```bash
# Check database integrity
sudo -u postgres psql passport_app_db -c "REINDEX DATABASE passport_app_db;"
```

## Next Steps

1. ✅ Setup PostgreSQL
2. ✅ Create database and user
3. ✅ Run migrations
4. ✅ Verify connections
5. ✅ Monitor logs
6. (Optional) Enable automated backups
7. (Optional) Setup replication for high availability

## Support

For issues, check:
- Django logs: `sudo journalctl -u passport_app -f`
- PostgreSQL logs: `sudo tail -f /var/log/postgresql/postgresql-*.log`
- Nginx logs: `sudo tail -f /var/log/nginx/error.log`
