# Future Development Guide

This guide explains how to continue development without Codex and how another developer can maintain the project.

## 1. Development Workflow

Before editing:

```powershell
git pull
```

Run locally:

```powershell
$env:DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/postgres?sslmode=require"
$env:AB_WEB_SECRET="local-development-secret"
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

After editing:

```powershell
git status
git add .
git commit -m "Describe the change"
git push
```

## 2. Project Architecture

The app is intentionally simple:

```text
FastAPI routes in app.py
Jinja2 templates in templates/
CSS in static/
PostgreSQL schema in supabase_schema.sql
Render deployment config in render.yaml / Procfile
```

There is no separate frontend build step. HTML is rendered server-side.

## 3. Where to Add Features

| Feature Type | Main Files |
| --- | --- |
| New page/route | `app.py`, new/existing template in `templates/` |
| UI style change | `static/app.css`, `static/style.css`, relevant template |
| Database table/column | `supabase_schema.sql`, `ensure_database_schema()` in `app.py` |
| Report/slip layout | `templates/report.html`, `templates/slip.html`, report helpers in `app.py` |
| Test/report format logic | `test_master`, `test_parameters`, routes in `app.py` |
| Billing/export logic | billing routes in `app.py`, `templates/billing.html` |

## 4. Safe Change Rules

- Make one feature/fix at a time.
- Test locally before pushing.
- Do not hardcode passwords.
- Do not remove existing routes unless sure they are unused.
- Back up Supabase before major database changes.
- Keep `DATABASE_URL` in environment variables only.
- Keep Render start command unchanged unless deployment docs are updated too.

## 5. Adding a New Database Column

1. Add the column to `supabase_schema.sql`.
2. Add `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...` inside `ensure_database_schema()` in `app.py`.
3. Use the column in queries/templates.
4. Test locally.
5. Commit and push.

## 6. Adding a New Page

1. Create a route in `app.py`.
2. Create a template in `templates/`.
3. Add navigation link in `templates/base.html` if needed.
4. Protect staff pages with `require_login(request)`.
5. Protect admin pages with `require_admin(request)`.

Example pattern:

```python
@app.get('/example', response_class=HTMLResponse)
def example_page(request: Request):
    red = require_login(request)
    if red:
        return red
    return templates.TemplateResponse(request, 'example.html', {'user': current_user(request)})
```

## 7. Testing Checklist

After any change, test:

```text
/                      public home
/login                 login
/dashboard             staff dashboard
/patients              patient search
/patients/new          patient registration
/results               result entry
/reports               report list
/report/{lab_no}       report preview
/slip/{lab_no}         slip preview
/tests                 test master
/billing               billing
/users                 admin users
```

Workflow test:

1. Login.
2. Create patient.
3. Add tests.
4. Enter results.
5. Open report.
6. Mark/print report.
7. Check billing.
8. Check report logs.

## 8. GitHub Workflow for Another Developer

First setup:

```powershell
git clone https://github.com/aitabaar/ab-management.git
cd ab-management
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Daily work:

```powershell
git pull
git status
```

After changes:

```powershell
git add .
git commit -m "Clear message"
git push
```

## 9. Deployment Safety

Before pushing to production:

- Confirm app runs locally.
- Confirm no real password was committed.
- Confirm `requirements.txt` includes any new package.
- Confirm Render logs are clean after deployment.

## 10. Suggested Future Improvements

- Store hashed passwords instead of plain text passwords.
- Add automated tests for routes and database queries.
- Add role permission checks per route/action.
- Add better audit logging for patient/result edits.
- Add Supabase backup schedule documentation for the selected plan.
- Add a staging Render service before production changes.

