# Database Setup Guide for AB Management

## Problem
The error `relation "hospitals" does not exist` occurs because the database schema hasn't been properly initialized in Supabase.

## Solution

### Step 1: Run the Main Schema Migration in Supabase

1. **Open Supabase SQL Editor:**
   - Go to https://app.supabase.com
   - Select your project
   - Click **SQL Editor** in the left sidebar
   - Click **New Query**

2. **Copy the content of this file:**
   - `migrations/000_init_main_schema.sql`

3. **Paste it into the SQL Editor**

4. **Click RUN** (or Cmd+Enter / Ctrl+Enter)

5. **Wait for completion** - You should see "Query successful" at the bottom

### Step 2: Run the Role-Based Permissions Migration

1. **Create a new query** in the SQL Editor

2. **Copy the content of this file:**
   - `migrations/001_multi_hospital_permissions.sql`

3. **Paste it into the SQL Editor**

4. **Click RUN**

5. **Wait for completion**

### Step 3: Deploy the Latest App Code

1. **Push the code to GitHub:**
   ```
   git add .
   git commit -m "Deploy with corrected database schema"
   git push
   ```

2. **Wait 2-3 minutes for Render to rebuild and deploy**

3. **Test the login at:** https://ab-management.onrender.com/login

## What These Migrations Do

### `000_init_main_schema.sql` (Main Schema - Run First)
- Creates all core tables: `users`, `hospitals`, `roles`, `permissions`, `patients`, `test_results`, etc.
- Adds `hospital_id` columns to all relevant tables (idempotent - safe to run multiple times)
- Creates indexes for performance
- Uses `CREATE TABLE IF NOT EXISTS` - won't fail if tables already exist

### `001_multi_hospital_permissions.sql` (Permissions - Run Second)
- Creates role-based permission system
- Creates `role_permissions`, `user_permissions`, `user_hospitals` tables
- Safe to run multiple times

## Important Notes

✅ **Both migrations are idempotent** - Safe to run multiple times  
✅ **No data will be dropped** - Only creates tables and columns  
✅ **Preserves existing data** - Uses `CREATE TABLE IF NOT EXISTS` and `ADD COLUMN IF NOT EXISTS`  
✅ **Order matters** - Run `000_init_main_schema.sql` FIRST, then `001_multi_hospital_permissions.sql`

## Troubleshooting

If you get an error:

1. **"Column already exists"** - This is normal, the migration skips it
2. **"Foreign key constraint"** - Ensure you run migrations in order
3. **"Permission denied"** - Make sure you're using the Supabase admin connection

## Verification

After running both migrations, check that tables were created:

```sql
-- List all tables
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;

-- You should see tables like: users, hospitals, patients, roles, permissions, etc.
```

## Next: App Deployment

The app will auto-initialize any remaining schema on startup. The fixes applied ensure:
- Graceful error handling if tables don't exist yet
- Login won't crash even if `login_logs` table is missing
- `is_active` column defaults to `true` if missing

After the schema is in place, the app should work perfectly!
