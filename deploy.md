# Deployment Guide

## Stack

- **Runtime:** Python 3.11+
- **Framework:** Django 5.0 + Django REST Framework
- **App server:** Gunicorn (included in production requirements)
- **Database:** PostgreSQL (SQLite for local dev only)
- **Media files:** Local filesystem or object storage (S3-compatible)
- **Reverse proxy:** Nginx (recommended)

---

## Environment Variables

Create a `.env` file at the project root (never commit it). All variables below are required in production.

```env
# Django core
DJANGO_SECRET_KEY=<64-character random string>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_SETTINGS_MODULE=config.settings.production

# Database (PostgreSQL)
DATABASE_URL=postgres://USER:PASSWORD@HOST:5432/DB_NAME

# CORS — comma-separated list of frontend origins
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Media files
MEDIA_URL=/media/
MEDIA_ROOT=/var/www/iyyah/media

# Timezone
TIME_ZONE=Africa/Dar_es_Salaam

# Optional: Sentry error tracking (production requirements include sentry-sdk)
SENTRY_DSN=https://...@sentry.io/...
```

Generate a secure `DJANGO_SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## First-Time Server Setup

### 1. Clone and install dependencies

```bash
git clone git@github.com:troubleman96/fingerprint-project-API.git
cd fingerprint-project-API
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/production.txt
```

### 2. Create the `.env` file

Copy the template above and fill in real values.

### 3. Run migrations

```bash
python manage.py migrate
```

### 4. Collect static files

```bash
python manage.py collectstatic --noinput
```

### 5. Seed initial data (first deploy only)

```bash
python manage.py seed
```

To wipe and re-seed from scratch:
```bash
python manage.py seed --flush
```

### 6. Create a superuser (optional — seed already creates admin@email.com)

```bash
python manage.py createsuperuser
```

---

## Running with Gunicorn

```bash
source .venv/bin/activate
gunicorn config.wsgi:application \
  --workers 3 \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile /var/log/iyyah/access.log \
  --error-logfile /var/log/iyyah/error.log
```

**Worker count rule of thumb:** `(2 × CPU cores) + 1`

---

## Systemd Service (recommended)

Create `/etc/systemd/system/iyyah-api.service`:

```ini
[Unit]
Description=Iyyah API (Gunicorn)
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/iyyah/API
EnvironmentFile=/var/www/iyyah/API/.env
ExecStart=/var/www/iyyah/API/.venv/bin/gunicorn config.wsgi:application \
          --workers 3 \
          --bind unix:/run/iyyah-api.sock \
          --timeout 120 \
          --access-logfile /var/log/iyyah/access.log \
          --error-logfile /var/log/iyyah/error.log
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable iyyah-api
sudo systemctl start iyyah-api
sudo systemctl status iyyah-api
```

---

## Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    client_max_body_size 20M;

    location /api/ {
        proxy_pass         http://unix:/run/iyyah-api.sock;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }

    location /media/ {
        alias /var/www/iyyah/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /static/ {
        alias /var/www/iyyah/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Test and reload:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## Deploying Updates

```bash
cd /var/www/iyyah/API
git pull origin master
source .venv/bin/activate
pip install -r requirements/production.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
sudo systemctl restart iyyah-api
```

---

## Development Server (local only)

```bash
source .venv/bin/activate
# or on this machine:
.venv/bin/python manage.py runserver
```

Uses `config.settings.development` automatically via `manage.py`. SQLite is the default database when `DATABASE_URL` is not set.

---

## Credentials (seeded defaults — change in production)

| Email | Password | Role |
|---|---|---|
| admin@email.com | Iyyah@2024 | ADMIN |
| officer@email.com | Iyyah@2024 | OFFICER |
| staff@email.com | Iyyah@2024 | STAFF |
| reviewer@email.com | Iyyah@2024 | OFFICER |
| support@email.com | Iyyah@2024 | STAFF |

Change all passwords immediately after first login on any production or staging environment.

---

## Key URLs

| URL | Purpose |
|---|---|
| `/api/` | API root |
| `/api/docs/` | API documentation |
| `/api/schema/` | OpenAPI schema (JSON) |
| `/admin/` | Django admin panel |

---

## Settings Reference

| Setting | File | Notes |
|---|---|---|
| Development | `config/settings/development.py` | `DEBUG=True`, `ALLOWED_HOSTS=*`, SQLite default |
| Production | `config/settings/production.py` | `DEBUG=False`, HTTPS forced, HSTS enabled |
| `DJANGO_SETTINGS_MODULE` | `.env` | Must be set to `config.settings.production` on server |

The `wsgi.py` defaults to `config.settings.production`, so Gunicorn picks up the right settings automatically as long as the `.env` is present.
