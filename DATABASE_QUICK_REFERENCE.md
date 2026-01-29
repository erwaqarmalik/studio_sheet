# Database Implementation - Quick Reference

## Summary of Changes

### Models Added
1. **UserRateLimit** - Track user generation limits (prevent abuse)
2. **GenerationAudit** - Audit trail for all generations (compliance)
3. **FeatureUsage** - Analytics on feature usage (insights)

### UserProfile Enhanced
- Added comprehensive address fields (street, landmark, city, state, pin, country)
- Removed old single `address` field
- Added `profile_complete` flag
- Added validation methods

### Database Engine
- SQLite for development (automatic)
- PostgreSQL for production (with environment variables)

## Local Development Setup

✅ **Already Complete:**
- Migration created and applied
- Models updated
- Forms updated
- Admin configured
- SQLite database updated

Run locally:
```bash
python manage.py runserver
```

## Server Deployment Steps

### 1. Install PostgreSQL
```bash
ssh root@165.22.214.244
sudo apt install postgresql postgresql-contrib python3-psycopg2 -y
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### 2. Create Database
```bash
sudo -u postgres psql
CREATE DATABASE passport_app_db;
CREATE USER passport_user WITH PASSWORD 'SecurePassword123!';
ALTER ROLE passport_user SET client_encoding TO 'utf8';
ALTER ROLE passport_user SET default_transaction_isolation TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE passport_app_db TO passport_user;
\q
```

### 3. Update .env on Server
```bash
ssh root@165.22.214.244
nano /var/www/passport_app/.env

# Add:
DB_ENGINE=postgresql
DB_NAME=passport_app_db
DB_USER=passport_user
DB_PASSWORD=SecurePassword123!
DB_HOST=localhost
DB_PORT=5432
```

### 4. Deploy
```powershell
.\deploy.ps1 -ServerIP "165.22.214.244"
```

That's it! The script handles everything:
- Git pull (gets migrations)
- pip install (gets psycopg2)
- Migrations run
- Static files collected
- Service restarted

## Admin Interface

**Login at:** http://165.22.214.244/admin/

### Available Models
- **Users** (with inline profiles and rate limits)
- **User Rate Limits** (with unblock action)
- **Generations** (read-only, sortable)
- **Generation Audits** (read-only, audit logs)
- **Feature Usage** (read-only, analytics)

## API/Usage

### Create Profile Automatically
```python
from django.contrib.auth.models import User
user = User.objects.create_user(username='john', password='pass')
# UserProfile and UserRateLimit automatically created via signals
```

### Check Profile Completeness
```python
user = User.objects.get(username='john')
is_complete = user.profile.is_complete()  # Returns True/False
```

### Get Full Address
```python
user = User.objects.get(username='john')
address = user.profile.get_full_address()
# "123 Main St, New York, NY 10001, United States"
```

### Rate Limiting
```python
user = User.objects.get(username='john')
rate_limit = user.rate_limit

# Check if blocked
if rate_limit.is_blocked:
    print(f"User blocked: {rate_limit.block_reason}")

# Auto reset if 24 hours passed
rate_limit.reset_if_needed()

# Manual unblock (admin action)
rate_limit.is_blocked = False
rate_limit.save()
```

### Log Generation
```python
from generator.models import GenerationAudit

GenerationAudit.objects.create(
    generation=generation_obj,
    user=request.user,
    action='created',
    ip_address=request.META.get('REMOTE_ADDR'),
    user_agent=request.META.get('HTTP_USER_AGENT'),
    details={'photos': 5, 'format': 'PDF'}
)
```

### Track Feature Usage
```python
from generator.models import FeatureUsage
import time

start = time.time()
# ... do feature ...
duration = int(time.time() - start)

FeatureUsage.objects.create(
    user=request.user,
    feature='crop',
    duration_seconds=duration,
    metadata={'images': 3}
)
```

## Testing

### Create Test Profile
```bash
python manage.py shell

from django.contrib.auth.models import User
from generator.models import UserProfile

# Create user
user = User.objects.create_user(username='testuser', password='test123')

# Update profile
profile = user.profile
profile.date_of_birth = '2000-01-01'
profile.phone_number = '+1234567890'
profile.street_address = '123 Main St'
profile.city = 'New York'
profile.state = 'NY'
profile.postal_code = '10001'
profile.country = 'US'
profile.profile_complete = profile.is_complete()
profile.save()

# Check
print(f"Profile complete: {profile.profile_complete}")
print(f"Address: {profile.get_full_address()}")

exit()
```

### Test Rate Limiting
```bash
python manage.py shell

from django.contrib.auth.models import User

user = User.objects.get(username='testuser')
rate_limit = user.rate_limit

# Simulate generation
rate_limit.generations_today = 50
rate_limit.total_size_today_mb = 500.0
rate_limit.save()

# Check if should block (customize limits in your code)
if rate_limit.generations_today > 100:
    rate_limit.is_blocked = True
    rate_limit.block_reason = 'Exceeded generation limit'
    rate_limit.save()

print(f"Generations today: {rate_limit.generations_today}")
print(f"Is blocked: {rate_limit.is_blocked}")

exit()
```

## Database Queries

### User Statistics
```python
from django.db.models import Count, Sum
from generator.models import PhotoGeneration

# Total generations per user
stats = PhotoGeneration.objects.values('user__username').annotate(
    total=Count('id'),
    total_size_mb=Sum('file_size_bytes') / (1024 * 1024)
).order_by('-total')
```

### Audit Trail for User
```python
from generator.models import GenerationAudit

user_audits = GenerationAudit.objects.filter(user__username='john').order_by('-timestamp')[:50]
```

### Feature Usage Analytics
```python
from generator.models import FeatureUsage
from django.db.models import Count, Avg

# Most used features
top_features = FeatureUsage.objects.values('feature').annotate(
    count=Count('id'),
    avg_duration=Avg('duration_seconds')
).order_by('-count')
```

### Blocked Users
```python
from generator.models import UserRateLimit

blocked = UserRateLimit.objects.filter(is_blocked=True).select_related('user')
```

## Troubleshooting

### Connection Error: psycopg2
```bash
# Install on server
cd /var/www/passport_app
source venv/bin/activate
pip install psycopg2-binary
```

### Connection Error: Database "passport_app_db" does not exist
```bash
# Verify database exists
sudo -u postgres psql -l | grep passport_app_db

# If missing, create it
sudo -u postgres psql
CREATE DATABASE passport_app_db;
GRANT ALL PRIVILEGES ON DATABASE passport_app_db TO passport_user;
\q
```

### Migration Errors
```bash
# Check migration status
python manage.py showmigrations

# List all migrations
python manage.py migrate --plan

# Run specific migration
python manage.py migrate generator 0004
```

### Check PostgreSQL Connection
```bash
# From server
sudo -u postgres psql passport_app_db

# Inside PostgreSQL
\dt  # List tables
SELECT COUNT(*) FROM auth_user;  # Count users
SELECT COUNT(*) FROM generator_userprofile;  # Count profiles
\q
```

## File Reference

- **Models:** [generator/models.py](generator/models.py)
- **Forms:** [generator/forms.py](generator/forms.py)
- **Admin:** [generator/admin.py](generator/admin.py)
- **Settings:** [passport_app/settings.py](passport_app/settings.py)
- **Migration:** [generator/migrations/0004_*.py](generator/migrations/)
- **Details:** [DATABASE_IMPROVEMENTS.md](DATABASE_IMPROVEMENTS.md)
- **Setup:** [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md)

## Key Facts

- ✅ 3 new models created (UserRateLimit, GenerationAudit, FeatureUsage)
- ✅ UserProfile enhanced with 7 new address fields
- ✅ Automatic profile/rate-limit creation via signals
- ✅ PostgreSQL support added (backward compatible with SQLite)
- ✅ 12+ database indexes for optimal performance
- ✅ Enhanced admin interface with custom actions
- ✅ Read-only audit and feature usage models
- ✅ Full form validation and address formatting

## Next Actions

1. ✅ Code changes complete
2. ⏳ Deploy to server with PostgreSQL
3. ⏳ Test profile creation requirement
4. ⏳ Test rate limiting functionality
5. ⏳ Monitor audit logs
6. ⏳ Analyze feature usage

Run deployment:
```powershell
.\deploy.ps1 -ServerIP "165.22.214.244"
```

Then verify PostgreSQL connection works!
