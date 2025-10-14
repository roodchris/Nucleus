-- PostgreSQL migration script to add NON_CLINICAL_OTHER to OpportunityType enum
-- Run this script against your PostgreSQL database to add the new enum value

-- Check if the enum value already exists
DO $$
BEGIN
    -- Check if NON_CLINICAL_OTHER already exists in the opportunitytype enum
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'NON_CLINICAL_OTHER' 
        AND enumtypid = (
            SELECT oid FROM pg_type WHERE typname = 'opportunitytype'
        )
    ) THEN
        -- Add NON_CLINICAL_OTHER at the beginning of the enum (before AEROSPACE_MEDICINE)
        ALTER TYPE opportunitytype ADD VALUE 'NON_CLINICAL_OTHER' BEFORE 'AEROSPACE_MEDICINE';
        RAISE NOTICE 'Successfully added NON_CLINICAL_OTHER to OpportunityType enum';
    ELSE
        RAISE NOTICE 'NON_CLINICAL_OTHER already exists in OpportunityType enum';
    END IF;
END $$;
