# Error Fix Guide

## 1. Render: Port Scan Timeout

Error:

```text
Port scan timeout reached, no open ports detected.
```

Fix:

```text
Start Command:
uvicorn app:app --host 0.0.0.0 --port $PORT
```

Also check:

- App did not crash in logs.
- `DATABASE_URL` is set.
- Latest GitHub commit is deployed.

## 2. Render: Exited With Status 1

Meaning:

The Python app crashed.

Fix:

1. Open Render logs.
2. Find the first Python traceback.
3. Fix the file/line shown.
4. Commit and push.
5. Deploy latest commit.

Commands:

```powershell
git status
git add .
git commit -m "Fix Render error"
git push
```

## 3. `DATABASE_URL is required`

Cause:

`DATABASE_URL` environment variable is missing.

Local fix:

```powershell
$env:DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/postgres?sslmode=require"
```

Render fix:

```text
Service > Environment > Add DATABASE_URL
```

## 4. Supabase Host/Connection Error

Common causes:

- Wrong project reference.
- Wrong password.
- Password special character not encoded.
- Missing `?sslmode=require`.
- Direct host has IPv6/network issue.

Fix:

- Use Supabase pooler URI.
- Encode special characters in password.
- Confirm host, port, database, user from Supabase settings.

## 5. `ModuleNotFoundError`

Cause:

Python package missing.

Fix:

```powershell
pip install -r requirements.txt
```

If on Render, confirm:

```text
Build Command:
pip install -r requirements.txt
```

## 6. Login Not Working

Check:

- User exists in `users` table.
- Password matches.
- `AB_WEB_SECRET` is set on Render.
- Browser cookies are enabled.

If sessions act strange, change `AB_WEB_SECRET` and log in again.

## 7. Result Entry Error

Check:

- Patient exists in `patients`.
- Booked tests exist in `patient_tests`.
- Test format exists in `test_parameters`.
- `DATABASE_URL` points to correct Supabase database.

Test page:

```text
/results?lab_no=0001
```

## 8. Report Not Opening

Check:

- Patient exists.
- Results exist if report requires entered values.
- Department filter is not hiding tests.
- Render logs do not show SQL error.

Test:

```text
/report/0001
/public-report/0001
```

## 9. Changes Not Showing on Render

Cause:

Latest code was not pushed or latest commit was not deployed.

Fix:

```powershell
git log -1 --oneline
git status
git push
```

Then Render:

```text
Manual Deploy > Deploy latest commit
```

## 10. `nothing to commit`

Meaning:

Git has no local file changes.

Check:

```powershell
git status
git log -1 --oneline
```

If Render is still old, deploy latest commit manually.

## 11. PowerShell Activation Blocked

Error:

```text
running scripts is disabled on this system
```

Fix:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

## 12. Package Install Fails

Fix:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If Python command is not found, reinstall Python and check "Add Python to PATH".

