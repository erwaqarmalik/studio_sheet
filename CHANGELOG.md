# Changelog

## [Improvements Implemented] - 2026-01-27

### Security Enhancements
- **SECRET_KEY validation**: Now requires proper SECRET_KEY in production, exits if insecure default is used
- **DEBUG mode**: Changed default from `True` to `False` for security
- **Production security headers**: Added SSL redirect, secure cookies, HSTS, XSS protection when DEBUG=False
- **Environment configuration**: Created `.env.example` with all required settings
- **Rate limiting configuration**: Added RATE_LIMIT_PER_HOUR setting (infrastructure for rate limiting)

### File Management
- **Cleanup management command**: Added `python manage.py cleanup_old_files` to delete old generated files
  - Configurable retention period (default 24 hours)
  - Dry-run mode for testing
  - Detailed logging of deleted files and freed space
- **Configurable file size**: MAX_FILE_SIZE_MB now configurable via environment

### Code Quality
- **Type hints**: Added comprehensive type hints to all functions in validators.py and views.py
- **Better validation**: 
  - Added image dimension validation (min/max)
  - Server-side numeric field validation with bounds checking
  - Copies list validation with reasonable limits (max 100)
  - File count limit (max 50 files per upload)
  - Better error messages with specific details
- **Improved error handling**: More specific ValidationError messages throughout

### Testing
- **Comprehensive test suite**: Created `generator/tests.py` with 25+ unit tests covering:
  - File validators (valid/invalid files, sizes, dimensions)
  - Numeric validators
  - Utility functions (grid calculations, cropping, conversions)
  - View endpoints
  - Configuration integrity

### Monitoring & Logging
- **Request logging middleware**: Tracks all requests with timing information
- **Structured logging**: Better log messages throughout application
- **Exception logging**: Automatic exception logging in middleware

### Developer Experience
- **Requirements file**: Added `requirements.txt` with all dependencies
- **Comprehensive README**: Created detailed README_NEW.md with:
  - Installation instructions
  - Configuration guide
  - Deployment instructions
  - Testing guide
  - Troubleshooting section
  - API documentation
- **Deployment notes**: Added production configuration examples

### Validation Improvements
- Paper size validation (must be in PAPER_SIZES)
- Orientation validation (must be portrait/landscape)
- Numeric bounds checking (margins, gaps: 0.0-5.0 cm)
- Better file validation with detailed error messages

## Recommended Next Steps

### High Priority
1. **Implement rate limiting**: Use django-ratelimit or similar
2. **Add user authentication**: Optional user accounts for history tracking
3. **Database migration**: Move from SQLite to PostgreSQL for production
4. **Error monitoring**: Integrate Sentry or similar service
5. **Add CSRF token verification**: Explicit checks in POST handlers

### Medium Priority
1. **Image optimization**: Compress images before processing
2. **Async processing**: Use Celery for large batch jobs
3. **Caching**: Add Redis for grid calculations
4. **Batch operations**: Select all, delete all functionality
5. **Image rotation**: Allow users to rotate uploaded images

### Nice to Have
1. **Preset templates**: Common passport photo layouts
2. **EXIF data handling**: Preserve/strip metadata
3. **Multiple output formats**: Add PNG, TIFF support
4. **API versioning**: Prepare for API expansion
5. **Accessibility improvements**: Full ARIA labels and keyboard navigation

## Breaking Changes
None - all changes are backward compatible

## Migration Notes
1. Copy `.env.example` to `.env` and configure
2. Run `python manage.py migrate` (no new migrations, but good practice)
3. Run `python manage.py test` to verify installation
4. Set up cleanup cron job/scheduled task
5. Review security settings in settings.py
