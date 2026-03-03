# Render Deployment Troubleshooting

## Database Connection Issues

### Issue: "Network is unreachable" or IPv6 Connection Errors

**Symptoms:**
- `connection to server at "db.xxxx.supabase.co" (IPv6 address), port 5432 failed: Network is unreachable`
- `OperationalError` when trying to connect to database

**Root Cause:**
Using direct database connection (port 5432) which attempts IPv6 connections that Render doesn't support well.

**Fix:**
Use Supabase Connection Pooler (port 6543) instead:

1. **Get Pooler Connection String from Supabase:**
   - Go to Supabase Dashboard → Your Project → Settings → Database
   - Find "Connection Pooling" section
   - Copy the connection string that uses port **6543**
   - Format: `postgresql://postgres:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres`

2. **Update Render DATABASE_URL:**
   - Go to Render Dashboard → Your Service → Environment
   - Update DATABASE_URL to the pooler connection string
   - **Important:** Do NOT add `?pgbouncer=true` or other query parameters - Django/psycopg2 doesn't recognize them

3. **Valid Connection String Examples:**
   ```
   ✓ postgresql://postgres:PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ✗ postgresql://postgres:PASSWORD@db.xxxx.supabase.co:5432/postgres (direct - fails on Render)
   ✗ postgresql://...?pgbouncer=true (invalid parameter error)
   ```

4. **Deploy:**
   - After updating DATABASE_URL, trigger "Manual Deploy"
   - Watch build logs for successful migration

---

## Database Migration Issue

If you're seeing `ProgrammingError` about missing tables (like `wallets_wallet`), it means migrations haven't run successfully on Render.

### Root Cause
The `DATABASE_URL` environment variable is not properly configured on Render.

### Fix Steps

1. **Go to Render Dashboard** → Your Service → Environment

2. **Check DATABASE_URL**:
   - Make sure `DATABASE_URL` is set to your Supabase PostgreSQL connection string
   - Format: `postgresql://username:password@host:port/database`
   - Example: `postgresql://postgres.xxxxx:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres`

3. **Trigger Manual Deploy**:
   - After setting DATABASE_URL, go to "Manual Deploy" → "Deploy latest commit"
   - Watch the build logs carefully
   - Look for "Running migrations..." output
   - Should see: "Operations to perform: Apply all migrations: ..."

4. **Verify Build Success**:
   The build.sh script now includes verbose logging:
   ```
   Installing dependencies...
   Collecting static files...
   Checking for pending migrations...
   Running migrations...
   Verifying database setup...
   Build completed successfully!
   ```

5. **Check Deployment Logs**:
   If build succeeds but API still fails, check Runtime Logs for errors

### Quick Test
After deployment, test the wallet endpoint:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://herald-backend-6i3m.onrender.com/api/v1/wallets/me/
```

Should return wallet data, not 500 error.

### Manual Migration (if needed)
If auto-migration fails, you can SSH into Render shell and run manually:
```bash
python manage.py migrate --noinput
```

### Verify Database Tables
After deployment, you can run the verification script:
```bash
python verify_db.py
```

This checks if all required tables exist in the database.
