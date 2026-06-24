# Database Guide

## 1. Database Type

The production database is Supabase PostgreSQL.

The app connects through:

```text
DATABASE_URL
```

No production database password should be stored in code.

## 2. DATABASE_URL Format

General format:

```text
postgresql://USER:PASSWORD@HOST:5432/postgres?sslmode=require
```

Supabase pooler format usually looks like:

```text
postgresql://postgres.PROJECT_REF:PASSWORD@POOLER_HOST:5432/postgres?sslmode=require
```

If the password has special characters, URL-encode them.

Common examples:

```text
@ becomes %40
# becomes %23
% becomes %25
space becomes %20
```

## 3. Where to Put DATABASE_URL

Local PowerShell:

```powershell
$env:DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/postgres?sslmode=require"
```

Render:

```text
Environment > DATABASE_URL > value
```

Do not commit `.env` or any file containing the real password.

## 4. Schema File

Schema file:

```text
supabase_schema.sql
```

It creates these tables:

```text
users
patients
patient_tests
test_results
test_master
test_parameters
panel_names
panel_test_rates
result_templates
app_settings
expenses
doctors
daily_patients
report_logs
```

It also creates indexes for lab-number lookups.

## 5. Automatic Schema Check

At FastAPI startup, the app starts a background schema check:

```text
ensure_database_schema()
```

It creates missing tables/indexes and adds important missing columns. This avoids Render port timeout because the check runs in a background thread.

## 6. Main Table Meanings

| Table | Meaning |
| --- | --- |
| `users` | Staff/admin login accounts. |
| `patients` | Main patient booking and billing record. |
| `patient_tests` | Tests booked for each patient/lab number. |
| `test_results` | Result values, morphology, remarks. |
| `test_master` | Master test list, departments, prices, report grouping. |
| `test_parameters` | Parameters/units/reference ranges for each test. |
| `panel_names` | Panels/hospitals/clinics. |
| `panel_test_rates` | Panel-specific rates. |
| `result_templates` | Reusable result remarks/morphology text. |
| `app_settings` | Lab/report settings. |
| `expenses` | Expense entries. |
| `doctors` | Doctor/referrer records. |
| `daily_patients` | Daily patient summary records. |
| `report_logs` | Report view/print logs. |

## 7. Backup Instructions

Use Supabase backups, not local files.

Recommended:

1. Open Supabase dashboard.
2. Open your project.
3. Use Database backup/export tools available in your Supabase plan.
4. Before major changes, export important tables or take a Supabase backup.

For manual export:

1. Supabase dashboard > Table Editor.
2. Open important table.
3. Export CSV if available.

Important tables to back up:

```text
patients
patient_tests
test_results
test_master
test_parameters
panel_names
panel_test_rates
users
app_settings
report_logs
```

## 8. Restore Instructions

Best restore path:

1. Use Supabase dashboard backup restore if your plan supports it.
2. Or import exported CSV data back into matching tables.
3. After restore, run the app once so schema check can add any missing columns/indexes.

Do not restore by uploading a local SQLite file. The app is PostgreSQL-based now.

## 9. Database Safety Rules

- Do not edit production tables without backup.
- Do not delete patient/test/result rows unless you are sure.
- Do not share `DATABASE_URL` publicly.
- Reset database password if it is exposed.
- Keep Render and local laptop using the same `DATABASE_URL` if they should share the same live data.

