"""
Routing functions for the SQL agent graph
"""
from langgraph.graph import END
from src.agent.state import SQLAgentState
from src.config.settings import MAX_RETRIES, MAX_TOTAL_ATTEMPTS


def route_after_syntax_check(state: SQLAgentState):
    """Route after pre-execution validation"""
    if state["valid"]:
        return "execute_sql"
    if state["retries"] >= MAX_RETRIES:
        return END
    return "correct_sql"


def route_after_execution(state: SQLAgentState):
    """Route after execution - goes to combined validation+response node"""
    if state["executed"]:
        return "validate_and_respond"
    if state["retries"] >= MAX_RETRIES:
        return END
    return "correct_sql"


def route_after_validation(state: SQLAgentState):
    """Route after answer validation"""
    if state["valid"]:
        return END  # Success!
    return "analyze_failure"


def route_after_failure_analysis(state: SQLAgentState):
    """AGENTIC ROUTING: Agent chooses strategy based on failure analysis"""
    attempted = state.get("attempted_strategies", [])
    failure_type = state.get("failure_type", "unknown")
    total_attempts = state.get("total_attempts", 0)
    
    print(f"🤔 Agent deciding next move...")
    print(f"   Total attempts: {total_attempts}/{MAX_TOTAL_ATTEMPTS}")
    print(f"   Strategies tried: {attempted}")
    print(f"   Failure type: {failure_type}")
    
    # PRIMARY ESCAPE HATCH - prevents infinite loops
    if total_attempts >= MAX_TOTAL_ATTEMPTS:
        print("   ⛔ Maximum attempts exhausted - asking user")
        return "ask_clarification"
    
    # Strategy escalation based on attempts
    if "simplified" not in attempted and total_attempts >= 2:
        print("   Decision: Try simplified SQL approach")
        return "generate_simplified"
    
    if "alternative" not in attempted and total_attempts >= 4:
        print("   Decision: Try completely different approach")
        return "generate_alternative"
    
    # Default: try correction if we have attempts left
    if total_attempts < MAX_TOTAL_ATTEMPTS - 1:
        print("   Decision: Try correcting SQL")
        return "correct_sql"
    
    # Final fallback
    print("   Decision: Give up, ask user for help")
    return "ask_clarification"