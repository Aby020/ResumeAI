# Deployment Readiness Inspection: ResumeAI

## Status
- **Deployment Status:** Not yet ready for production deployment on Render.
- **Goal:** Prepare for deployment to Render using a Neon PostgreSQL database.

## Inspection Results
1.  **Django Version:** 5.2.16 (defined in `requirements.txt`).
2.  **Python Requirements:** `requirements.txt` is present and includes necessary production dependencies (`gunicorn`, `whitenoise`, `psycopg2-binary`, `dj-database-url`).
3.  **Database Configuration:** Uses `dj-database-url` to parse `DATABASE_URL` from the environment, falling back to a local SQLite file. This is Render-compatible (Neon PostgreSQL can be provided via `DATABASE_URL`).
4.  **Security:** Uses `python-decouple` to manage sensitive settings (`SECRET_KEY`, `EMAIL_HOST_PASSWORD`, `OPENAI_API_KEY`, etc.).
5.  **Static Files:** `whitenoise` is configured for production static file serving.
6.  **Media/Uploads:** `django-cloudinary-storage` is used for media storage, which is suitable for Render's ephemeral filesystem.
7.  **Deployment Blockers:**
    *   No `render.yaml` blueprint configuration.
    *   Need to ensure PostgreSQL migrations are applied during build.
    *   Need to ensure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` are correctly configured in Render's environment variables.
    *   Need to ensure `DEBUG=False` in production environment.

## Changes Required (Action Plan)
1.  **Render Configuration:** Create a `render.yaml` file to define the service, build command, and start command.
2.  **Environment Variables:** Define the required environment variables in the Render dashboard.
3.  **PostgreSQL Migration:** Ensure migrations run automatically on deployment.

## Required Environment Variables (Render)
- `SECRET_KEY`: (Generate a strong, random key)
- `DEBUG`: `False`
- `ALLOWED_HOSTS`: `<your-app-name>.onrender.com`
- `CSRF_TRUSTED_ORIGINS`: `https://<your-app-name>.onrender.com`
- `DATABASE_URL`: (Neon PostgreSQL connection string)
- `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`: (From Cloudinary)
- `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`: (For outbound email)
- `OPENAI_API_KEY`: (For AI features)

## Recommended Render Commands
- **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput`
- **Start Command:** `gunicorn ResumeAI.wsgi:application --bind 0.0.0.0:$PORT`
  - **IMPORTANT:** Must bind to `0.0.0.0:$PORT` (Render injects the `$PORT` env var). The default `gunicorn` bind (`127.0.0.1:8000`) will cause a health-check failure on Render.
- **Root Directory:** `./`

## Potential Deployment Issues
1.  **Cloudinary startup crash risk:** `settings.py` gates Cloudinary config on the `RENDER` env var (which Render auto-sets to `true`). Because the Cloudinary credentials are read with `config(...)` and have **no default**, if `CLOUDINARY_CLOUD_NAME` / `CLOUDINARY_API_KEY` / `CLOUDINARY_API_SECRET` are missing, the app will raise `UndefinedValueError` at startup and fail to boot. **All three Cloudinary vars must be set**, or the Cloudinary block needs a graceful fallback (code change — out of scope for this inspection).
2.  **`DEBUG` defaults to `True`:** `settings.py` sets `DEBUG = config("DEBUG", default=True, cast=bool)`. If `DEBUG` is not explicitly set to `False` in the Render env, the app will run in debug mode in production. Must set `DEBUG=False`.
3.  **`ALLOWED_HOSTS` defaults to localhost:** Must set `ALLOWED_HOSTS` to your Render subdomain, otherwise all requests get `DisallowedHost` errors.
4.  **`CSRF_TRUSTED_ORIGINS` must be set:** Required for login/POST forms to work over HTTPS on the Render domain.
5.  **`SECRET_KEY` has no default:** Must be set in the Render env with a strong, unique value.
6.  **Local `db.sqlite3` in repo root:** Gitignored (`*.sqlite3`), so it will not be deployed. Neon will be used via `DATABASE_URL`. No conflict, but do not rely on any local SQLite data in production.
7.  **spaCy model:** `en_core_web_sm` is not pip-installable and is downloaded via `python -m spacy download`. It is not in `requirements.txt`, so the build command above does not install it. The analyzer degrades gracefully (plain-token fallback) if absent, so it is non-blocking — but AI/NLP features will be weaker until installed (could be added to build command later).

## What We Should Do Next
1.  Create `render.yaml` blueprint.
2.  (User Action) Create Neon PostgreSQL database.
3.  (User Action) Create Cloudinary account (if not existing).
4.  (User Action) Create Render Web Service and link the repository.
5.  Configure environment variables in the Render dashboard.
6.  Trigger first deployment.
