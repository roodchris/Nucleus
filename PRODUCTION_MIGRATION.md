# Production Database Migration Guide

## Issue
The production database is missing the `timezone` column in the `user` table, causing internal server errors.

## Solution
Run the following SQL command on your production PostgreSQL database to add the missing column:

### Option 1: Using Render Console
1. Go to your Render dashboard
2. Navigate to your web service
3. Click on "Shell" or "Console"
4. Run: `python migrate_database.py`

### Option 2: Direct SQL Command
Connect to your PostgreSQL database and run:
```sql
ALTER TABLE "user" ADD COLUMN timezone VARCHAR(50);
```

### Option 3: Using psql (if you have direct database access)
```bash
psql -h your-db-host -U your-username -d your-database
```
Then run:
```sql
ALTER TABLE "user" ADD COLUMN timezone VARCHAR(50);
```

## After Migration
Once the migration is complete, the timezone functionality will be automatically enabled in the next deployment.

## Verification
After running the migration, you can verify it worked by:
1. Checking that the website loads without errors
2. The timezone functionality in the WRVU calculator should work
3. Users should be able to set their timezone preferences

## Rollback (if needed)
If you need to rollback, run:
```sql
ALTER TABLE "user" DROP COLUMN timezone;
```
