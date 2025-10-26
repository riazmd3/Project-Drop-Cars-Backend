-- Migration to add admin profit tracking
-- Run this migration to add admin balance and ledger tables

-- ========================================
-- 1. Add balance column to admin table
-- ========================================
ALTER TABLE admin ADD COLUMN IF NOT EXISTS balance INTEGER NOT NULL DEFAULT 0;

-- ========================================
-- 2. Create admin_wallet_ledger table
-- ========================================
CREATE TABLE IF NOT EXISTS admin_wallet_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL REFERENCES admin(id),
    order_id INTEGER REFERENCES orders(id),
    entry_type admin_wallet_entry_type_enum NOT NULL,
    amount INTEGER NOT NULL,
    balance_before INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    notes VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Create index on admin_id for faster queries
CREATE INDEX IF NOT EXISTS idx_admin_wallet_ledger_admin_id ON admin_wallet_ledger(admin_id);

-- Create index on order_id for faster queries
CREATE INDEX IF NOT EXISTS idx_admin_wallet_ledger_order_id ON admin_wallet_ledger(order_id);

-- Create index on created_at for faster queries
CREATE INDEX IF NOT EXISTS idx_admin_wallet_ledger_created_at ON admin_wallet_ledger(created_at);

-- ========================================
-- 3. Create enum type for admin wallet entry type
-- ========================================
DO $$ BEGIN
    CREATE TYPE admin_wallet_entry_type_enum AS ENUM ('CREDIT', 'DEBIT');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

