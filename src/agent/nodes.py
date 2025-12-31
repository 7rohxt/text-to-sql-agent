"""
All node functions for the SQL agent graph
"""
import json
from src.agent.state import SQLAgentState
from src.prompts.templates import (
    build_planning_prompt,
    build_optimized_prompt,
    build_optimized_correction_prompt,
    build_validation_and_response_prompt,
    build_simplified_prompt,
    build_alternative_prompt
)
from src.utils.llm import call_llm
from src.utils.sql_utils import clean_sql, validate_sql
from src.utils.schema_utils import (
    FULL_SCHEMA,
    ensure_schema_dict,
    schema_filter_tool
)


def planning_node(state: SQLAgentState, conn, cursor) -> SQLAgentState:
    """
    Analyzes question and decides which tables are needed.
    This is what makes it AGENTIC - the agent plans before acting.
    """
    print("🧠 Planning: Analyzing question...")
    
    prompt = build_planning_prompt(state["question"])
    response = call_llm(prompt)
    
    try:
        planned_tables = json.loads(response)
        
        if not isinstance(planned_tables, list):
            print("⚠️ Planning failed: Invalid response format")
            planned_tables = list(FULL_SCHEMA['tables'].keys())
        
        print(f"📋 Plan: Need tables {planned_tables}")
        
        filtered_schema = schema_filter_tool(planned_tables)
        print(f"✂️ Filtered schema: {len(filtered_schema['tables'])} tables, {len(filtered_schema['common_joins'])} joins")
        
        return {
            **state, 
            "planned_tables": planned_tables,
            "filtered_schema": filtered_schema
        }
    
    except json.JSONDecodeError as e:
        print(f"⚠️ Planning failed to parse JSON: {e}")
        print(f"Raw response: {response[:200]}")
        return {
            **state,
            "planned_tables": list(FULL_SCHEMA['tables'].keys()),
            "filtered_schema": FULL_SCHEMA
        }


def generate_sql_node(state: SQLAgentState, conn, cursor) -> SQLAgentState:
    """Generates SQL using filtered schema from planning node"""
    print("🔄 Generating SQL...")
    
    schema_to_use = ensure_schema_dict(state.get("filtered_schema", FULL_SCHEMA))
    
    prompt = build_optimized_prompt(state["question"], schema_to_use)
    raw_sql = call_llm(prompt)
    sql = clean_sql(raw_sql)
    
    print(f"Generated: {sql[:100]}...")
    
    return {
        **state, 
        "sql": sql,
        "total_attempts": state.get("total_attempts", 0) + 1
    }


def validate_sql_node(state: SQLAgentState, conn, cursor) -> SQLAgentState:
    """Validate SQL syntax and safety before execution"""
    print("🔍 Validating syntax...")
    is_valid, reason = validate_sql(state["sql"])
    print(f"Syntax valid: {is_valid}")
    if not is_valid:
        print(f"Reason: {reason}")
    return {
        **state, 
        "valid": is_valid, 
        "reason": None if is_valid else reason, 
        "executed": False
    }


def execute_sql_node(state: SQLAgentState, conn, cursor) -> SQLAgentState:
    """Execute SQL with proper transaction management"""
    print("⚡ Executing SQL...")
    try:
        cursor.execute(state["sql"])
        results = cursor.fetchall()
        conn.commit()
        print(f"✅ Executed! Got {len(results)} rows")
        return {
            **state, 
            "executed": True, 
            "results": results, 
            "reason": None
        }
    except Exception as e:
        conn.rollback()
        print(f"❌ Execution failed: {str(e)[:100]}")
        print("🔄 Transaction rolled back")
        return {
            **state, 
            "executed": False, 
            "results": None, 
            "reason": f"Execution error: {str(e)}"
        }


def validate_and_respond_node(state: SQLAgentState, conn, cursor) -> SQLAgentState:
    """Validates if SQL results answer the question AND generates natural language response"""
    print("🔍 Validating answer + generating response...")
    
    if not state["executed"] or not state["results"]:
        print("⚠️ Cannot validate - no results to check")
        return {
            **state, 
            "valid": False, 
            "reason": "No results to validate",
            "nl_response": "I couldn't execute the query to get an answer."
        }
    
    prompt = build_validation_and_response_prompt(
        question=state["question"],
        sql=state["sql"],
        results=state["results"]
    )
    
    response = call_llm(prompt)
    
    try:
        output = json.loads(response)
        
        is_valid = output.get("valid", False)
        reason = output.get("reason", "Unknown validation failure")
        nl_response = output.get("natural_language_response", "Unable to generate response.")
        
        if is_valid:
            print("✅ Answer validated! Generated NL response.")
            print(f"📝 Response: {nl_response[:100]}...")
        else:
            print(f"❌ Answer validation failed: {reason}")
        
        return {
            **state, 
            "valid": is_valid, 
            "reason": None if is_valid else reason,
            "nl_response": nl_response
        }
    
    except json.JSONDecodeError as e:
        print(f"⚠️ Failed to parse validation response: {e}")
        return {
            **state, 
            "valid": False, 
            "reason": "Validation parsing error",
            "nl_response": "Error processing the query results."
        }


def correct_sql_node(state: SQLAgentState, conn, cursor) -> SQLAgentState:
    """Attempt to correct SQL based on error"""
    print(f"🔧 Correcting SQL (attempt {state['total_attempts'] + 1})...")
    
    schema_to_use = ensure_schema_dict(state.get("filtered_schema", FULL_SCHEMA))
    
    prompt = build_optimized_correction_prompt(
        question=state["question"],
        schema=schema_to_use,
        previous_sql=state["sql"],
        error_reason=state["reason"]
    )
    corrected_sql = call_llm(prompt)
    sql = clean_sql(corrected_sql)
    print(f"Corrected: {sql[:100]}...")
    
    attempted = state.get("attempted_strategies", [])
    if "correct" not in attempted:
        attempted.append("correct")
    
    return {
        **state, 
        "sql": sql, 
        "retries": state["retries"] + 1,
        "total_attempts": state.get("total_attempts", 0) + 1,
        "attempted_strategies": attempted
    }


def analyze_failure_node(state: SQLAgentState, conn, cursor) -> SQLAgentState:
    """AGENTIC: Agent analyzes WHY it failed and classifies failure type"""
    print("🧠 Analyzing failure...")
    
    reason = state.get("reason", "")
    
    if "syntax" in reason.lower() or "invalid" in reason.lower():
        failure_type = "syntax_error"
        print("📊 Failure type: Syntax error")
    elif "no results" in reason.lower() or "empty" in reason.lower():
        failure_type = "no_results"
        print("📊 Failure type: No results returned")
    elif "execution" in reason.lower() or "does not exist" in reason.lower():
        failure_type = "execution_error"
        print("📊 Failure type: Execution error")
    elif not state.get("valid", False) and state.get("executed", False):
        failure_type = "semantic_error"
        print("📊 Failure type: Answer doesn't match question")
    else:
        failure_type = "unknown"
        print("📊 Failure type: Unknown")
    
    return {**state, "failure_type": failure_type}


def generate_simplified_sql_node(state: SQLAgentState, conn, cursor) -> SQLAgentState:
    """STRATEGY: Try a simpler query approach"""
    print("🔄 Strategy: Generating SIMPLIFIED SQL...")
    
    schema_to_use = ensure_schema_dict(state.get("filtered_schema", FULL_SCHEMA))
    
    prompt = build_simplified_prompt(
        question=state["question"],
        schema=schema_to_use,
        previous_sql=state["sql"],
        error_reason=state["reason"]
    )
    
    raw_sql = call_llm(prompt)
    sql = clean_sql(raw_sql)
    print(f"Simplified: {sql[:100]}...")
    
    attempted = state.get("attempted_strategies", [])
    attempted.append("simplified")
    
    return {
        **state, 
        "sql": sql, 
        "current_strategy": "simplified",
        "attempted_strategies": attempted,
        "retries": 0,
        "total_attempts": state.get("total_attempts", 0) + 1
    }


def generate_alternative_approach_node(state: SQLAgentState, conn, cursor) -> SQLAgentState:
    """STRATEGY: Try a completely different approach"""
    print("🔄 Strategy: Trying ALTERNATIVE approach...")
    
    schema_to_use = ensure_schema_dict(state.get("filtered_schema", FULL_SCHEMA))
    
    prompt = build_alternative_prompt(
        question=state["question"],
        schema=schema_to_use,
        previous_sql=state["sql"],
        error_reason=state["reason"],
        attempted_strategies=state.get("attempted_strategies", [])
    )
    
    raw_sql = call_llm(prompt)
    sql = clean_sql(raw_sql)
    print(f"Alternative: {sql[:100]}...")
    
    attempted = state.get("attempted_strategies", [])
    attempted.append("alternative")
    
    return {
        **state, 
        "sql": sql, 
        "current_strategy": "alternative",
        "attempted_strategies": attempted,
        "retries": 0,
        "total_attempts": state.get("total_attempts", 0) + 1
    }


def ask_clarification_node(state: SQLAgentState, conn, cursor) -> SQLAgentState:
    """FINAL FALLBACK: Agent admits it needs help and asks user"""
    print("💬 Strategy: Asking user for clarification...")
    
    clarification = f"""I tried multiple approaches but couldn't answer your question: "{state['question']}"

Attempts made: {state.get('total_attempts', 0)}
Strategies tried: {', '.join(state.get('attempted_strategies', ['direct']))}

Last error: {state['reason']}

Could you please:
- Rephrase your question, or
- Provide more specific details, or
- Break it into smaller questions?"""
    
    return {
        **state,
        "nl_response": clarification,
        "valid": False
    }