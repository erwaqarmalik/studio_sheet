# Production deployment configuration

# Add to settings.py for production database (PostgreSQL)
"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}
"""

# Gunicorn configuration (gunicorn.conf.py)
"""
bind = "0.0.0.0:8000"
workers = 3
worker_class = "sync"
timeout = 120
keepalive = 5
errorlog = "/var/log/gunicorn/error.log"
accesslog = "/var/log/gunicorn/access.log"
loglevel = "info"
"""

# Systemd service file (/etc/systemd/system/passport_app.service)
"""
[Unit]
Description=Passport Photo Generator
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/passport_app
Environment="PATH=/var/www/passport_app/venv/bin"
ExecStart=/var/www/passport_app/venv/bin/gunicorn passport_app.wsgi:application --bind unix:/run/passport_app.sock

[Install]
WantedBy=multi-user.target
"""
