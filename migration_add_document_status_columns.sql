-- Migration: Add document status columns and enum type
-- This migration adds DocumentStatusEnum and status columns for GCS-backed documents

-- Create the document status enum type
CREATE TYPE document_status_enum AS ENUM ('Pending', 'Verified', 'Invalid');

-- Add document status columns to car_details table
ALTER TABLE car_details 
ADD COLUMN rc_front_status document_status_enum DEFAULT 'Pending',
ADD COLUMN rc_back_status document_status_enum DEFAULT 'Pending',
ADD COLUMN insurance_status document_status_enum DEFAULT 'Pending',
ADD COLUMN fc_status document_status_enum DEFAULT 'Pending',
ADD COLUMN car_img_status document_status_enum DEFAULT 'Pending';

-- Add document status column to car_driver table
ALTER TABLE car_driver 
ADD COLUMN licence_front_status document_status_enum DEFAULT 'Pending';

-- Add document status column to vendor_details table
ALTER TABLE vendor_details 
ADD COLUMN aadhar_status document_status_enum DEFAULT 'Pending';

-- Add document status column to vehicle_owner_details table
ALTER TABLE vehicle_owner_details 
ADD COLUMN aadhar_status document_status_enum DEFAULT 'Pending';

-- Update existing records to have 'Pending' status for documents that have URLs
UPDATE car_details 
SET rc_front_status = 'Pending' 
WHERE rc_front_img_url IS NOT NULL;

UPDATE car_details 
SET rc_back_status = 'Pending' 
WHERE rc_back_img_url IS NOT NULL;

UPDATE car_details 
SET insurance_status = 'Pending' 
WHERE insurance_img_url IS NOT NULL;

UPDATE car_details 
SET fc_status = 'Pending' 
WHERE fc_img_url IS NOT NULL;

UPDATE car_details 
SET car_img_status = 'Pending' 
WHERE car_img_url IS NOT NULL;

UPDATE car_driver 
SET licence_front_status = 'Pending' 
WHERE licence_front_img IS NOT NULL;

UPDATE vendor_details 
SET aadhar_status = 'Pending' 
WHERE aadhar_front_img IS NOT NULL;

UPDATE vehicle_owner_details 
SET aadhar_status = 'Pending' 
WHERE aadhar_front_img IS NOT NULL;
