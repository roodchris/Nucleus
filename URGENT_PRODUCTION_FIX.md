# 🚨 URGENT: Production Database Migration Required

## Issue
The production website is showing 500 errors because the database migration hasn't been run yet. The error shows:

```
sqlalchemy.exc.ProgrammingError: (psycopg.errors.UndefinedColumn) column resident_profile.medical_specialty does not exist
```

## Immediate Fix Required

### Step 1: Access Your Production Server
SSH into your production server or access your deployment platform (Render, Heroku, etc.)

### Step 2: Run the Migration
Execute these commands on your production server:

```bash
# Navigate to your app directory
cd /path/to/your/app

# Make sure you have the latest code
git pull origin main

# Run the production migration
python production_migration.py
```

### Step 3: Restart Your Application
After the migration completes, restart your web application to ensure all changes take effect.

## Expected Migration Output
You should see output like this:

```
🚀 Starting production database migration...
Database URL: postgresql://...
✅ Database connection successful

📋 Migration 1: JobReview table
  Adding specialty column to job_review...
  ✅ Added specialty column to job_review

👤 Migration 2: ResidentProfile table
  Adding medical_specialty column to resident_profile...
  ✅ Added medical_specialty column to resident_profile

🏥 Migration 3: EmployerProfile table
  Adding medical_specialty column to employer_profile...
  ✅ Added medical_specialty column to employer_profile
  Removing modalities column from employer_profile...
  ✅ Removed modalities column from employer_profile

🔄 Migration 4: Update practice type values
  ✅ Updated X JobReview records
  ✅ Updated X EmployerProfile records
  ✅ Updated X CompensationData records

🎉 All migrations completed successfully!
```

## Alternative: Manual SQL Commands

If the Python script doesn't work, you can run these SQL commands directly on your PostgreSQL database:

```sql
-- Add columns
ALTER TABLE job_review ADD COLUMN IF NOT EXISTS specialty VARCHAR(100);
ALTER TABLE resident_profile ADD COLUMN IF NOT EXISTS medical_specialty VARCHAR(100);
ALTER TABLE employer_profile ADD COLUMN IF NOT EXISTS medical_specialty VARCHAR(100);

-- Remove old column (if exists)
ALTER TABLE employer_profile DROP COLUMN IF EXISTS modalities;

-- Update practice type values
UPDATE job_review SET practice_type = 'Telemedicine' WHERE practice_type = 'Teleradiology';
UPDATE employer_profile SET practice_setting = 'Telemedicine' WHERE practice_setting = 'Teleradiology';
UPDATE compensation_data SET practice_type = 'Telemedicine' WHERE practice_type = 'Teleradiology';
```

## Verification
After running the migration, the "Application Decisions" page should work without errors.

## Need Help?
If you're using a platform like Render or Heroku, you might need to:
- Use their CLI tools to run the migration
- Access their web shell/console
- Or run the SQL commands through their database interface

Let me know your deployment platform and I can provide specific instructions!
