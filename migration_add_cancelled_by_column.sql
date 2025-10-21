-- Migration script to add cancelled_by column to orders table
-- Run this script to add the cancelled_by column for order cancellation tracking

-- Add the cancelled_by column
ALTER TABLE orders ADD COLUMN cancelled_by VARCHAR(50);

-- Add constraint to ensure only valid values
ALTER TABLE orders ADD CONSTRAINT chk_cancelled_by 
CHECK (cancelled_by IN ('AUTO_CANCELLED', 'CANCELLED_BY_VENDOR'));

-- Update existing cancelled orders to have cancelled_by = 'AUTO_CANCELLED'
-- (assuming they were auto-cancelled if they exist)
UPDATE orders SET cancelled_by = 'AUTO_CANCELLED' 
WHERE trip_status = 'CANCELLED' AND cancelled_by IS NULL;

-- Add index for better query performance
CREATE INDEX idx_orders_cancelled_by ON orders(cancelled_by);

-- Verify the changes
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'orders' AND column_name = 'cancelled_by';
