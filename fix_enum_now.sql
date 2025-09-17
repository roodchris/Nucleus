-- CRITICAL FIX: Add NEUROLOGICAL_SURGERY to PostgreSQL enum
-- Run this immediately to fix the opportunity creation error

-- First, let's see what enum values currently exist
SELECT 'Current enum values before fix:' as info;
SELECT unnest(enum_range(NULL::opportunitytype))::text as current_values;

-- Add NEUROLOGICAL_SURGERY (the immediate fix needed)
ALTER TYPE opportunitytype ADD VALUE 'NEUROLOGICAL_SURGERY';

-- Add all other missing medical specialties
ALTER TYPE opportunitytype ADD VALUE 'AEROSPACE_MEDICINE';
ALTER TYPE opportunitytype ADD VALUE 'ANESTHESIOLOGY'; 
ALTER TYPE opportunitytype ADD VALUE 'CHILD_NEUROLOGY';
ALTER TYPE opportunitytype ADD VALUE 'DERMATOLOGY';
ALTER TYPE opportunitytype ADD VALUE 'EMERGENCY_MEDICINE';
ALTER TYPE opportunitytype ADD VALUE 'FAMILY_MEDICINE';
ALTER TYPE opportunitytype ADD VALUE 'INTERNAL_MEDICINE';
ALTER TYPE opportunitytype ADD VALUE 'MEDICAL_GENETICS';
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

-- Verify all values were added
SELECT 'Updated enum values after fix:' as info;
SELECT unnest(enum_range(NULL::opportunitytype))::text as updated_values ORDER BY updated_values;
