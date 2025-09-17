# Deployment Checklist - Generic Medical Specialties Update

## 🚀 Pre-Deployment Steps

### 1. Code Changes Summary
- ✅ Updated job reviews to include medical specialty selection (27 specialties)
- ✅ Updated practice profile page to be generic (not radiology-specific)
- ✅ Updated resident profile ("My Profile") to include medical specialty
- ✅ Changed "Teleradiology" to "Telemedicine" across all forms
- ✅ Added specialty bubbles to job reviews display
- ✅ Fixed compensation data specialty display formatting

### 2. Database Changes Required
- ✅ Add `specialty` column to `job_review` table
- ✅ Add `medical_specialty` column to `resident_profile` table  
- ✅ Add `medical_specialty` column to `employer_profile` table
- ✅ Remove `modalities` column from `employer_profile` table
- ✅ Update existing 'Teleradiology' records to 'Telemedicine'

## 📋 Deployment Instructions

### Step 1: Backup Production Database
```bash
# Create a backup of your PostgreSQL database
pg_dump your_database_url > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Step 2: Deploy Code Changes
```bash
# Push to your production branch
git add .
git commit -m "feat: Add generic medical specialties support across platform

- Add medical specialty selection to job reviews (27 specialties)
- Update practice profile to be generic (not radiology-specific)  
- Add medical specialty to resident profiles
- Change Teleradiology to Telemedicine for consistency
- Add specialty display bubbles to job reviews
- Fix compensation data specialty formatting"

git push origin main
```

### Step 3: Run Database Migration
```bash
# On your production server, run the migration script
python production_migration.py
```

### Step 4: Verify Deployment
- ✅ Check job reviews submit page has medical specialty dropdown
- ✅ Check practice profile page has medical specialty (not modalities)
- ✅ Check resident profile ("My Profile") has medical specialty
- ✅ Verify all forms use "Telemedicine" instead of "Teleradiology"
- ✅ Check job reviews display shows specialty bubbles
- ✅ Verify compensation data shows readable specialty names

## 🔧 Environment Compatibility

### PostgreSQL Support
- ✅ All migrations use standard SQL compatible with PostgreSQL
- ✅ VARCHAR lengths are appropriate for PostgreSQL
- ✅ No SQLite-specific syntax used
- ✅ Proper transaction handling for production

### Required Environment Variables
- `DATABASE_URL` - Your PostgreSQL connection string
- All existing environment variables remain the same

## 🚨 Rollback Plan

If issues occur, you can rollback:

1. **Code Rollback**: Revert to previous git commit
2. **Database Rollback**: Restore from backup created in Step 1
3. **Partial Rollback**: The new columns are optional, so the app will work even if migration partially fails

## ✅ Post-Deployment Testing

### Test Cases
1. **Job Review Submission**: Submit a job review with medical specialty
2. **Practice Profile**: Update practice profile with medical specialty  
3. **Resident Profile**: Update resident profile with medical specialty
4. **Specialty Display**: Verify specialty bubbles show readable names
5. **Filtering**: Test specialty filtering in job reviews
6. **Compensation Data**: Check specialty names display properly

### Expected Behavior
- All forms should have 27 medical specialty options
- "Telemedicine" should appear instead of "Teleradiology"
- Specialty displays should show readable names (e.g., "Family Medicine")
- Existing data should remain intact and functional

## 📞 Support

If you encounter any issues during deployment:
1. Check the migration script output for specific error messages
2. Verify your PostgreSQL connection and permissions
3. Ensure all environment variables are properly set
4. Check application logs for any runtime errors

The migration script is designed to be safe and idempotent - you can run it multiple times without issues.
