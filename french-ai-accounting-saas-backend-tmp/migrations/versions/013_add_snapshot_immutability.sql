-- Migration: Add Audit Snapshot Immutability Protection
-- Dou Expense & Audit AI – France Edition
-- Prevents UPDATE/DELETE on audit_snapshots table at database level

-- ============================================================================
-- IMMUTABILITY FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION prevent_snapshot_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'audit_snapshots table is immutable - updates and deletes are not allowed. Snapshot ID: %', COALESCE(OLD.id::text, NEW.id::text);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Prevent UPDATE on audit_snapshots
DROP TRIGGER IF EXISTS prevent_snapshot_update ON audit_snapshots;
CREATE TRIGGER prevent_snapshot_update
    BEFORE UPDATE ON audit_snapshots
    FOR EACH ROW
    EXECUTE FUNCTION prevent_snapshot_modification();

-- Prevent DELETE on audit_snapshots
DROP TRIGGER IF EXISTS prevent_snapshot_delete ON audit_snapshots;
CREATE TRIGGER prevent_snapshot_delete
    BEFORE DELETE ON audit_snapshots
    FOR EACH ROW
    EXECUTE FUNCTION prevent_snapshot_modification();

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify triggers are created
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'prevent_snapshot_update' 
        AND tgrelid = 'audit_snapshots'::regclass
    ) THEN
        RAISE EXCEPTION 'Trigger prevent_snapshot_update was not created';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'prevent_snapshot_delete' 
        AND tgrelid = 'audit_snapshots'::regclass
    ) THEN
        RAISE EXCEPTION 'Trigger prevent_snapshot_delete was not created';
    END IF;
    
    RAISE NOTICE 'Audit snapshot immutability protection successfully enabled';
END $$;

