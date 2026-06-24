# New Laptop Setup Guide

Use this guide when moving the project to another laptop.

## 1. Required Software

Install these on the new laptop:

1. Python 3.11 or newer.
2. Git.
3. VS Code or another code editor.
4. A browser.
5. Access to the GitHub repository.
6. Access to the Supabase project.
7. Access to the Render dashboard.

Recommended Python version:

```text
Python 3.11.x
```

## 2. Clone the Project

Open PowerShell:

```powershell
cd D:\
mkdir "web broswer and exe file"
cd "D:\web broswer and exe file"
git clone https://github.com/aitabaar/ab-management.git
cd ab-management
```

If you choose another folder, that is fine. Just run all future commands from the cloned project folder.

## 3. Create Virtual Environment

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

## 4. Install Python Packages

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Set Environment Variables Locally

Use the Supabase PostgreSQL connection string from Supabase.

PowerShell example:

```powershell
$env:DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/postgres?sslmode=require"
$env:AB_WEB_SECRET="local-development-secret-change-this"
```

Do not paste the real password into any committed file.

## 6. Run the App Locally

```powershell
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

Open:

```text
http://127.0.0.1:8000
```

Staff login:

```text
http://127.0.0.1:8000/login
```

## 7. Reconnect Supabase on New Laptop

1. Open Supabase dashboard.
2. Open the project.
3. Go to Project Settings > Database.
4. Copy the PostgreSQL connection string.
5. Use the pooler URI if direct connection has network/IPv6 issues.
6. Replace `[YOUR-PASSWORD]` with the real database password.
7. URL-encode special password characters. Example: `@` becomes `%40`.
8. Set it as `DATABASE_URL` in PowerShell before running the app.

## 8. Quick Test After Setup

Open these pages:

```text
/
/login
/dashboard
/patients
/patients/new
/results
/reports
/tests
/billing
/users
```

Test workflow:

1. Login as a staff/admin user from the existing Supabase `users` table.
2. Register a test patient.
3. Add tests.
4. Enter result by lab number.
5. Open report.
6. Print/report preview.
7. Check billing page.
8. Check admin users/test master if logged in as Admin.

## 9. Update From GitHub Later

Before starting work:

```powershell
git pull
```

After editing:

```powershell
git status
git add .
git commit -m "Describe the update"
git push
```

