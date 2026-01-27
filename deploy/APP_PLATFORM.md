# DigitalOcean App Platform Deployment (Alternative)

App Platform is a managed PaaS. However, this app writes user uploads and generated files to `media/`. App Platform file system is ephemeral, so use a persistent volume or DigitalOcean Spaces for media. Alternatively, switch to a Droplet (see DO_DROPLET_SETUP.md).

## Option A: Quick start (best for stateless demos)
1. Push repo to GitHub/GitLab.
2. Create App in App Platform → select your repo.
3. Environment:
   - Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - Run Command: `gunicorn passport_app.wsgi:application --bind 0.0.0.0:$PORT --workers 3`
4. Add Environment Variables:
   - `SECRET_KEY` (required)
   - `DEBUG` = `False`
   - `ALLOWED_HOSTS` = your app domain
   - `MAX_FILE_SIZE_MB`, `FILE_CLEANUP_HOURS`, `RATE_LIMIT` as needed
5. Static files: App Platform will serve `/static/` from `staticfiles/` if present after `collectstatic`.
6. Media uploads: Not persisted across deploys. Use Spaces (S3-compatible) via `django-storages` for production.

## Option B: Containerized
- Create a `Dockerfile` that runs `collectstatic` and starts Gunicorn.
- Add a volume mount for `/app/media` if you enable persistent storage.

## Recommended for production
- Use Droplet + Nginx (see DO_DROPLET_SETUP.md), or
- Configure `django-storages` + Spaces for media and use App Platform.
