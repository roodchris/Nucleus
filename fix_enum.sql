-- Fix PostgreSQL enum to add interventional_radiology value
-- Run this script on your production PostgreSQL database

-- First, check current enum values
SELECT unnest(enum_range(NULL::opportunitytype)) as enum_value
ORDER BY enum_value;

-- Add the new enum value (this will fail if it already exists, which is fine)
ALTER TYPE opportunitytype 
ADD VALUE 'interventional_radiology' BEFORE 'consulting_other';

-- Verify the addition
SELECT unnest(enum_range(NULL::opportunitytype)) as enum_value
ORDER BY enum_value;

-- If you need to check if the value exists first, you can use:
-- SELECT 1 FROM pg_enum 
-- WHERE enumlabel = 'interventional_radiology' 
-- AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'opportunitytype');





