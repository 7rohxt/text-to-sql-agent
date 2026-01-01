"""
Tests for the SQL Agent
"""
import pytest
from src.agent.agent import SQLAgent


@pytest.fixture
def agent():
    """Create agent instance for tests"""
    agent = SQLAgent()
    yield agent
    agent.close()


def test_simple_query(agent):
    """Test simple query that should succeed"""
    result = agent.query("Show me the top 5 most ordered products")
    
    assert result["valid"] is True
    assert result["executed"] is True
    assert result["sql"] is not None
    assert result["nl_response"] is not None
    assert result["total_attempts"] <= 2  # Should succeed quickly


def test_impossible_query(agent):
    """Test impossible query that should fail gracefully"""
    result = agent.query("What's the average profit margin per product category?")
    
    assert result["valid"] is False  # Should fail
    assert "clarification" in result["nl_response"].lower() or "not available" in result["nl_response"].lower()
    assert result["total_attempts"] > 0


def test_department_query(agent):
    """Test department-related query"""
    result = agent.query("Which department has the most products?")
    
    assert result["valid"] is True
    assert result["executed"] is True
    assert "department" in result["sql"].lower()