-- Migration to update address fields and remove organization_id
-- Run this migration to update the database schema

-- ========================================
-- 1. Remove organization_id from vehicle_owner table
-- ========================================
ALTER TABLE vehicle_owner DROP COLUMN IF EXISTS organization_id;

-- ========================================
-- 2. Add city and pincode to vehicle_owner_details table
-- ========================================
ALTER TABLE vehicle_owner_details DROP COLUMN IF EXISTS organization_id;
ALTER TABLE vehicle_owner_details ADD COLUMN IF NOT EXISTS city VARCHAR NOT NULL DEFAULT '';
ALTER TABLE vehicle_owner_details ADD COLUMN IF NOT EXISTS pincode VARCHAR NOT NULL DEFAULT '';

-- Update existing records (optional - you may want to populate with actual values)
-- UPDATE vehicle_owner_details SET city = 'Unknown', pincode = '000000' WHERE city = '' OR city IS NULL;

-- ========================================
-- 3. Update vendor_details table: Rename adress to address and add city, pincode
-- ========================================
ALTER TABLE vendor_details DROP COLUMN IF EXISTS organization_id;

-- Rename adress to address
ALTER TABLE vendor_details RENAME COLUMN adress TO address;

-- Add city and pincode columns
ALTER TABLE vendor_details ADD COLUMN IF NOT EXISTS city VARCHAR NOT NULL DEFAULT '';
ALTER TABLE vendor_details ADD COLUMN IF NOT EXISTS pincode VARCHAR NOT NULL DEFAULT '';

-- Update existing records (optional - you may want to populate with actual values)
-- UPDATE vendor_details SET city = 'Unknown', pincode = '000000' WHERE city = '' OR city IS NULL;

-- ========================================
-- 4. Update car_driver table: Rename adress to address, add city and pincode, remove organization_id
-- ========================================
ALTER TABLE car_driver DROP COLUMN IF EXISTS organization_id;

-- Rename adress to address
ALTER TABLE car_driver RENAME COLUMN adress TO address;

-- Add city and pincode columns
ALTER TABLE car_driver ADD COLUMN IF NOT EXISTS city VARCHAR NOT NULL DEFAULT '';
ALTER TABLE car_driver ADD COLUMN IF NOT EXISTS pincode VARCHAR NOT NULL DEFAULT '';

-- Update existing records (optional - you may want to populate with actual values)
-- UPDATE car_driver SET city = 'Unknown', pincode = '000000' WHERE city = '' OR city IS NULL;

-- ========================================
-- 5. Add year_of_the_car to car_details table and remove organization_id
-- ========================================
ALTER TABLE car_details DROP COLUMN IF EXISTS organization_id;
ALTER TABLE car_details ADD COLUMN IF NOT EXISTS year_of_the_car VARCHAR;

-- ========================================
-- 6. Make city and pincode NOT NULL (after populating with defaults)
-- ========================================
-- Uncomment these lines after you've updated the existing records with real values

-- ALTER TABLE vehicle_owner_details ALTER COLUMN city SET NOT NULL;
-- ALTER TABLE vehicle_owner_details ALTER COLUMN pincode SET NOT NULL;

-- ALTER TABLE vendor_details ALTER COLUMN city SET NOT NULL;
-- ALTER TABLE vendor_details ALTER COLUMN pincode SET NOT NULL;

-- ALTER TABLE car_driver ALTER COLUMN city SET NOT NULL;
-- ALTER TABLE car_driver ALTER COLUMN pincode SET NOT NULL;

