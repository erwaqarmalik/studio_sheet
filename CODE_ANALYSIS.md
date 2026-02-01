# Code Analysis: Duplicates & Unused Code

## Summary
- **Total files analyzed**: 5 main files (app.js, views.py, api_views.py, urls.py, config.py)
- **Unused variables**: 3
- **Unused imports**: 2 (Python)
- **Duplicate event listener patterns**: None critical
- **Dead code**: None (all functions are used)

---

## JavaScript (app.js) - 950 lines

### ✅ UNUSED VARIABLES (3)

These variables are **defined but never used**:

#### 1. `PHOTO_W` and `PHOTO_H` (Lines 38-39)
```javascript
let PHOTO_W = CONFIG.photo_width_cm;  // ❌ UNUSED - immediately reassigned
let PHOTO_H = CONFIG.photo_height_cm; // ❌ UNUSED - immediately reassigned
```
- **Problem**: These are declared at module level then reassigned in `updatePhotoSize()`
- **Usage**: Only the reassigned values in `updatePhotoSize()` are used
- **Fix**: Remove initial declarations, or consolidate into the function scope
- **Lines**: 38-39, and lines 213 where they're overwritten

#### 2. `currentPhotoSize` (Line 40)
```javascript
let currentPhotoSize = 'passport_35x45';  // ❌ UNUSED INITIALLY
```
- **Problem**: Declared but only written to, never read from
- **Usage**: Only assigned in `updatePhotoSize()` but never used anywhere
- **Fix**: Remove this variable OR convert assignment to local scope in `updatePhotoSize()`
- **Evidence**: Grep shows it's only assigned once (line 40 init and line 201 in updatePhotoSize)
- **Note**: The value `'passport_35x45'` is only mentioned in these two places

#### 3. `customWidth` and `customHeight` (Lines 41-42)
```javascript
let customWidth = null;   // ❌ UNUSED (except for assignment)
let customHeight = null;  // ❌ UNUSED (except for assignment)
```
- **Problem**: Declared but only assigned, never read
- **Usage**: Values assigned to in `updatePhotoSize()` (lines 209-210) but never used
- **Should be**: Local variables in `updatePhotoSize()` instead of module-level
- **Reason for existence**: Likely artifact from refactoring

---

### ✅ ACCEPTABLE PATTERNS (Not Issues)

#### Debug Console Logs (Lines 60-67)
```javascript
console.log('Critical elements check:');
console.log('input:', !!input);
console.log('preview:', !!preview);
console.log('uploadZone:', !!uploadZone);
```
- ✅ **Acceptable**: Used for development debugging
- **Recommendation**: These can stay or be wrapped in `if (DEBUG)` mode

#### Element Existence Checks (Lines 84-89)
```javascript
if (!defaultPhotoSize) console.warn("defaultPhotoSize not found");
if (!customSizeContainer) console.warn("customSizeContainer not found");
```
- ✅ **Acceptable**: Defensive programming for missing HTML elements
- **No changes needed**

---

### ✅ ALL FUNCTIONS ARE USED

| Function | Lines | Used | Status |
|----------|-------|------|--------|
| `preventDefaults()` | 136 | Drop handler | ✅ |
| `handleDrop()` | 155 | Drop event | ✅ |
| `updatePhotoSize()` | 201 | Change listener | ✅ |
| `removeBackgroundAPI()` | 253 | BG removal button | ✅ |
| `safeNum()` | 294 | Grid calculation | ✅ |
| `formatFileSize()` | 299 | File preview | ✅ |
| `addFiles()` | 310 | File input handler | ✅ |
| `removeFile()` | 346 | Delete button | ✅ |
| `renderPreview()` | 367 | After all file ops | ✅ |
| `calculateGrid()` | 489 | Layout update | ✅ |
| `openCropModal()` | 529 | Crop button | ✅ |
| `closeCropModal()` | 699 | Modal close | ✅ |
| `openBgRemovalModal()` | 809 | BG remove button | ✅ |
| `closeBgRemovalModal()` | 833 | Modal close | ✅ |
| `updateFileInput()` | 921 | Before form submit | ✅ |

---

## Python (views.py) - 304 lines

### ✅ UNUSED IMPORTS (1)

```python
from .models import PhotoGeneration  # Line 15
```
- **Status**: ✅ **USED**
- **Location**: Line 247 - `PhotoGeneration.objects.create(...)`
- **No changes needed**

All other imports are actively used:
- ✅ `generate_pdf` - Line 232
- ✅ `generate_jpeg` - Line 243
- ✅ `zip_files` - Line 253
- ✅ `crop_to_passport_aspect_ratio` - Line 126
- ✅ `remove_background` - Line 143
- ✅ `PASSPORT_CONFIG` - Multiple uses
- ✅ `PHOTO_SIZES` - Line 110
- ✅ Validators - Lines 60-66

---

## Python (api_views.py) - 130 lines

### ✅ ALL IMPORTS USED

```python
import os          # ✅ Not used but acceptable (compatibility)
import io          # ✅ Line 67 - BytesIO()
import base64      # ✅ Line 50, 115 - b64decode/b64encode
import logging     # ✅ Line 54 - logger
import JsonResponse # ✅ Line 31+ - Multiple returns
```

### ✅ UNUSED VARIABLE (1)

```python
import os  # Line 6 - ❌ NEVER USED
```
- **Problem**: Imported but never referenced
- **Fix**: Remove line 6
- **Impact**: None - safe to remove

---

## Configuration Files

### ✅ config.py - CLEAN
- No unused variables or code
- Well-organized

### ✅ urls.py - CLEAN
- No unused patterns or code

---

## HTML (index.html) - 391 lines

### ✅ ALL ELEMENTS USED

Every element referenced in JavaScript is present:
- ✅ `passport-config-data` - Line 376
- ✅ `paper-sizes-data` - Line 378
- ✅ `photo-sizes-data` - Line 382
- ✅ `photoInput` - Form input
- ✅ `preview` - Preview grid
- ✅ All modal elements

---

## CSS (style.css)

### ✅ ALL STYLES USED

All CSS classes are applied in HTML or JavaScript:
- ✅ `.preview-card` - Generated in renderPreview()
- ✅ `.crop-badge` - Applied in renderPreview()
- ✅ `.bg-removed-badge` - Applied in renderPreview()
- ✅ All Bootstrap utilities used

---

# RECOMMENDATIONS

## High Priority - Remove (5 lines)

### 1. Remove unused Python import
**File**: `generator/api_views.py` Line 6
```python
# REMOVE THIS LINE:
import os
```
**Why**: Never used, safe to remove

---

## Medium Priority - Refactor (3 variables)

### 2. Fix JavaScript unused variables
**File**: `generator/static/generator/app.js`

**Option A: Consolidate into function scope** (Recommended)
```javascript
// REMOVE Lines 38-42:
let PHOTO_W = CONFIG.photo_width_cm;
let PHOTO_H = CONFIG.photo_height_cm;
let currentPhotoSize = 'passport_35x45';
let customWidth = null;
let customHeight = null;

// CHANGE updatePhotoSize() to declare these locally:
function updatePhotoSize() {
    let currentPhotoSize = defaultPhotoSize.value;
    let PHOTO_W, PHOTO_H, customWidth, customHeight;
    
    if (currentPhotoSize === 'custom') {
        customSizeContainer.style.display = 'block';
        customWidth = parseFloat(customWidthInput.value) || 3.5;
        customHeight = parseFloat(customHeightInput.value) || 4.5;
        // ... rest unchanged
    }
    // ... rest unchanged
}
```

**Option B: Just remove initialization**
```javascript
// Lines 38-42 become:
let PHOTO_W;
let PHOTO_H;
let currentPhotoSize;
```

**Recommendation**: Use Option A (consolidate to function scope) as these are only used within `updatePhotoSize()` and the grid calculation.

---

## Low Priority - Keep (Acceptable)

✅ **Keep debug console.logs** - Useful for development
✅ **Keep defensive element checks** - Good practice
✅ **Keep all error handling** - Important for UX
✅ **Keep all comments** - Well documented

---

# SUMMARY TABLE

| Category | Count | Status |
|----------|-------|--------|
| Unused Imports | 1 | ✅ Can Remove |
| Unused Variables | 4 | ⚠️ Should Refactor |
| Unused Functions | 0 | ✅ All Used |
| Duplicate Code | 0 | ✅ None Found |
| Dead Code | 0 | ✅ None Found |
| **Total Lines to Clean**: | **~10** | **Low Impact** |

---

## Code Quality Assessment

| Metric | Status | Notes |
|--------|--------|-------|
| **Overall Quality** | ✅ GOOD | Well-structured, intentional |
| **Maintainability** | ✅ GOOD | Clear function separation |
| **Performance** | ✅ GOOD | No redundant operations |
| **Security** | ✅ GOOD | Proper CSRF exemption, input validation |
| **Testing Readiness** | ✅ GOOD | Functions are independent and testable |

---

## Conclusion

The codebase is **exceptionally clean**. The unused variables identified are minor artifacts from initial development that don't impact functionality. The suggested refactoring would improve code clarity by 5-10 lines but is not critical.

**Recommended Action**: Optional cleanup during next maintenance cycle. No urgent changes needed.
