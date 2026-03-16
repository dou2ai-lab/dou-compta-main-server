-- Migration: Phase 31 & 32 - Monitoring Tables
-- Adds tables for production monitoring, SLOs, and alerts.

-- ============================================================================
-- SERVICE METRICS (Phase 31)
-- ============================================================================

CREATE TABLE service_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    value DECIMAL(15, 4) NOT NULL,
    labels JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_service_metrics_service_name ON service_metrics(service_name);
CREATE INDEX idx_service_metrics_metric_name ON service_metrics(metric_name);
CREATE INDEX idx_service_metrics_timestamp ON service_metrics(timestamp DESC);
CREATE INDEX idx_service_metrics_service_metric_time ON service_metrics(service_name, metric_name, timestamp DESC);

-- ============================================================================
-- SLO METRICS (Phase 31)
-- ============================================================================

CREATE TABLE slo_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    target_value DECIMAL(15, 4) NOT NULL,
    target_type VARCHAR(20) NOT NULL DEFAULT 'minimum', -- 'minimum', 'maximum'
    window_days INTEGER NOT NULL DEFAULT 30,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_slo_metrics_service_name ON slo_metrics(service_name);

-- ============================================================================
-- ALERT RULES (Phase 31)
-- ============================================================================

CREATE TABLE alert_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    service_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    condition VARCHAR(10) NOT NULL, -- '>', '<', '>=', '<=', '=='
    threshold DECIMAL(15, 4) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'warning', -- 'info', 'warning', 'critical'
    description TEXT,
    notification_channels VARCHAR(50)[] DEFAULT ARRAY['email'],
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alert_rules_service_name ON alert_rules(service_name);
CREATE INDEX idx_alert_rules_is_active ON alert_rules(is_active);

-- ============================================================================
-- ALERTS (Phase 31)
-- ============================================================================

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_rule_id UUID NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE,
    service_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15, 4) NOT NULL,
    threshold DECIMAL(15, 4) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- 'active', 'resolved', 'acknowledged'
    triggered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255)
);

CREATE INDEX idx_alerts_alert_rule_id ON alerts(alert_rule_id);
CREATE INDEX idx_alerts_service_name ON alerts(service_name);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_triggered_at ON alerts(triggered_at DESC);




