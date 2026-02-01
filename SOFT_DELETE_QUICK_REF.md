# 🚀 Soft Delete - Quick Reference

## 📌 Common Operations

### Python Code

```python
from generator.models import PhotoGeneration

# Soft delete
obj.delete(deleted_by=request.user, reason="User requested")

# Restore
obj.restore(restored_by=request.user, reason="Mistake")

# Hard delete (permanent)
obj.hard_delete()

# Check if deleted
if obj.is_deleted():
    print("This record is deleted")

# Query active only (default)
PhotoGeneration.objects.all()

# Query with deleted
PhotoGeneration.all_objects.all()

# Query only deleted
PhotoGeneration.objects.only_deleted()
```

---

## 🖥️ Admin Actions

| Action | What It Does | Reversible |
|--------|-------------|------------|
| **Soft delete selected items** | Marks records as deleted | ✅ Yes |
| **Restore selected items** | Undeletes records | ✅ Yes |
| **⚠️ PERMANENTLY delete** | Removes from database | ❌ No |

**Visual Indicators:**
- 🗑️ **DELETED** = Soft-deleted (can restore)
- ✓ **Active** = Normal record

---

## 💻 Management Commands

### Cleanup Old Deleted Records

```bash
# See what would be deleted (dry run)
python manage.py cleanup_soft_deleted --days=30 --dry-run

# Actually delete records older than 30 days
python manage.py cleanup_soft_deleted --days=30

# Only PhotoGeneration records
python manage.py cleanup_soft_deleted --days=90 --model=PhotoGeneration
```

### Restore Deleted Records

```bash
# List all deleted records
python manage.py restore_deleted --model=PhotoGeneration

# Restore specific record
python manage.py restore_deleted --model=PhotoGeneration --id=123

# Restore all (asks for confirmation)
python manage.py restore_deleted --model=PhotoGeneration --all
```

### View Deletion History

```bash
# Last 30 days
python manage.py view_deletion_history

# Last 90 days, PhotoGeneration only
python manage.py view_deletion_history --days=90 --model=PhotoGeneration

# Only restorations by admin user
python manage.py view_deletion_history --action=restored --user=admin
```

---

## 📊 Models with Soft Delete

✅ **PhotoGeneration** - User's photo generations
✅ **GenerationAudit** - Audit trail records

**New Model:**
📦 **DeletionHistory** - Tracks all delete/restore operations

---

## ⚙️ Automated Cleanup (Cron)

### Monthly cleanup of records deleted 90+ days ago

**Linux/Mac:**
```bash
# Add to crontab (crontab -e)
0 2 1 * * cd /path/to/app && python manage.py cleanup_soft_deleted --days=90
```

**Windows Task Scheduler:**
- Run: `python.exe manage.py cleanup_soft_deleted --days=90`
- Schedule: Monthly, 1st day, 2:00 AM

---

## 🔍 Query Examples

### Get All Active Records
```python
active = PhotoGeneration.objects.filter(user=request.user)
```

### Get All Including Deleted
```python
all_records = PhotoGeneration.all_objects.filter(user=request.user)
```

### Get Only Deleted
```python
deleted = PhotoGeneration.objects.only_deleted()
```

### Filter Active Records
```python
# This works as expected (only active)
recent = PhotoGeneration.objects.filter(
    created_at__gte=last_week
).order_by('-created_at')
```

---

## 🎯 Best Practices

### Retention Policy

| Model | Recommended Retention |
|-------|----------------------|
| PhotoGeneration | 90 days |
| GenerationAudit | 365 days |
| DeletionHistory | Never delete |

### When to Use

✅ **Use Soft Delete:**
- User-generated content
- Records that might need restoration
- Compliance-sensitive data

❌ **Use Hard Delete:**
- Temporary data (sessions, caches)
- Duplicate/spam records
- After retention period expires

### Performance Tips

- Default queries exclude deleted (fast)
- `.all_objects` includes deleted (slightly slower)
- Schedule cleanup during low-traffic hours
- Monitor database size growth

---

## 🐛 Quick Troubleshooting

**Problem**: Can't find record after deletion
**Solution**: Use `.all_objects` instead of `.objects`

**Problem**: Record still appears in list
**Solution**: Check `deleted_at` field - might not be actually deleted

**Problem**: Can't restore record
**Solution**: Check if it was hard deleted (irreversible)

**Problem**: Cleanup not deleting anything
**Solution**: Check if records are old enough (`--days` parameter)

---

## 📈 Monitoring Queries

```python
from generator.models import DeletionHistory
from django.db.models import Count

# Total deletions this month
DeletionHistory.objects.filter(
    action='deleted',
    performed_at__month=timezone.now().month
).count()

# Restoration rate
deleted = DeletionHistory.objects.filter(action='deleted').count()
restored = DeletionHistory.objects.filter(action='restored').count()
rate = (restored / deleted * 100) if deleted > 0 else 0

# Most deleted model
DeletionHistory.objects.values('model_name') \
    .annotate(count=Count('id')) \
    .order_by('-count')
```

---

## 🔐 Security Notes

- Only staff users can delete/restore via admin
- All operations are logged in DeletionHistory
- Deleted_by field tracks who performed action
- Reason field for accountability

---

## 📚 Full Documentation

See [SOFT_DELETE_GUIDE.md](SOFT_DELETE_GUIDE.md) for complete guide.

---

**Quick Help:**
- List deleted: `python manage.py restore_deleted --model=MODEL`
- View history: `python manage.py view_deletion_history`
- Cleanup old: `python manage.py cleanup_soft_deleted --dry-run`

**Status**: ✅ Production Ready  
**Version**: 1.0.0  
**Updated**: February 1, 2026
