-- Change pick_near_city to text[] in orders and new_orders
ALTER TABLE orders
ALTER COLUMN pick_near_city TYPE text[] USING (
  CASE 
    WHEN pick_near_city IS NULL THEN NULL
    WHEN pick_near_city = 'ALL' THEN ARRAY['ALL']::text[]
    ELSE ARRAY[pick_near_city]::text[]
  END
);

ALTER TABLE new_orders
ALTER COLUMN pick_near_city TYPE text[] USING (
  CASE 
    WHEN pick_near_city IS NULL THEN NULL
    WHEN pick_near_city = 'ALL' THEN ARRAY['ALL']::text[]
    ELSE ARRAY[pick_near_city]::text[]
  END
);
