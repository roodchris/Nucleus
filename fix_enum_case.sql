-- Fix enum case mismatch by updating database enum to use uppercase values
-- This fixes the 'invalid input value for enum' error

-- Step 1: Create new enum type with uppercase values
CREATE TYPE opportunitytype_new AS ENUM (
    'IN_PERSON_CONTRAST',
    'TELE_CONTRAST', 
    'DIAGNOSTIC_INTERPRETATION',
    'TELE_DIAGNOSTIC_INTERPRETATION',
    'INTERVENTIONAL_RADIOLOGY',
    'CONSULTING_OTHER'
);

-- Step 2: Update opportunity table to use new enum
ALTER TABLE opportunity 
ALTER COLUMN opportunity_type TYPE opportunitytype_new 
USING opportunity_type::text::opportunitytype_new;

-- Step 3: Replace old enum type
DROP TYPE opportunitytype;
ALTER TYPE opportunitytype_new RENAME TO opportunitytype;

-- Step 4: Verify the fix
SELECT unnest(enum_range(NULL::opportunitytype)) as enum_value
ORDER BY enum_value;
