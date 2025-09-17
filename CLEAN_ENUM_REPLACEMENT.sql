-- CLEAN ENUM REPLACEMENT - Remove Legacy Values and Add Medical Specialties
-- This approach migrates existing data and creates a clean enum

-- Step 1: Show current state
SELECT 'CURRENT ENUM VALUES:' as info;
SELECT unnest(enum_range(NULL::opportunitytype))::text as current_values ORDER BY current_values;

-- Step 2: Show current opportunities and their types
SELECT 'CURRENT OPPORTUNITIES BY TYPE:' as info;
SELECT opportunity_type, COUNT(*) as count 
FROM opportunity 
GROUP BY opportunity_type 
ORDER BY opportunity_type;

-- Step 3: Add RADIOLOGY_DIAGNOSTIC first (we'll map legacy values to this)
ALTER TYPE opportunitytype ADD VALUE 'RADIOLOGY_DIAGNOSTIC';

-- Step 4: Update existing opportunities to use new enum values
-- Map legacy radiology values to RADIOLOGY_DIAGNOSTIC
UPDATE opportunity SET opportunity_type = 'RADIOLOGY_DIAGNOSTIC' WHERE opportunity_type = 'IN_PERSON_CONTRAST';
UPDATE opportunity SET opportunity_type = 'RADIOLOGY_DIAGNOSTIC' WHERE opportunity_type = 'TELE_CONTRAST';
UPDATE opportunity SET opportunity_type = 'RADIOLOGY_DIAGNOSTIC' WHERE opportunity_type = 'DIAGNOSTIC_INTERPRETATION';
UPDATE opportunity SET opportunity_type = 'RADIOLOGY_DIAGNOSTIC' WHERE opportunity_type = 'TELE_DIAGNOSTIC_INTERPRETATION';
UPDATE opportunity SET opportunity_type = 'RADIOLOGY_DIAGNOSTIC' WHERE opportunity_type = 'CONSULTING_OTHER';
-- INTERVENTIONAL_RADIOLOGY can stay as-is since it's already a valid medical specialty

-- Step 5: Add all medical specialties
ALTER TYPE opportunitytype ADD VALUE 'AEROSPACE_MEDICINE';
ALTER TYPE opportunitytype ADD VALUE 'ANESTHESIOLOGY';
ALTER TYPE opportunitytype ADD VALUE 'CHILD_NEUROLOGY';
ALTER TYPE opportunitytype ADD VALUE 'DERMATOLOGY';
ALTER TYPE opportunitytype ADD VALUE 'EMERGENCY_MEDICINE';
ALTER TYPE opportunitytype ADD VALUE 'FAMILY_MEDICINE';
ALTER TYPE opportunitytype ADD VALUE 'INTERNAL_MEDICINE';
ALTER TYPE opportunitytype ADD VALUE 'MEDICAL_GENETICS';
ALTER TYPE opportunitytype ADD VALUE 'NEUROLOGICAL_SURGERY';
ALTER TYPE opportunitytype ADD VALUE 'NEUROLOGY';
ALTER TYPE opportunitytype ADD VALUE 'NUCLEAR_MEDICINE';
ALTER TYPE opportunitytype ADD VALUE 'OBSTETRICS_GYNECOLOGY';
ALTER TYPE opportunitytype ADD VALUE 'OCCUPATIONAL_ENVIRONMENTAL_MEDICINE';
ALTER TYPE opportunitytype ADD VALUE 'ORTHOPAEDIC_SURGERY';
ALTER TYPE opportunitytype ADD VALUE 'OTOLARYNGOLOGY';
ALTER TYPE opportunitytype ADD VALUE 'PATHOLOGY';
ALTER TYPE opportunitytype ADD VALUE 'PEDIATRICS';
ALTER TYPE opportunitytype ADD VALUE 'PHYSICAL_MEDICINE_REHABILITATION';
ALTER TYPE opportunitytype ADD VALUE 'PLASTIC_SURGERY';
ALTER TYPE opportunitytype ADD VALUE 'PSYCHIATRY';
ALTER TYPE opportunitytype ADD VALUE 'RADIATION_ONCOLOGY';
ALTER TYPE opportunitytype ADD VALUE 'GENERAL_SURGERY';
ALTER TYPE opportunitytype ADD VALUE 'THORACIC_SURGERY';
ALTER TYPE opportunitytype ADD VALUE 'UROLOGY';
ALTER TYPE opportunitytype ADD VALUE 'VASCULAR_SURGERY';

-- Step 6: Verify the final result
SELECT 'FINAL ENUM VALUES:' as info;
SELECT unnest(enum_range(NULL::opportunitytype))::text as final_values ORDER BY final_values;

SELECT 'FINAL OPPORTUNITIES BY TYPE:' as info;
SELECT opportunity_type, COUNT(*) as count 
FROM opportunity 
GROUP BY opportunity_type 
ORDER BY opportunity_type;

-- Step 7: Summary
SELECT 'SUMMARY:' as info, COUNT(*) as total_enum_values 
FROM (SELECT unnest(enum_range(NULL::opportunitytype))::text) t;

-- NOTE: The legacy enum values will still exist in the enum but won't be used
-- PostgreSQL doesn't allow removing enum values, but this is fine - they're just unused
-- All existing opportunities are now mapped to valid medical specialties
