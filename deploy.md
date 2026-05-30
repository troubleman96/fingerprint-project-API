# Deployment Guide

## Stack

- **Runtime:** Python 3.11+
- **Framework:** Django 5.0 + Django REST Framework
- **App server:** Gunicorn (included in production requirements)
- **Database:** PostgreSQL (SQLite for local dev only)
- **Media files:** Local filesystem
- **Reverse proxy:** Nginx
- **Server:** `captainhugo@vps3376277`
- **API domain:** `https://api-finger-print.simamia.online`
- **Project path:** `~/projects/finger-print/API`

---

## Environment Variables

Create a `.env` file at `~/projects/finger-print/API/.env` (never commit it).

```env
# Django core
DJANGO_SECRET_KEY=<64-character random string>
DEBUG=False
ALLOWED_HOSTS=api-finger-print.simamia.online
DJANGO_SETTINGS_MODULE=config.settings.production

# Database (PostgreSQL)
DATABASE_URL=postgres://USER:PASSWORD@localhost:5432/fingerprint_db

# CORS — UI origin(s)
CORS_ALLOWED_ORIGINS=https://finger-print.simamia.online

# Media files
MEDIA_URL=/media/
MEDIA_ROOT=/home/captainhugo/projects/finger-print/API/media

# Timezone
TIME_ZONE=Africa/Dar_es_Salaam

# Optional: Sentry
SENTRY_DSN=https://...@sentry.io/...
```

Generate a secure `DJANGO_SECRET_KEY`:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## First-Time Server Setup

### 1. The repo is already cloned

```bash
# Already done:
# cd ~/projects/finger-print/API
# git clone git@github.com:troubleman96/fingerprint-project-API.git .
```

### 2. Create the virtualenv and install dependencies

```bash
cd ~/projects/finger-print/API
python3 -m venv .venv
.venv/bin/pip install -r requirements/production.txt
```

### 3. Create the `.env` file

```bash
nano ~/projects/finger-print/API/.env
# paste the env block above with real values
```

### 4. Run migrations

```bash
.venv/bin/python manage.py migrate
```

### 5. Collect static files

```bash
.venv/bin/python manage.py collectstatic --noinput
```

### 6. Seed initial data (first deploy only)

```bash
.venv/bin/python manage.py seed
```

To wipe and re-seed:
```bash
.venv/bin/python manage.py seed --flush
```

### 7. Create a superuser (optional — seed already creates admin@email.com)

```bash
.venv/bin/python manage.py createsuperuser
```

---

## Running with Gunicorn (manual test)

```bash
cd ~/projects/finger-print/API
.venv/bin/gunicorn config.wsgi:application \
  --workers 3 \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

Visit `http://vps3376277:8000/api/` to confirm it responds before wiring up Nginx.

**Worker count rule of thumb:** `(2 × CPU cores) + 1`

---

## Systemd Service

Create `/etc/systemd/system/fingerprint-api.service`:

```ini
[Unit]
Description=Fingerprint API (Gunicorn)
After=network.target

[Service]
User=captainhugo
Group=captainhugo
WorkingDirectory=/home/captainhugo/projects/finger-print/API
EnvironmentFile=/home/captainhugo/projects/finger-print/API/.env
ExecStart=/home/captainhugo/projects/finger-print/API/.venv/bin/gunicorn config.wsgi:application \
          --workers 3 \
          --bind unix:/run/fingerprint-api.sock \
          --timeout 120 \
          --access-logfile /home/captainhugo/projects/finger-print/API/logs/access.log \
          --error-logfile /home/captainhugo/projects/finger-print/API/logs/error.log
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Create the logs directory first:
```bash
mkdir -p ~/projects/finger-print/API/logs
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable fingerprint-api
sudo systemctl start fingerprint-api
sudo systemctl status fingerprint-api
```

Check logs:
```bash
sudo journalctl -u fingerprint-api -f
```

---

## Nginx Configuration

Create `/etc/nginx/sites-available/fingerprint-api`:

```nginx
server {
    listen 80;
    server_name api-finger-print.simamia.online;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name api-finger-print.simamia.online;

    ssl_certificate     /etc/letsencrypt/live/api-finger-print.simamia.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api-finger-print.simamia.online/privkey.pem;

    client_max_body_size 20M;

    location / {
        proxy_pass         http://unix:/run/fingerprint-api.sock;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }

    location /media/ {
        alias /home/captainhugo/projects/finger-print/API/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /static/ {
        alias /home/captainhugo/projects/finger-print/API/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/fingerprint-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL Certificate (Certbot)

```bash
sudo certbot --nginx -d api-finger-print.simamia.online
```

---

## Deploying Updates

```bash
cd ~/projects/finger-print/API
git pull origin master
.venv/bin/pip install -r requirements/production.txt
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart fingerprint-api
```

---

## Development Server (local machine only)

```bash
# Local machine — venv python doesn't activate via source on this setup
.venv/bin/python manage.py runserver
```

Uses `config.settings.development` by default. SQLite is used when `DATABASE_URL` is not set.

---

## Credentials (seeded defaults — change in production)

| Email | Password | Role |
|---|---|---|
| admin@email.com | Iyyah@2024 | ADMIN |
| officer@email.com | Iyyah@2024 | OFFICER |
| staff@email.com | Iyyah@2024 | STAFF |
| reviewer@email.com | Iyyah@2024 | OFFICER |
| support@email.com | Iyyah@2024 | STAFF |

Change all passwords immediately after first login on the server.

---

## Key URLs (production)

| URL | Purpose |
|---|---|
| `https://api-finger-print.simamia.online/api/` | API root |
| `https://api-finger-print.simamia.online/api/docs/` | API documentation |
| `https://api-finger-print.simamia.online/api/schema/` | OpenAPI schema |
| `https://api-finger-print.simamia.online/admin/` | Django admin |

---

## Settings Reference

| Setting | File | Notes |
|---|---|---|
| Development | `config/settings/development.py` | `DEBUG=True`, `ALLOWED_HOSTS=*`, SQLite default |
| Production | `config/settings/production.py` | `DEBUG=False`, HTTPS forced, HSTS enabled |
| `DJANGO_SETTINGS_MODULE` | `.env` | Set to `config.settings.production` on server |

`wsgi.py` defaults to `config.settings.production`, so Gunicorn picks up the right settings automatically as long as `.env` is present.
