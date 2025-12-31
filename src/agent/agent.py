"""
Main SQL Agent class and graph construction
"""
from langgraph.graph import StateGraph, END
from src.agent.state import SQLAgentState
from src.agent.nodes import (
    planning_node,
    generate_sql_node,
    validate_sql_node,
    execute_sql_node,
    validate_and_respond_node,
    correct_sql_node,
    analyze_failure_node,
    generate_simplified_sql_node,
    generate_alternative_approach_node,
    ask_clarification_node
)
from src.agent.routing import (
    route_after_syntax_check,
    route_after_execution,
    route_after_validation,
    route_after_failure_analysis
)
from src.db.db_connection import get_db_connection


class SQLAgent:
    """
    Agentic SQL generation system with planning, execution, and self-correction
    """
    
    def __init__(self):
        """Initialize the SQL agent with database connection and graph"""
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        self.graph = self._build_graph()
        print("✅ SQL Agent initialized")
    
    def _build_graph(self):
        """Build the LangGraph workflow"""
        graph = StateGraph(SQLAgentState)
        
        # Create wrapper functions that inject conn and cursor
        def wrap_node(node_func):
            return lambda state: node_func(state, self.conn, self.cursor)
        
        # Add all nodes
        graph.add_node("planning", wrap_node(planning_node))
        graph.add_node("generate_sql", wrap_node(generate_sql_node))
        graph.add_node("validate_sql", wrap_node(validate_sql_node))
        graph.add_node("execute_sql", wrap_node(execute_sql_node))
        graph.add_node("validate_and_respond", wrap_node(validate_and_respond_node))
        graph.add_node("correct_sql", wrap_node(correct_sql_node))
        graph.add_node("analyze_failure", wrap_node(analyze_failure_node))
        graph.add_node("generate_simplified", wrap_node(generate_simplified_sql_node))
        graph.add_node("generate_alternative", wrap_node(generate_alternative_approach_node))
        graph.add_node("ask_clarification", wrap_node(ask_clarification_node))
        
        # Set entry point
        graph.set_entry_point("planning")
        
        # Define edges
        graph.add_edge("planning", "generate_sql")
        graph.add_edge("generate_sql", "validate_sql")
        
        # Conditional edges
        graph.add_conditional_edges(
            "validate_sql",
            route_after_syntax_check,
            {
                "execute_sql": "execute_sql",
                "correct_sql": "correct_sql",
                END: END
            }
        )
        
        graph.add_conditional_edges(
            "execute_sql",
            route_after_execution,
            {
                "validate_and_respond": "validate_and_respond",
                "correct_sql": "correct_sql",
                END: END
            }
        )
        
        graph.add_conditional_edges(
            "validate_and_respond",
            route_after_validation,
            {
                "analyze_failure": "analyze_failure",
                END: END
            }
        )
        
        graph.add_conditional_edges(
            "analyze_failure",
            route_after_failure_analysis,
            {
                "correct_sql": "correct_sql",
                "generate_simplified": "generate_simplified",
                "generate_alternative": "generate_alternative",
                "ask_clarification": "ask_clarification"
            }
        )
        
        # Strategy nodes back to validation
        graph.add_edge("generate_simplified", "validate_sql")
        graph.add_edge("generate_alternative", "validate_sql")
        graph.add_edge("correct_sql", "validate_sql")
        graph.add_edge("ask_clarification", END)

        return graph.compile()
    
    def query(self, question: str) -> dict:
        """
        Main method to query the agent with a natural language question
        
        Args:
            question: Natural language question
            
        Returns:
            dict with keys: question, sql, nl_response, valid, total_attempts
        """
        initial_state: SQLAgentState = {
            "question": question,
            "sql": None,
            "valid": False,
            "reason": None,
            "retries": 0,
            "executed": False,
            "results": None,
            "nl_response": None,
            "failure_type": None,
            "attempted_strategies": [],
            "current_strategy": "direct",
            "planned_tables": None,
            "filtered_schema": None,
            "total_attempts": 0
        }
        
        final_state = self.graph.invoke(initial_state)
    
        return {
            "question": final_state["question"],
            "sql": final_state.get("sql"),
            "nl_response": final_state.get("nl_response"),
            "valid": final_state.get("valid", False),
            "executed": final_state.get("executed", False),
            "results": final_state.get("results"),
            "total_attempts": final_state.get("total_attempts", 0),
            "attempted_strategies": final_state.get("attempted_strategies", [])
        }

    def close(self):
        """Close database connection"""
        self.cursor.close()
        self.conn.close()
        print("✅ Database connection closed")