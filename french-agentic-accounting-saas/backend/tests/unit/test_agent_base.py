# -----------------------------------------------------------------------------
# File: test_agent_base.py
# Description: Unit tests for agent base framework
# -----------------------------------------------------------------------------

"""Unit tests for agent base framework."""
import pytest
from common.agent_base import AgentBase, AgentResult, AgentStatus


class TestAgentResult:
    def test_initial_status(self):
        result = AgentResult(agent_code="TEST", status=AgentStatus.PENDING)
        assert result.status == AgentStatus.PENDING

    def test_add_log(self):
        result = AgentResult(agent_code="TEST", status=AgentStatus.PENDING)
        result.add_log("test message")
        assert len(result.audit_log) == 1
        assert result.audit_log[0]["message"] == "test message"

    def test_to_dict(self):
        result = AgentResult(agent_code="TEST", status=AgentStatus.SUCCESS, confidence=0.95)
        d = result.to_dict()
        assert d["agent_code"] == "TEST"
        assert d["status"] == "success"
        assert d["confidence"] == 0.95

    def test_execution_id_generated(self):
        r1 = AgentResult(agent_code="TEST", status=AgentStatus.PENDING)
        r2 = AgentResult(agent_code="TEST", status=AgentStatus.PENDING)
        assert r1.execution_id != r2.execution_id


class TestAgentBase:
    @pytest.mark.asyncio
    async def test_unimplemented_run_raises(self):
        agent = AgentBase()
        result = await agent.execute({})
        assert result.status == AgentStatus.FAILED

    @pytest.mark.asyncio
    async def test_custom_agent(self):
        class TestAgent(AgentBase):
            agent_code = "TEST"
            async def run(self, context, result):
                return {"worked": True}

        agent = TestAgent()
        result = await agent.execute({})
        assert result.status == AgentStatus.SUCCESS
        assert result.data["worked"] is True
