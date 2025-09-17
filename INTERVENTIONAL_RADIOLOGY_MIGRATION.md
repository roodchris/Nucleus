# Interventional Radiology Job Type Migration Guide

## Overview
This migration adds "Interventional radiology" as a new job type option to the radiology moonlighting job board.

## Changes Made
1. **Models**: Added `INTERVENTIONAL_RADIOLOGY = "interventional_radiology"` to `OpportunityType` enum
2. **Forms**: Added "Interventional radiology" option to `OPP_TYPE_CHOICES`
3. **Database**: Updated PostgreSQL enum type to include the new value

## Migration Steps

### Option 1: Using Migration Script (Recommended)
1. Deploy the updated code to production
2. Go to your Render dashboard
3. Navigate to your web service
4. Click on "Shell" or "Console"
5. Run: `python migrate_interventional_radiology.py`

### Option 2: Direct SQL Command (PostgreSQL)
Connect to your PostgreSQL database and run:
```sql
ALTER TYPE opportunitytype ADD VALUE 'interventional_radiology' BEFORE 'consulting_other';
```

### Option 3: Using psql (if you have direct database access)
```bash
psql -h your-db-host -U your-username -d your-database
```
Then run:
```sql
ALTER TYPE opportunitytype ADD VALUE 'interventional_radiology' BEFORE 'consulting_other';
```

## Verification
After running the migration, verify it worked by:
1. Checking that the website loads without errors
2. Creating a new opportunity and verifying "Interventional radiology" appears in the job type dropdown
3. Filtering opportunities by "Interventional radiology" type
4. Viewing existing opportunities with the new type

## Rollback (if needed)
If you need to rollback, you'll need to:
1. Remove any opportunities that use the interventional_radiology type
2. Remove the enum value (this is complex in PostgreSQL and may require recreating the enum type)

## Testing Checklist
- [ ] New opportunity creation form shows "Interventional radiology" option
- [ ] Opportunity filtering works with "Interventional radiology" type
- [ ] Opportunity listing displays "Interventional radiology" correctly
- [ ] Opportunity detail pages show "Interventional radiology" type
- [ ] Admin dashboard shows opportunities with "Interventional radiology" type
- [ ] Email notifications work for interventional radiology opportunities

## Notes
- The new job type will appear between "Tele diagnostic interpretation" and "Consulting & Other Opportunities" in the dropdown
- All existing functionality will continue to work unchanged
- The migration is safe to run multiple times (idempotent)

