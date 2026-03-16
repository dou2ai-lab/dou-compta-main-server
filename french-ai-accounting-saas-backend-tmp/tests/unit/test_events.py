# -----------------------------------------------------------------------------
# File: test_events.py
# Description: Unit tests for domain events
# -----------------------------------------------------------------------------

"""Unit tests for domain events."""
import pytest
import json
from common.events import DomainEvent


class TestDomainEvent:
    def test_create_event(self):
        event = DomainEvent(
            event_type="expense.approved",
            aggregate_type="expense",
            aggregate_id="123",
            tenant_id="tenant-1",
            payload={"amount": "100"},
        )
        assert event.event_type == "expense.approved"
        assert event.event_id  # auto-generated

    def test_to_json(self):
        event = DomainEvent(
            event_type="test", aggregate_type="test",
            aggregate_id="1", tenant_id="t1",
        )
        json_str = event.to_json()
        parsed = json.loads(json_str)
        assert parsed["event_type"] == "test"

    def test_from_json(self):
        event = DomainEvent(
            event_type="test", aggregate_type="test",
            aggregate_id="1", tenant_id="t1",
        )
        json_str = event.to_json()
        restored = DomainEvent.from_json(json_str)
        assert restored.event_type == event.event_type
        assert restored.event_id == event.event_id

    def test_to_dict(self):
        event = DomainEvent(
            event_type="test", aggregate_type="test",
            aggregate_id="1", tenant_id="t1",
            payload={"key": "value"},
        )
        d = event.to_dict()
        assert d["payload"]["key"] == "value"
