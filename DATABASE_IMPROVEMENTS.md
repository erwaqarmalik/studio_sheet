# Database Improvements - Implementation Summary

## Overview

Comprehensive database enhancements have been implemented to support:
- PostgreSQL migration for production
- Enhanced user profiles with complete address information
- Rate limiting to prevent abuse
- Audit logging for compliance
- Feature usage analytics

## What Changed

### 1. **Enhanced UserProfile Model**

#### New Address Fields:
- `street_address` - House number and street name
- `landmark` - Nearby landmark for easy reference
- `city` - City/Town
- `state` - State/Province (dropdown with Indian states)
- `postal_code` - PIN/Postal code (5-6 digits)
- `country` - Country dropdown (IN, US, UK, CA, AU, Other)

#### Other Enhancements:
- `profile_complete` - Boolean flag to track profile completion
- Enhanced `created_at` and `updated_at` with database indexing
- New method: `get_full_address()` - Returns formatted complete address
- New method: `is_complete()` - Checks if all required fields are filled

#### Database Indexes:
```python
- user
- created_at
- postal_code
- (country, state)
```

### 2. **New UserRateLimit Model**

Tracks and enforces per-user rate limits to prevent abuse:

- `generations_today` - Count of generations today
- `total_size_today_mb` - Total file size generated today
- `is_blocked` - Whether user is rate-limited
- `block_reason` - Reason for blocking
- `block_until` - When block expires
- `reset_if_needed()` - Auto-reset counters after 24 hours

### 3. **New GenerationAudit Model**

Complete audit trail for compliance and debugging:

- `generation` - Link to PhotoGeneration
- `user` - User who performed action
- `action` - Action type (created, downloaded, deleted, expired, failed)
- `ip_address` - IP address of requester
- `user_agent` - Browser/client information
- `timestamp` - When action occurred
- `details` - JSON for action-specific data

#### Database Indexes:
```python
- (generation, -timestamp)
- (user, -timestamp)
- (action, -timestamp)
```

### 4. **New FeatureUsage Model**

Analytics model to track feature usage:

- `feature` - Feature name (crop, batch_upload, export_pdf, etc.)
- `user` - User using feature
- `timestamp` - When feature was used
- `duration_seconds` - How long operation took
- `metadata` - JSON for feature-specific data

#### Database Indexes:
```python
- (feature, -timestamp)
- (user, -timestamp)
```

### 5. **PostgreSQL Support**

Updated `settings.py` to auto-detect database engine:

```python
if DEBUG or config('DB_ENGINE', default='sqlite') == 'sqlite':
    # Use SQLite for development
else:
    # Use PostgreSQL for production
```

**Environment variables for PostgreSQL:**
```
DB_ENGINE=postgresql
DB_NAME=passport_app_db
DB_USER=passport_user
DB_PASSWORD=<secure_password>
DB_HOST=localhost
DB_PORT=5432
```

### 6. **Enhanced Forms**

Updated `UserProfileForm` to include all new fields:

```python
Fields:
- first_name (required)
- last_name (required)
- email (required)
- date_of_birth (required)
- phone_number (required, validated)
- street_address (required)
- landmark (optional)
- city (required)
- state (required, dropdown)
- postal_code (required, 5-6 digits)
- country (required, dropdown)

Custom Validation:
- Phone number format validation
- Postal code digit validation
- Profile completion flag updated on save
```

### 7. **Enhanced Admin Interface**

New admin features for management:

#### UserProfile Inline:
- All address fields editable
- `profile_complete` flag visible
- Read-only timestamps

#### UserRateLimit Admin:
- List view showing generations and blocking status
- Action to unblock users
- Search by username/email

#### GenerationAudit Admin:
- Read-only (audit logs cannot be modified)
- Date hierarchy for browsing by date
- Filter by action type and timestamp

#### FeatureUsage Admin:
- Read-only (feature usage cannot be modified)
- Date hierarchy for analytics
- Filter by feature type

### 8. **Signal Handlers (Auto-Creation)**

When a new user is created:

```python
1. UserProfile is automatically created
2. UserRateLimit is automatically created
```

This ensures no user exists without these records.

## Migration Path

### Local Development (No Action Needed)

The migration has already been applied locally:

```bash
✅ Migrations created: 0004_featureusage_generationaudit_userratelimit_and_more.py
✅ Local SQLite database updated
✅ Models synchronized
```

### Server Deployment

To deploy to production with PostgreSQL:

**Step 1: Setup PostgreSQL on Server**

```powershell
ssh root@165.22.214.244

# Inside server shell:
sudo apt update
sudo apt install postgresql postgresql-contrib python3-psycopg2 -y
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

**Step 2: Create Database and User**

```bash
sudo -u postgres psql

# Inside PostgreSQL:
CREATE DATABASE passport_app_db;
CREATE USER passport_user WITH PASSWORD 'SecurePassword123!';
ALTER ROLE passport_user SET client_encoding TO 'utf8';
ALTER ROLE passport_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE passport_user SET default_transaction_deferrable TO on;
ALTER ROLE passport_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE passport_app_db TO passport_user;

\q
```

**Step 3: Update Server .env**

```bash
nano /var/www/passport_app/.env

# Add these lines:
DB_ENGINE=postgresql
DB_NAME=passport_app_db
DB_USER=passport_user
DB_PASSWORD=SecurePassword123!
DB_HOST=localhost
DB_PORT=5432
```

**Step 4: Deploy**

```powershell
.\deploy.ps1 -ServerIP "165.22.214.244"
```

The deployment script will:
1. Pull latest code (with migrations)
2. Install psycopg2-binary
3. Run migrations
4. Collect static files
5. Restart Gunicorn

**Step 5: Verify**

```bash
ssh root@165.22.214.244
cd /var/www/passport_app
source venv/bin/activate

# Check connection
python manage.py dbshell
\dt  # List tables
\q

# Check migrations
python manage.py migrate --check

# Create superuser (if needed)
python manage.py createsuperuser
```

## Key Benefits

✅ **Better Performance** - PostgreSQL is more efficient than SQLite for production

✅ **User Safety** - Complete address information for identification and verification

✅ **Abuse Prevention** - Rate limiting prevents users from overloading the server

✅ **Compliance** - Audit trail for regulatory requirements

✅ **Analytics** - Feature usage tracking for insights

✅ **Reliability** - Auto-created profiles ensure data consistency

✅ **Admin Control** - Enhanced Django admin interface for management

## Breaking Changes

⚠️ **Admin Registration Changes:**

The new models are automatically registered in admin:
- UserProfile (inline with User)
- UserRateLimit (inline with User)
- GenerationAudit (read-only)
- FeatureUsage (read-only)

## Database Indexes

Created indexes for optimal query performance:

```sql
-- UserProfile
CREATE INDEX idx_user_profile_user ON generator_userprofile(user_id);
CREATE INDEX idx_user_profile_created ON generator_userprofile(created_at);
CREATE INDEX idx_user_profile_postal ON generator_userprofile(postal_code);
CREATE INDEX idx_user_profile_location ON generator_userprofile(country, state);

-- UserRateLimit
CREATE INDEX idx_rate_limit_user ON generator_userratelimit(user_id);
CREATE INDEX idx_rate_limit_blocked ON generator_userratelimit(is_blocked);

-- GenerationAudit
CREATE INDEX idx_audit_generation_date ON generator_generationaudit(generation_id, timestamp DESC);
CREATE INDEX idx_audit_user_date ON generator_generationaudit(user_id, timestamp DESC);
CREATE INDEX idx_audit_action_date ON generator_generationaudit(action, timestamp DESC);

-- FeatureUsage
CREATE INDEX idx_feature_usage_date ON generator_featureusage(feature, timestamp DESC);
CREATE INDEX idx_feature_user_date ON generator_featureusage(user_id, timestamp DESC);
```

## Next Steps

1. ✅ Enhanced models implemented
2. ✅ Forms updated
3. ✅ Admin interface configured
4. ✅ Migrations created and applied locally
5. ⏳ Deploy to server with PostgreSQL
6. ⏳ Test profile creation requirement
7. ⏳ Monitor rate limiting
8. ⏳ Export audit logs for compliance

## Files Modified

- `generator/models.py` - Added new models and signal handlers
- `generator/forms.py` - Enhanced UserProfileForm with all fields
- `generator/admin.py` - Enhanced admin interface for all models
- `passport_app/settings.py` - Added PostgreSQL support
- `requirements.txt` - Added psycopg2-binary
- `generator/migrations/0004_*.py` - Migration file created

## Support Resources

For detailed PostgreSQL setup instructions, see:
- [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md)

For deployment details, see:
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

## Rollback Plan

If needed to revert to SQLite:

1. Remove PostgreSQL environment variables from `.env`
2. Restore SQLite backup: `db.sqlite3.backup`
3. Restart services

The code supports both SQLite and PostgreSQL automatically.
