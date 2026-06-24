# AB Management Lab Web App - Project Documentation

## 1. Project Overview

This is a FastAPI web application for laboratory management. It supports public report lookup and staff/admin workflows for patient booking, result entry, report printing, billing, tests, departments, panels, doctors, expenses, and audit/report logs.

The app is designed to run:

- Locally on a laptop for development.
- Online on Render as a Python web service.
- With Supabase PostgreSQL as the shared production database.

The app does not require a local database file for production. Runtime database access uses the `DATABASE_URL` environment variable.

## 2. Main Features

- Public report search by lab number.
- Staff login and logout.
- Dashboard with patient/revenue/report summary.
- Patient registration and patient detail editing.
- Add/remove patient tests.
- Result entry by lab number.
- Department-wise pending/ready workflow.
- Report preview and print status logging.
- Patient collection slip preview.
- Test master and test format management.
- Department add/rename.
- Panel price management.
- Billing, CSV export, and Excel-style export.
- Users/admin management.
- Expenses, doctors, daily patients, cash report.
- Supabase-backed schema auto-check at startup.

## 3. Folder Structure

```text
lab_web_app/
  .gitignore
  Procfile
  README.md
  SUPABASE_SETUP.md
  app.py
  render.yaml
  requirements.txt
  supabase_schema.sql
  PROJECT_DOCUMENTATION.md
  NEW_LAPTOP_SETUP.md
  DEPLOYMENT_GUIDE.md
  DATABASE_GUIDE.md
  ERROR_FIX_GUIDE.md
  FUTURE_DEVELOPMENT_GUIDE.md
  static/
    app.css
    style.css
  templates/
    audit.html
    backup.html
    base.html
    billing.html
    cash_report.html
    daily_patients.html
    dashboard.html
    departments.html
    doctors.html
    expenses.html
    home.html
    login.html
    new_patient.html
    panels.html
    patient_detail.html
    patient_form.html
    patients.html
    pending_ready.html
    public_report.html
    report.html
    report_logs.html
    reports.html
    reports_index.html
    result_templates.html
    results.html
    results_index.html
    settings.html
    slip.html
    slips.html
    test_format.html
    test_master.html
    tests.html
    users.html
```

Ignored local/runtime files:

```text
__pycache__/
.env
.venv/
venv/
backups/
*.db
*.sqlite
*.sqlite3
```

## 4. Important Files

| File | Purpose |
| --- | --- |
| `app.py` | Main FastAPI application, routes, database wrapper, report/slip logic, billing/admin workflows. |
| `supabase_schema.sql` | PostgreSQL schema used for Supabase tables and indexes. |
| `requirements.txt` | Python packages needed to run the app. |
| `render.yaml` | Render Blueprint/service config. |
| `Procfile` | Alternative Render/start command definition. |
| `.gitignore` | Prevents local secrets, virtualenv, cache, and local DB backups from being committed. |
| `templates/` | Jinja2 HTML pages for all screens and printable reports/slips. |
| `static/` | CSS and static web assets. |
| `README.md` | Short quick-start overview. |
| `SUPABASE_SETUP.md` | Supabase runtime notes. |

## 5. Database Details

Database engine:

```text
Supabase PostgreSQL
```

Runtime connection variable:

```text
DATABASE_URL
```

Main tables:

| Table | Purpose |
| --- | --- |
| `users` | Staff/admin login users and roles. |
| `patients` | Patient booking, billing, report/payment status. |
| `patient_tests` | Tests booked for each lab number. |
| `test_results` | Parameter-wise entered results. |
| `test_master` | Test list, price, department, status, report grouping. |
| `test_parameters` | Format/parameters for each test. |
| `panel_names` | Panels/hospitals/clinics. |
| `panel_test_rates` | Panel-wise test rates. |
| `result_templates` | Saved morphology/remarks shortcuts. |
| `app_settings` | Lab name, report spacing/header/footer settings. |
| `expenses` | Expense records. |
| `doctors` | Referring doctors. |
| `daily_patients` | Daily patient summary table. |
| `report_logs` | Report view/print audit log. |

## 6. Important Routes

Public:

```text
/                         public home/report lookup
/public-report            public report search
/public-report/{lab_no}   public report by lab number
```

Staff:

```text
/login
/logout
/dashboard
/patients
/patients/new
/patients/{lab_no}
/results
/pending-ready
/slip/{lab_no}
/report/{lab_no}
/reports
/report-logs
/billing
/billing/export.csv
/billing/export.xls
/tests
/tests/{test_name}/format
/departments
/panels
/settings
/users
/expenses
/doctors
/daily-patients
/cash-report
/result-templates
/backup
```

## 7. Runtime Design

`app.py` reads:

```python
DATABASE_URL = os.environ.get("DATABASE_URL")
PORT = os.environ.get("PORT", "8000")
```

Render provides `PORT` automatically. You must provide `DATABASE_URL`.

The schema check runs in a background startup thread. This avoids Render port timeout while still allowing missing tables to be created automatically.

## 8. Security Notes

- Do not commit database passwords.
- Do not hardcode Supabase password in `app.py`.
- Store secrets only in environment variables.
- Keep `.env` ignored.
- Change default/demo staff passwords before production use.
- Use HTTPS URL from Render for hospitals/patients.

