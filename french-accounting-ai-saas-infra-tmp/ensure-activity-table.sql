-- Create user_management_activities table if missing (for Activity Log tab).
-- Run from project root: docker compose -f infrastructure/docker-compose.yml exec -T postgres psql -U dou_user -d dou_expense_audit -f - < infrastructure/ensure-activity-table.sql

CREATE TABLE IF NOT EXISTS user_management_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    performed_by_id UUID NOT NULL REFERENCES users(id),
    action VARCHAR(80) NOT NULL,
    target_user_id UUID REFERENCES users(id),
    target_role_id UUID REFERENCES roles(id),
    details JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);
