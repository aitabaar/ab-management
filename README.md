# AB Management Web App

FastAPI laboratory management portal for AB Lab / AB Management.

The app is production-ready for Render and uses Supabase PostgreSQL through `DATABASE_URL`.

## Local Run

```powershell
$env:DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/postgres?sslmode=require"
$env:AB_WEB_SECRET="change-this-local-secret"
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

## Render

Build command:

```text
pip install -r requirements.txt
```

Start command:

```text
uvicorn app:app --host 0.0.0.0 --port $PORT
```

Required environment variables:

- `DATABASE_URL`
- `AB_WEB_SECRET`

## Main Pages

- `/` public report lookup
- `/login` staff login
- `/dashboard` staff dashboard
- `/patients/new` patient registration
- `/results` result entry
- `/reports` report list and print/export
- `/billing` billing and exports
- `/users` admin user management

## Full Documentation

- `PROJECT_DOCUMENTATION.md` - complete app overview and file guide
- `NEW_LAPTOP_SETUP.md` - clone/run setup for another laptop
- `DEPLOYMENT_GUIDE.md` - Render deployment settings and workflow
- `DATABASE_GUIDE.md` - Supabase PostgreSQL and backup/restore notes
- `ERROR_FIX_GUIDE.md` - common errors and fixes
- `FUTURE_DEVELOPMENT_GUIDE.md` - how to continue development safely
