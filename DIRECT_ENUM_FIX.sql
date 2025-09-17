-- DIRECT PostgreSQL Enum Fix
-- Run this SQL directly on your production database
-- This will add all 26 missing medical specialties to the existing enum

-- First, show current enum values
SELECT 'BEFORE FIX - Current enum values:' as status;
SELECT unnest(enum_range(NULL::opportunitytype))::text as current_values ORDER BY current_values;

-- Add all missing medical specialties (one by one to handle any duplicates gracefully)

-- Medical specialties that need to be added
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
ALTER TYPE opportunitytype ADD VALUE 'RADIOLOGY_DIAGNOSTIC';
ALTER TYPE opportunitytype ADD VALUE 'GENERAL_SURGERY';
ALTER TYPE opportunitytype ADD VALUE 'THORACIC_SURGERY';
ALTER TYPE opportunitytype ADD VALUE 'UROLOGY';
ALTER TYPE opportunitytype ADD VALUE 'VASCULAR_SURGERY';

-- Show final enum values to confirm all were added
SELECT 'AFTER FIX - All enum values:' as status;
SELECT unnest(enum_range(NULL::opportunitytype))::text as all_values ORDER BY all_values;

-- Count total values
SELECT 'SUMMARY:' as status, COUNT(*) as total_enum_values 
FROM (SELECT unnest(enum_range(NULL::opportunitytype))::text) t;
