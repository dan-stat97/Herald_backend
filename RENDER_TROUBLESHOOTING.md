# Render Deployment Troubleshooting

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
