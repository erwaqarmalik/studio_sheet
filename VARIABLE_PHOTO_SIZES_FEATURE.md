# Variable Photo Sizes Feature Implementation

## Overview
This document describes the new feature that allows users to select different photo sizes and configure the number of copies for each photo, instead of using fixed 3.5×4.5 cm dimensions for all photos.

## Completed Changes

### 1. Configuration Updates (`generator/config.py`)
**File:** [generator/config.py](generator/config.py)

Added `PHOTO_SIZES` dictionary with 10 preset options:
```python
PHOTO_SIZES = {
    "passport_35x45": {"width": 3.5, "height": 4.5, "label": "Passport (3.5×4.5 cm)"},
    "passport_small": {"width": 2.5, "height": 3.5, "label": "Small Passport (2.5×3.5 cm)"},
    "id_card": {"width": 3.0, "height": 4.0, "label": "ID Card (3.0×4.0 cm)"},
    "visa_3x4": {"width": 3.0, "height": 4.0, "label": "Visa (3.0×4.0 cm)"},
    "visa_4x6": {"width": 4.0, "height": 6.0, "label": "Visa Large (4.0×6.0 cm)"},
    "uk_visa": {"width": 4.45, "height": 5.59, "label": "UK Visa (4.45×5.59 cm)"},
    "us_visa": {"width": 5.0, "height": 5.0, "label": "US Passport (5.0×5.0 cm)"},
    "schengen": {"width": 3.5, "height": 4.5, "label": "Schengen (3.5×4.5 cm)"},
    "australia": {"width": 4.5, "height": 5.5, "label": "Australia (4.5×5.5 cm)"},
    "canada": {"width": 3.5, "height": 4.5, "label": "Canada (3.5×4.5 cm)"},
    "custom": {"width": None, "height": None, "label": "Custom Size"},
}
```

Maintains backward compatibility with default 3.5×4.5 cm in `PASSPORT_CONFIG`.

### 2. Database Model - PhotoConfiguration (`generator/models.py`)
**File:** [generator/models.py](generator/models.py)

Created new `PhotoConfiguration` model (lines ~350-410) with:
- `generation` (FK to PhotoGeneration): Links to parent batch
- `photo_index` (IntegerField): Position in batch (0-based)
- `photo_size` (CharField): Selected preset size key
- `custom_width_cm` (FloatField, optional): Custom width (1-20cm range)
- `custom_height_cm` (FloatField, optional): Custom height (1-20cm range)
- `copies` (IntegerField): Number of copies (1-100) for this photo
- `get_actual_dimensions()` method: Returns actual width/height tuple

**Key Features:**
- One-to-many relationship: PhotoGeneration → PhotoConfiguration (multiple photos)
- Unique constraint: (generation, photo_index) ensures no duplicates
- Validation: Custom size requires both width and height
- Full index coverage for optimal queries

### 3. Forms (`generator/forms.py`)
**File:** [generator/forms.py](generator/forms.py)

#### Updated PassportForm
Added fields:
- `default_photo_size` (ChoiceField): Global default size for all photos
- `default_copies` (IntegerField): Global default copies per photo

#### New PhotoConfigurationForm
Form for configuring individual photos with:
- `photo_size`: Dropdown with all available sizes
- `custom_width_cm`, `custom_height_cm`: Hidden by default, shown only for custom size
- `copies`: Number input (1-100)

Validation ensures:
- Custom size requires both dimensions
- Dimensions within valid range
- Copy count within limits

### 4. Admin Interface (`generator/admin.py`)
**File:** [generator/admin.py](generator/admin.py)

Added `PhotoConfigurationInline`:
- Shows photos associated with each generation
- Editable inline with photo_size, dimensions, and copies
- Read-only photo_index to prevent modifications

Integrated into `PhotoGenerationAdmin`:
- View all photos in a generation
- Edit individual photo configurations
- Visual layout with tabular display

### 5. Database Migration
**File:** [generator/migrations/0005_photoconfiguration.py](generator/migrations/0005_photoconfiguration.py)

Migration creates:
- `PhotoConfiguration` model table
- Foreign key to PhotoGeneration
- Unique index on (generation, photo_index)
- Indexes for optimal query performance

## Frontend Implementation (TODO)

### UI Changes Needed in `index.html`

1. **Photo Size Selection Section** - Add after upload
   - Global default size selector
   - Global default copies input
   - Option to override per-photo

2. **Per-Photo Configuration Panel**
   - Display uploaded photos in grid
   - For each photo:
     - Photo size dropdown
     - Custom width/height inputs (hidden unless custom selected)
     - Copies counter (+/- buttons)
   - Live preview of layout changes

3. **JavaScript Updates** (`app.js`)
   - Handle photo size changes and recalculate layout
   - Show/hide custom size inputs
   - Update live statistics dynamically
   - Validate custom dimensions before submission

### Backend Updates (TODO)

1. **Views** (`views.py`)
   - Parse per-photo configurations from form
   - Save PhotoConfiguration records
   - Update `crop_to_passport_aspect_ratio()` to accept variable sizes
   - Handle multiple aspect ratios in single batch
   - Recalculate layout with variable photo sizes

2. **Photo Processing**
   - Update cropping logic for different aspect ratios
   - Maintain quality across different sizes
   - Proper scaling and positioning

3. **PDF/Image Generation**
   - Handle multiple photo sizes in single output
   - Proper layout calculation
   - Optimize spacing for mixed sizes

## User Workflow

### Current User Flow
1. Upload photos
2. Crop each photo to 3.5×4.5 cm (fixed)
3. Select layout options (paper size, gaps, margins)
4. Generate output

### New User Flow
1. Upload photos
2. Crop each photo (new aspect ratio selected per-photo)
3. **NEW:** For each photo:
   - Select photo size (preset or custom)
   - If custom, enter width and height
   - Specify number of copies
4. Select layout options
5. Generate output with mixed sizes

## Testing Checklist

- [ ] Admin interface displays PhotoConfiguration correctly
- [ ] Custom size fields hidden by default, shown only for custom
- [ ] Validation prevents invalid custom sizes
- [ ] PhotoConfiguration properly linked to PhotoGeneration
- [ ] Migration applied successfully
- [ ] No conflicts with existing data
- [ ] Form validation works for per-photo configs
- [ ] Multiple photo batches work independently
- [ ] Per-photo configuration persists after save

## Performance Considerations

- Added database indexes for fast queries by (generation, photo_index)
- Lazy loading of photo configurations with PhotoGeneration
- Efficient bulk operations via inline admin
- One query per generation to fetch all photo configs

## API Contract Changes

### PhotoGeneration Model Changes
- `num_photos`: Now represents count in PhotoConfiguration records
- `total_copies`: Now sum of all PhotoConfiguration.copies

### New API for Views
```python
# Get configuration for a photo
config = PhotoConfiguration.objects.get(generation=gen, photo_index=0)
width, height = config.get_actual_dimensions()
copies = config.copies
```

## Backward Compatibility

- Existing PhotoGeneration records remain unchanged
- Default photo size is still 3.5×4.5 cm
- Existing views will work with 1:1 mapping (1 photo = 1 PhotoConfiguration)
- Can be extended to support batch configurations later

## Future Enhancements

1. **Batch Size Templates**: Save and reuse configurations
2. **Layout Optimization**: Auto-arrange mixed sizes for minimal waste
3. **Export Configurations**: Save size/copy configs for reuse
4. **Presets Manager**: Custom size presets per user
5. **API Endpoints**: For third-party integrations
6. **Bulk Operations**: Apply size changes to multiple photos

## Migration Steps for Live Server

1. Run `python manage.py migrate` to create PhotoConfiguration table
2. No data migration needed (PhotoConfiguration is optional)
3. Update Django app code with new forms and views
4. Test with new photo batch
5. Existing photosheets remain unaffected

## Model Relationships

```
User (1)
  ↓
  └─ PhotoGeneration (*)
      ├─ session_id (unique)
      ├─ output_path
      ├─ output_url
      └─ PhotoConfiguration (*)
          ├─ photo_index (0-based)
          ├─ photo_size
          ├─ custom_width_cm (optional)
          ├─ custom_height_cm (optional)
          └─ copies
```

## Configuration File Changes

### Before
```python
PASSPORT_CONFIG = {
    "photo_width_cm": 3.5,
    "photo_height_cm": 4.5,
    ...
}
```

### After
```python
PHOTO_SIZES = { ... 10 presets ... }

PASSPORT_CONFIG = {
    "default_photo_size": "passport_35x45",
    "photo_width_cm": 3.5,  # Still here for backward compat
    "photo_height_cm": 4.5, # Still here for backward compat
    ...
}
```

## Implementation Priority

1. ✅ Config structure (PHOTO_SIZES)
2. ✅ Database model (PhotoConfiguration)
3. ✅ Forms (PassportForm updates, PhotoConfigurationForm)
4. ✅ Admin interface (PhotoConfigurationInline)
5. ✅ Database migration
6. ⏳ Frontend UI (index.html)
7. ⏳ JavaScript logic (app.js)
8. ⏳ Backend views (views.py)
9. ⏳ Image processing updates
10. ⏳ Testing and optimization

## Next Steps

1. **Frontend Implementation**: Update index.html with per-photo configuration UI
2. **JavaScript Enhancement**: Add logic for photo size selection and layout preview
3. **Backend Processing**: Update views.py to handle variable photo sizes
4. **Image Processing**: Modify cropping and layout generation for mixed sizes
5. **Testing**: Comprehensive testing with various size combinations
6. **Documentation**: Create user guide and admin documentation

---

**Status**: Backend infrastructure complete ✅ | Frontend pending ⏳

**Last Updated**: Today
**Implementation Phase**: Infrastructure Complete (Phase 1)
