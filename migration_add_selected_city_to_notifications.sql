-- Add selected_city column (text array) to notifications
ALTER TABLE notifications
ADD COLUMN IF NOT EXISTS selected_city text[] DEFAULT ARRAY[]::text[];
