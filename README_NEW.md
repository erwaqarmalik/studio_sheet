# Passport Photo Generator

A Django web application that helps users create passport-sized photo sheets from uploaded photos. Upload photos, customize layout options, and download professionally formatted PDF or JPEG sheets.

## Features

- **Photo Upload**: Drag-and-drop or click to upload multiple photos (JPG, PNG)
- **Smart Cropping**: Interactive cropping with Cropper.js to match passport photo aspect ratio (3.5×4.5 cm)
- **Flexible Layouts**: 
  - Multiple paper sizes (A4, A3, Letter)
  - Portrait or landscape orientation
  - Customizable margins, gaps, and copy counts
  - Optional cut lines for easy trimming
- **Multiple Output Formats**: PDF or high-resolution JPEG (300 DPI)
- **Live Preview**: Real-time calculation of photos per page
- **Responsive Design**: Works on desktop and mobile devices

## Requirements

- Python 3.8+
- Django 5.0+
- Pillow 10.0+
- ReportLab 4.0+

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd passport_app
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and set your configuration:

```env
SECRET_KEY=your-secret-key-here-generate-a-strong-one
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
MAX_FILE_SIZE_MB=10
FILE_CLEANUP_HOURS=24
RATE_LIMIT=100
```

**Important**: Generate a strong SECRET_KEY for production:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create Required Directories

```bash
mkdir -p logs media/uploads media/outputs
```

### 7. Run Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` in your browser.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key (required) | None |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Comma-separated host list | `localhost,127.0.0.1` |
| `MAX_FILE_SIZE_MB` | Maximum upload size per file | `10` |
| `FILE_CLEANUP_HOURS` | Hours before old files are deleted | `24` |
| `RATE_LIMIT` | Max requests per hour | `100` |

### Photo Settings

Default settings in `generator/config.py`:

- **Photo Size**: 3.5 × 4.5 cm (standard passport size)
- **Default Paper**: A4 portrait
- **Default Margins**: 1.0 cm
- **Default Gaps**: 0.5 cm column, 0.5 cm row
- **Output DPI**: 300 (JPEG)

## File Cleanup

Generated files are stored in `media/outputs/<session_id>/`. To prevent disk space issues, run the cleanup command regularly:

### Manual Cleanup

```bash
# Delete files older than 24 hours (default)
python manage.py cleanup_old_files

# Delete files older than 48 hours
python manage.py cleanup_old_files --hours=48

# Dry run (see what would be deleted)
python manage.py cleanup_old_files --dry-run
```

### Automated Cleanup (Linux/macOS)

Add to crontab:
```bash
# Run cleanup daily at 2 AM
0 2 * * * cd /path/to/passport_app && /path/to/venv/bin/python manage.py cleanup_old_files
```

### Automated Cleanup (Windows)

Create a scheduled task using Task Scheduler to run:
```powershell
cd C:\path\to\passport_app
venv\Scripts\python.exe manage.py cleanup_old_files
```

## Testing

### Run All Tests

```bash
python manage.py test
```

### Run Specific Test Class

```bash
python manage.py test generator.tests.ValidatorTests
```

### Run with Coverage

```bash
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

## Production Deployment

### Security Checklist

- [ ] Set strong `SECRET_KEY` in `.env`
- [ ] Set `DEBUG=False` in `.env`
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Use HTTPS (SSL certificates)
- [ ] Set up file cleanup automation
- [ ] Configure rate limiting
- [ ] Set up monitoring and error tracking
- [ ] Use a proper database (PostgreSQL recommended)
- [ ] Set up regular backups

### Using Gunicorn

1. Install Gunicorn:
```bash
pip install gunicorn
```

2. Run with Gunicorn:
```bash
gunicorn passport_app.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/passport_app/staticfiles/;
    }

    location /media/ {
        alias /path/to/passport_app/media/;
    }
}
```

### Collect Static Files

```bash
python manage.py collectstatic --noinput
```

## API Endpoints

### GET `/`
Display the upload form

### POST `/`
Process uploaded photos and generate output

**Parameters:**
- `photos[]`: Uploaded photo files (required)
- `paper_size`: Paper size - "A4", "A3", or "Letter" (default: "A4")
- `orientation`: "portrait" or "landscape" (default: "portrait")
- `margin_cm`: Margin in cm (0.0-5.0, default: 1.0)
- `col_gap_cm`: Column gap in cm (0.0-5.0, default: 0.5)
- `row_gap_cm`: Row gap in cm (0.0-5.0, default: 0.5)
- `cut_lines`: "yes" or "no" (default: "yes")
- `output_type`: "PDF" or "JPEG" (default: "PDF")
- `copies[]`: Array of copy counts per photo (default: 1 each)

## Project Structure

```
passport_app/
├── generator/              # Main application
│   ├── management/         # Management commands
│   │   └── commands/
│   │       └── cleanup_old_files.py
│   ├── static/generator/   # Static files
│   │   ├── app.js         # Frontend logic
│   │   └── style.css      # Styles
│   ├── templates/generator/
│   │   └── index.html     # Main template
│   ├── config.py          # Configuration constants
│   ├── forms.py           # Django forms
│   ├── middleware.py      # Custom middleware
│   ├── models.py          # Database models (empty)
│   ├── tests.py           # Unit tests
│   ├── urls.py            # URL routing
│   ├── utils.py           # Image processing utilities
│   ├── validators.py      # Input validators
│   ├── views.py           # View logic
│   └── widgets.py         # Form widgets
├── passport_app/          # Project settings
│   ├── settings.py        # Django settings
│   ├── urls.py            # Root URL config
│   └── wsgi.py            # WSGI application
├── logs/                  # Application logs
├── media/                 # User uploads and outputs
│   ├── uploads/
│   └── outputs/
├── .env                   # Environment variables (create from .env.example)
├── .env.example           # Example environment config
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Troubleshooting

### Images not cropping correctly
- Ensure uploaded images meet minimum dimensions (100×100 px)
- Check browser console for JavaScript errors
- Verify Cropper.js is loading from CDN

### File upload fails
- Check `MAX_FILE_SIZE_MB` setting
- Verify `media/uploads/` directory is writable
- Check Django logs in `logs/django.log`

### Generated files not appearing
- Verify `media/outputs/` directory is writable
- Check for errors in `logs/django.log`
- Ensure sufficient disk space

### Permission errors
```bash
chmod -R 755 media/ logs/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review logs in `logs/django.log`

## Acknowledgments

- [Django](https://www.djangoproject.com/)
- [Pillow](https://python-pillow.org/)
- [ReportLab](https://www.reportlab.com/)
- [Cropper.js](https://fengyuanchen.github.io/cropperjs/)
