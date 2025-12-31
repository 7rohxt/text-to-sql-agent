"""
State definition for the SQL agent
"""
from typing import TypedDict, Optional, List, Dict, Any


class SQLAgentState(TypedDict):
    """State schema for the SQL agent"""
    # Core fields
    question: str
    sql: Optional[str]
    valid: bool
    reason: Optional[str]
    
    # Execution tracking
    executed: bool
    results: Optional[list]
    nl_response: Optional[str]
    
    # Strategy tracking
    retries: int
    total_attempts: int
    failure_type: Optional[str]
    attempted_strategies: List[str]
    current_strategy: str
    
    # Planning fields
    planned_tables: Optional[List[str]]
    filtered_schema: Optional[Dict[str, Any]]