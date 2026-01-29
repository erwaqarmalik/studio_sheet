# Variable Photo Sizes - Quick Reference

## What's New?

Instead of fixed 3.5×4.5 cm photos for all images, users can now:
- ✅ Choose different photo sizes (10 presets available)
- ✅ Configure copies per photo individually
- ✅ Use custom dimensions (1-20 cm range)

## Available Photo Size Presets

| ID | Size | Dimensions | Category |
|---|---|---|---|
| passport_35x45 | Passport | 3.5×4.5 cm | Standard |
| passport_small | Small Passport | 2.5×3.5 cm | Standard |
| id_card | ID Card | 3.0×4.0 cm | Standard |
| visa_3x4 | Visa | 3.0×4.0 cm | Visa |
| visa_4x6 | Visa Large | 4.0×6.0 cm | Visa |
| uk_visa | UK Visa | 4.45×5.59 cm | Visa |
| us_visa | US Passport | 5.0×5.0 cm | Visa |
| schengen | Schengen | 3.5×4.5 cm | Visa |
| australia | Australia | 4.5×5.5 cm | Visa |
| canada | Canada | 3.5×4.5 cm | Visa |
| custom | Custom Size | User-defined | Custom |

## Database Model

### PhotoConfiguration
```
Attributes:
- generation (FK): Parent PhotoGeneration
- photo_index: 0-based position in batch
- photo_size: Preset key or 'custom'
- custom_width_cm: Width for custom size (optional)
- custom_height_cm: Height for custom size (optional)
- copies: Number of copies (1-100)

Methods:
- get_actual_dimensions() → (width, height) tuple
```

## Admin Interface

Access photo configurations via:
1. Django Admin → Photo Generation
2. Click on a photo generation record
3. View/edit associated photos in "Photo Configuration" section

## Forms

### PassportForm (Global Settings)
```python
default_photo_size  # Default size for all photos
default_copies      # Default copies for all photos
```

### PhotoConfigurationForm (Per-Photo)
```python
photo_size          # Dropdown: preset or 'custom'
custom_width_cm     # Only if photo_size = 'custom'
custom_height_cm    # Only if photo_size = 'custom'
copies              # 1-100 copies
```

## Config File Structure

### generator/config.py
```python
PHOTO_SIZES = {
    "preset_key": {
        "width": 3.5,
        "height": 4.5,
        "label": "Display Name",
        "category": "Category Name"
    },
    ...
}

PASSPORT_CONFIG = {
    "default_photo_size": "passport_35x45",
    "default_copies": 6,
    # ... other settings
}
```

## Implementation Checklist

### Phase 1: Backend Infrastructure ✅ COMPLETE
- [x] Config: PHOTO_SIZES with presets
- [x] Model: PhotoConfiguration created
- [x] Forms: PassportForm + PhotoConfigurationForm
- [x] Admin: PhotoConfigurationInline
- [x] Migration: 0005_photoconfiguration applied
- [x] Validation: Custom size constraints

### Phase 2: Frontend UI (TODO)
- [ ] Update index.html with size selection UI
- [ ] Add per-photo configuration panel
- [ ] JavaScript for size switching
- [ ] Show/hide custom dimension inputs
- [ ] Live layout preview updates

### Phase 3: Backend Processing (TODO)
- [ ] Update views.py to handle per-photo configs
- [ ] Create PhotoConfiguration records
- [ ] Variable aspect ratio cropping
- [ ] Layout calculation for mixed sizes
- [ ] PDF/Image generation with multiple sizes

## Code Examples

### Get Photo Dimensions
```python
config = PhotoConfiguration.objects.get(generation=gen, photo_index=0)
width_cm, height_cm = config.get_actual_dimensions()
# Returns: (3.5, 4.5) for preset, or (custom_w, custom_h) for custom
```

### Create Photo Configuration
```python
photo_config = PhotoConfiguration.objects.create(
    generation=photo_gen,
    photo_index=0,
    photo_size="passport_35x45",
    copies=6
)

# Custom size
custom_config = PhotoConfiguration.objects.create(
    generation=photo_gen,
    photo_index=1,
    photo_size="custom",
    custom_width_cm=4.0,
    custom_height_cm=5.0,
    copies=3
)
```

### Query All Photos in Generation
```python
photos = PhotoConfiguration.objects.filter(
    generation=photo_gen
).order_by('photo_index')

for photo in photos:
    print(f"Photo {photo.photo_index}: {photo.photo_size}, {photo.copies} copies")
    w, h = photo.get_actual_dimensions()
    print(f"  Dimensions: {w}×{h} cm")
```

## Key Constraints

- **Copy Count**: 1-100 copies per photo
- **Custom Width**: 1-20 cm
- **Custom Height**: 1-20 cm
- **Photo Index**: Unique per generation
- **Database**: One PhotoConfiguration per photo

## Backward Compatibility

✅ **Fully backward compatible**
- Existing PhotoGeneration records unchanged
- Default size still 3.5×4.5 cm
- New model is optional (gradual adoption)
- No breaking changes to existing API

## Database Indexes

```sql
-- Fast queries by generation and photo index
CREATE INDEX idx_generation_photo ON PhotoConfiguration(generation_id, photo_index);

-- Unique constraint: one config per photo position
CREATE UNIQUE INDEX idx_gen_photo_unique ON PhotoConfiguration(generation_id, photo_index);
```

## Testing

```python
# Verify model creation
from generator.models import PhotoConfiguration
config = PhotoConfiguration.objects.first()
assert config.get_actual_dimensions() == (3.5, 4.5)

# Test custom sizes
config = PhotoConfiguration(
    photo_size="custom",
    custom_width_cm=5.0,
    custom_height_cm=7.0
)
assert config.get_actual_dimensions() == (5.0, 7.0)
```

## Migration Info

**Migration File**: `generator/migrations/0005_photoconfiguration.py`
**Status**: Applied ✅
**Reversible**: Yes (can rollback if needed)
**Data Loss**: None (no data migration)

## File Changes Summary

| File | Changes | Lines |
|---|---|---|
| generator/config.py | Added PHOTO_SIZES dict | +40 |
| generator/models.py | Added PhotoConfiguration model | +65 |
| generator/forms.py | Added PassportForm fields + PhotoConfigurationForm | +95 |
| generator/admin.py | Added PhotoConfigurationInline | +50 |
| generator/migrations/0005_photoconfiguration.py | New migration | Auto-generated |
| VARIABLE_PHOTO_SIZES_FEATURE.md | Comprehensive documentation | New file |

## Total Lines Added: ~300 lines of production code

---

**Commit**: 42d17f5
**Date**: Today
**Feature Status**: 🔵 Infrastructure Complete - Phase 1 of 3
