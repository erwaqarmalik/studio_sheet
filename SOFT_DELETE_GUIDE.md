# Soft Delete & History Tracking - Implementation Guide

## 📋 Overview

This implementation adds **soft delete functionality** and **deletion history tracking** to the Passport Photo Generator application. Instead of permanently deleting records, they are marked as deleted and can be restored later.

---

## ✨ Features

### 1. **Soft Delete**
- Records are marked as deleted instead of being removed from database
- Deleted records are hidden from normal queries
- Can be restored at any time
- Maintains data integrity and relationships

### 2. **History Tracking**
- Every delete and restore operation is logged
- Tracks who performed the action and when
- Stores reason for deletion/restoration
- Maintains audit trail for compliance

### 3. **Admin Interface**
- Visual indicators for deleted records (🗑️ badges)
- Bulk actions: Soft Delete, Restore, Hard Delete
- Filter by deletion status
- View deletion history

### 4. **Management Commands**
- Cleanup old deleted records automatically
- Restore deleted records from command line
- View deletion history reports

---

## 🏗️ Architecture

### Models with Soft Delete

✅ **PhotoGeneration** - User's photo generation history
✅ **GenerationAudit** - Audit trail records

### New Model

📦 **DeletionHistory** - Tracks all deletion and restoration operations

### Soft Delete Fields

Every soft-delete enabled model has:
- `deleted_at` - Timestamp when deleted (null = active)
- `deleted_by` - User who deleted the record
- `deletion_reason` - Text explanation for deletion

---

## 🔧 Technical Implementation

### Mixin Class

```python
from generator.mixins import SoftDeleteMixin

class MyModel(SoftDeleteMixin, models.Model):
    # Your fields...
    pass
```

The mixin provides:
- `.delete()` - Soft delete by default
- `.delete(hard_delete=True)` - Permanent deletion
- `.restore()` - Restore deleted record
- `.is_deleted()` - Check deletion status

### Custom Managers

```python
# Default manager (excludes deleted)
PhotoGeneration.objects.all()  # Only active records

# Include deleted records
PhotoGeneration.all_objects.all()  # All records

# Only deleted records
PhotoGeneration.objects.only_deleted()  # Soft-deleted only
```

---

## 📖 Usage Examples

### In Python Code

#### Soft Delete a Record
```python
from generator.models import PhotoGeneration

generation = PhotoGeneration.objects.get(id=123)
generation.delete(
    deleted_by=request.user,
    reason='User requested deletion'
)
```

#### Restore a Record
```python
generation = PhotoGeneration.all_objects.get(id=123)
if generation.is_deleted():
    generation.restore(
        restored_by=request.user,
        reason='User requested restoration'
    )
```

#### Permanent Deletion
```python
# Hard delete (use with caution!)
generation.delete(hard_delete=True)

# Or use the method directly
generation.hard_delete()
```

#### Query Only Active Records
```python
# This is the default behavior
active_generations = PhotoGeneration.objects.filter(user=request.user)

# Explicitly include deleted
all_generations = PhotoGeneration.all_objects.filter(user=request.user)

# Only deleted
deleted_only = PhotoGeneration.objects.only_deleted()
```

---

## 🖥️ Django Admin Usage

### Viewing Records

1. Navigate to **PhotoGeneration** or **GenerationAudit** in admin
2. Deleted records show **🗑️ DELETED** badge in red
3. Active records show **✓ Active** badge in green
4. Use filter **"By deleted at"** to filter by status

### Soft Delete Records

1. Select records to delete
2. Choose action: **"Soft delete selected items"**
3. Click "Go"
4. Records are marked as deleted (not removed from database)

### Restore Records

1. Select deleted records (shown with 🗑️ badge)
2. Choose action: **"Restore selected items"**
3. Click "Go"
4. Records are restored and active again

### Permanent Deletion

⚠️ **Warning**: This cannot be undone!

1. Select records to permanently delete
2. Choose action: **"⚠️ PERMANENTLY delete selected items"**
3. Click "Go"
4. Records are removed from database forever

### View Deletion History

1. Navigate to **Deletion History** in admin
2. See all delete/restore operations
3. Filter by model, action, or date
4. Click **"View Related Object"** to see the record (if it still exists)

---

## 🛠️ Management Commands

### 1. Cleanup Old Deleted Records

Permanently delete records that were soft-deleted more than X days ago.

```bash
# Dry run (see what would be deleted)
python manage.py cleanup_soft_deleted --days=30 --dry-run

# Actually delete (default: 30 days)
python manage.py cleanup_soft_deleted --days=30

# Specific model only
python manage.py cleanup_soft_deleted --days=90 --model=PhotoGeneration

# All models (default)
python manage.py cleanup_soft_deleted --days=60 --model=all
```

**Options:**
- `--days=N` - Delete records deleted more than N days ago (default: 30)
- `--dry-run` - Show what would be deleted without deleting
- `--model=MODEL` - Cleanup specific model (PhotoGeneration, GenerationAudit, or all)

**When to use:**
- Scheduled as a cron job (monthly cleanup)
- When database size needs to be reduced
- After confirming deleted records are no longer needed

---

### 2. Restore Deleted Records

Restore soft-deleted records from command line.

```bash
# List all soft-deleted PhotoGeneration records
python manage.py restore_deleted --model=PhotoGeneration

# Restore specific record by ID
python manage.py restore_deleted --model=PhotoGeneration --id=123

# Restore specific record with reason
python manage.py restore_deleted --model=PhotoGeneration --id=123 --reason="User requested restoration"

# Restore ALL deleted records of a model
python manage.py restore_deleted --model=PhotoGeneration --all
```

**Options:**
- `--model=MODEL` - Model to restore from (required)
- `--id=ID` - Primary key of record to restore
- `--all` - Restore all deleted records (requires confirmation)
- `--reason=TEXT` - Reason for restoration

**When to use:**
- User requests to restore accidentally deleted data
- After investigation, records should be undeleted
- Bulk restoration after accidental bulk deletion

---

### 3. View Deletion History

View reports of all deletion and restoration operations.

```bash
# View last 30 days of history
python manage.py view_deletion_history

# View last 90 days
python manage.py view_deletion_history --days=90

# Filter by model
python manage.py view_deletion_history --model=PhotoGeneration

# Filter by action type
python manage.py view_deletion_history --action=deleted

# Filter by user
python manage.py view_deletion_history --user=admin

# Show more records
python manage.py view_deletion_history --limit=100

# Combined filters
python manage.py view_deletion_history --model=PhotoGeneration --action=restored --days=7
```

**Options:**
- `--days=N` - Show last N days (default: 30)
- `--model=NAME` - Filter by model name
- `--action=TYPE` - Filter by action (deleted, restored, hard_deleted)
- `--user=USERNAME` - Filter by username
- `--limit=N` - Max records to show (default: 50)

**When to use:**
- Audit who deleted what and when
- Investigate suspicious deletions
- Compliance reporting
- Understanding deletion patterns

---

## 🔄 Migration

The implementation includes a Django migration:

```bash
# Apply the migration
python manage.py migrate

# This adds:
# - deleted_at, deleted_by, deletion_reason to PhotoGeneration
# - deleted_at, deleted_by, deletion_reason to GenerationAudit
# - Creates DeletionHistory table
```

**Migration File**: `generator/migrations/0006_generationaudit_deleted_at_and_more.py`

---

## ⚙️ Automated Cleanup Schedule

### Using Cron (Linux/Mac)

Add to crontab:

```bash
# Run cleanup monthly (1st of month at 2 AM)
0 2 1 * * cd /var/www/passport_app && /var/www/passport_app/venv/bin/python manage.py cleanup_soft_deleted --days=90 >> /var/www/passport_app/logs/cleanup.log 2>&1
```

### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create new task
3. Trigger: Monthly, 1st day, 2:00 AM
4. Action: Run program
   - Program: `C:\Python\python.exe`
   - Arguments: `manage.py cleanup_soft_deleted --days=90`
   - Start in: `D:\Projects\passport_app`

---

## 📊 Database Schema

### DeletionHistory Table

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| model_name | CharField(100) | Name of model (e.g., "PhotoGeneration") |
| object_id | Integer | PK of the deleted/restored object |
| action | CharField(20) | deleted, restored, or hard_deleted |
| performed_by | ForeignKey(User) | User who performed action (nullable) |
| performed_at | DateTime | When action was performed |
| reason | TextField | Reason for action |
| metadata | JSONField | Additional metadata |

**Indexes:**
- `(model_name, object_id, -performed_at)`
- `(performed_by, -performed_at)`
- `(action, -performed_at)`

---

## 🔐 Security & Permissions

### Admin Permissions

- **Soft Delete**: Staff users with change permission
- **Restore**: Staff users with change permission
- **Hard Delete**: Staff users with delete permission
- **View History**: Staff users with view permission

### Audit Trail

Every operation is logged with:
- Who performed the action
- When it was performed
- Why it was performed (if provided)
- What was affected

---

## 🎯 Best Practices

### When to Soft Delete

✅ **Use Soft Delete For:**
- User-generated content (photos, generations)
- Audit trail records
- Records that might need restoration
- Compliance-sensitive data

❌ **Don't Use Soft Delete For:**
- Temporary data (sessions, caches)
- System-generated data with no value
- Performance-critical tables (adds query overhead)

### Retention Policy

Recommended retention periods:
- **PhotoGeneration**: 90 days
- **GenerationAudit**: 365 days (1 year for compliance)
- **DeletionHistory**: Never delete (permanent audit trail)

### Performance Considerations

- Soft delete adds a WHERE clause to queries (minimal overhead)
- Use `.only_deleted()` sparingly (not indexed for performance)
- Schedule cleanup during low-traffic hours
- Consider database size growth and plan cleanup schedules

---

## 🐛 Troubleshooting

### Records Not Showing After Delete

**Cause**: Using default manager which excludes deleted records

**Solution**: Use `all_objects` manager
```python
PhotoGeneration.all_objects.get(id=123)
```

### Cannot Restore Record

**Cause**: Record was hard deleted, not soft deleted

**Solution**: Check DeletionHistory for `hard_deleted` action. Hard deleted records cannot be restored.

### Cleanup Command Not Deleting

**Cause**: Records not old enough or using `--dry-run`

**Solution**: 
- Check deletion date with: `PhotoGeneration.objects.only_deleted()`
- Remove `--dry-run` flag to actually delete

---

## 📈 Monitoring & Analytics

### Deletion Metrics

Track deletion patterns:

```python
from generator.models import DeletionHistory
from django.db.models import Count

# Deletions by model
DeletionHistory.objects.filter(action='deleted') \
    .values('model_name') \
    .annotate(count=Count('id'))

# Deletions by user
DeletionHistory.objects.filter(action='deleted') \
    .values('performed_by__username') \
    .annotate(count=Count('id'))

# Restoration rate
total_deleted = DeletionHistory.objects.filter(action='deleted').count()
total_restored = DeletionHistory.objects.filter(action='restored').count()
restoration_rate = (total_restored / total_deleted * 100) if total_deleted > 0 else 0
```

---

## 🔄 Upgrade Path

### Existing Data

Existing records are **not affected** by this update:
- All existing records remain active (deleted_at = null)
- No data loss
- No changes to existing functionality

### Rollback

If needed, the migration can be reversed:

```bash
python manage.py migrate generator 0005
```

---

## 📚 Additional Resources

### Related Files

- **Mixin**: `generator/mixins.py`
- **Models**: `generator/models.py`
- **Admin**: `generator/admin.py`
- **Commands**: `generator/management/commands/`

### Documentation

- [Django Soft Delete Patterns](https://docs.djangoproject.com/en/stable/topics/db/managers/)
- [Custom Model Managers](https://docs.djangoproject.com/en/stable/topics/db/managers/)
- [Django Management Commands](https://docs.djangoproject.com/en/stable/howto/custom-management-commands/)

---

## ✅ Summary

**What was added:**
- ✅ Soft delete mixin with custom managers
- ✅ Deletion history tracking model
- ✅ Admin interface with visual indicators
- ✅ Three management commands for maintenance
- ✅ Comprehensive documentation

**Benefits:**
- 💾 Data safety (accidental deletions can be recovered)
- 📊 Complete audit trail
- 🔄 Easy restoration workflow
- 🛡️ Compliance-ready
- ⚙️ Automated cleanup

**Status**: ✅ Ready for production use

---

**Last Updated**: February 1, 2026
**Version**: 1.0.0
**Django Version**: 5.0+
