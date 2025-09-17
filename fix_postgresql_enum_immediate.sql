-- IMMEDIATE FIX for PostgreSQL enum issue
-- Run this SQL directly on your production database to fix the NEUROLOGICAL_SURGERY enum error

-- Add all missing specialty values to the opportunitytype enum
-- These commands are safe to run multiple times

-- Add the missing specialty values one by one
DO $$
BEGIN
    -- Add NEUROLOGICAL_SURGERY (the one causing the immediate error)
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'NEUROLOGICAL_SURGERY';
        RAISE NOTICE 'Added NEUROLOGICAL_SURGERY to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'NEUROLOGICAL_SURGERY already exists in enum';
    END;
    
    -- Add all other specialty values
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'AEROSPACE_MEDICINE';
        RAISE NOTICE 'Added AEROSPACE_MEDICINE to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'AEROSPACE_MEDICINE already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'ANESTHESIOLOGY';
        RAISE NOTICE 'Added ANESTHESIOLOGY to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'ANESTHESIOLOGY already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'CHILD_NEUROLOGY';
        RAISE NOTICE 'Added CHILD_NEUROLOGY to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'CHILD_NEUROLOGY already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'DERMATOLOGY';
        RAISE NOTICE 'Added DERMATOLOGY to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'DERMATOLOGY already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'EMERGENCY_MEDICINE';
        RAISE NOTICE 'Added EMERGENCY_MEDICINE to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'EMERGENCY_MEDICINE already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'FAMILY_MEDICINE';
        RAISE NOTICE 'Added FAMILY_MEDICINE to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'FAMILY_MEDICINE already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'INTERNAL_MEDICINE';
        RAISE NOTICE 'Added INTERNAL_MEDICINE to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'INTERNAL_MEDICINE already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'MEDICAL_GENETICS';
        RAISE NOTICE 'Added MEDICAL_GENETICS to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'MEDICAL_GENETICS already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'NEUROLOGY';
        RAISE NOTICE 'Added NEUROLOGY to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'NEUROLOGY already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'NUCLEAR_MEDICINE';
        RAISE NOTICE 'Added NUCLEAR_MEDICINE to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'NUCLEAR_MEDICINE already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'OBSTETRICS_GYNECOLOGY';
        RAISE NOTICE 'Added OBSTETRICS_GYNECOLOGY to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'OBSTETRICS_GYNECOLOGY already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'OCCUPATIONAL_ENVIRONMENTAL_MEDICINE';
        RAISE NOTICE 'Added OCCUPATIONAL_ENVIRONMENTAL_MEDICINE to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'OCCUPATIONAL_ENVIRONMENTAL_MEDICINE already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'ORTHOPAEDIC_SURGERY';
        RAISE NOTICE 'Added ORTHOPAEDIC_SURGERY to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'ORTHOPAEDIC_SURGERY already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'OTOLARYNGOLOGY';
        RAISE NOTICE 'Added OTOLARYNGOLOGY to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'OTOLARYNGOLOGY already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'PATHOLOGY';
        RAISE NOTICE 'Added PATHOLOGY to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'PATHOLOGY already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'PEDIATRICS';
        RAISE NOTICE 'Added PEDIATRICS to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'PEDIATRICS already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'PHYSICAL_MEDICINE_REHABILITATION';
        RAISE NOTICE 'Added PHYSICAL_MEDICINE_REHABILITATION to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'PHYSICAL_MEDICINE_REHABILITATION already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'PLASTIC_SURGERY';
        RAISE NOTICE 'Added PLASTIC_SURGERY to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'PLASTIC_SURGERY already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'PSYCHIATRY';
        RAISE NOTICE 'Added PSYCHIATRY to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'PSYCHIATRY already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'RADIATION_ONCOLOGY';
        RAISE NOTICE 'Added RADIATION_ONCOLOGY to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'RADIATION_ONCOLOGY already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'GENERAL_SURGERY';
        RAISE NOTICE 'Added GENERAL_SURGERY to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'GENERAL_SURGERY already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'THORACIC_SURGERY';
        RAISE NOTICE 'Added THORACIC_SURGERY to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'THORACIC_SURGERY already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'UROLOGY';
        RAISE NOTICE 'Added UROLOGY to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'UROLOGY already exists in enum';
    END;
    
    BEGIN
        ALTER TYPE opportunitytype ADD VALUE 'VASCULAR_SURGERY';
        RAISE NOTICE 'Added VASCULAR_SURGERY to enum';
    EXCEPTION
        WHEN duplicate_object THEN
            RAISE NOTICE 'VASCULAR_SURGERY already exists in enum';
    END;
    
END $$;

-- Verify the enum now contains all values
SELECT 'Current enum values:' as status;
SELECT unnest(enum_range(NULL::opportunitytype))::text as enum_value 
FROM (SELECT 1) t 
ORDER BY enum_value;
