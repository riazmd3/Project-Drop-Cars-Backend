-- Migration: Add permit image URL and status to car_details
-- Run order: after existing document status migrations

ALTER TABLE car_details
ADD COLUMN IF NOT EXISTS permit_img_url VARCHAR UNIQUE,
ADD COLUMN IF NOT EXISTS permit_status document_status_enum;

-- Default existing rows to NULLs; app logic treats NULL as Pending until set


