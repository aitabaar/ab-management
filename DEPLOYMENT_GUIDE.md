# Render Deployment Guide

This app is deployed as a Render Python web service.

## 1. Render Build Settings

Build command:

```text
pip install -r requirements.txt
```

Start command:

```text
uvicorn app:app --host 0.0.0.0 --port $PORT
```

Render automatically provides `PORT`. Do not create a manual `PORT` environment variable.

## 2. Render Environment Variables

Required:

```text
DATABASE_URL
AB_WEB_SECRET
PYTHON_VERSION
```

Recommended values:

```text
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/postgres?sslmode=require
AB_WEB_SECRET=use-a-long-random-secret
PYTHON_VERSION=3.11.9
```

Do not use `SUPABASE_DB_URL`. The app reads `DATABASE_URL`.

## 3. render.yaml

The project includes:

```yaml
services:
  - type: web
    name: ab-management-web
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: AB_WEB_SECRET
        generateValue: true
      - key: PYTHON_VERSION
        value: 3.11.9
```

## 4. Procfile

The project also includes:

```text
web: uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
```

Render can use the explicit Start Command from the dashboard or `render.yaml`. Keep both consistent.

## 5. Deploy From GitHub

1. Push the project to GitHub.
2. Open Render.
3. New > Web Service.
4. Connect repository: `aitabaar/ab-management`.
5. Branch: `main`.
6. Runtime: Python.
7. Build Command: `pip install -r requirements.txt`.
8. Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`.
9. Add environment variables.
10. Deploy.

If the GitHub repository root is this project folder, leave Root Directory blank. If this project is inside a larger repository, set Root Directory to the project folder name.

## 6. Deploy Future Updates

On your laptop:

```powershell
git status
git add .
git commit -m "Describe the update"
git push
```

Render will auto-deploy if auto deploy is enabled. Otherwise:

```text
Render Dashboard > Service > Manual Deploy > Deploy latest commit
```

## 7. Confirm Deployment

After deploy, check:

```text
/
/login
/dashboard
/public-report
/patients
/results
/reports
/billing
```

Render logs should show the service started and no fatal Python traceback.

## 8. Important Render Errors

### Port scan timeout

Cause:

- Wrong start command.
- App crashes before opening port.
- App blocks startup too long.

Correct start command:

```text
uvicorn app:app --host 0.0.0.0 --port $PORT
```

### `DATABASE_URL is required`

Cause:

- Missing environment variable.

Fix:

```text
Render > Service > Environment > Add DATABASE_URL
```

### Supabase connection error

Cause:

- Wrong password.
- Wrong host.
- Missing `?sslmode=require`.
- Direct connection not available from Render.

Fix:

- Use Supabase pooler connection string.
- URL-encode password special characters.

