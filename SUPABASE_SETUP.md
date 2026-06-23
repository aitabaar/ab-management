# Supabase Runtime

The database has been migrated to Supabase PostgreSQL. The app now requires `DATABASE_URL` at startup and does not use a local database fallback.

## Connection String

Use the Supabase pooler or direct PostgreSQL URI with SSL:

```text
postgresql://USER:PASSWORD@HOST:5432/postgres?sslmode=require
```

For Render, save that value as the `DATABASE_URL` environment variable.

## Schema

`supabase_schema.sql` is loaded automatically when the FastAPI app starts. Missing tables and indexes are created with `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS`.

## Backups

Backups and restore are handled in the Supabase dashboard. The Render web service is stateless and should not store database backup files locally.
