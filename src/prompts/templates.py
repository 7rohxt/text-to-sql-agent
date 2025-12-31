"""
Prompt templates for the SQL agent
"""
import json
from typing import Dict, Any, List
from src.utils.schema_utils import FULL_SCHEMA


def build_planning_prompt(question: str) -> str:
    """Prompt for planning node to decide which tables are needed"""
    available_tables = list(FULL_SCHEMA['tables'].keys())
    table_descriptions = {
        name: FULL_SCHEMA['tables'][name].get('description', 'No description')
        for name in available_tables
    }
    
    return f"""
You are a database query planner. Analyze the user's question and decide which tables are needed.

Available tables:
{json.dumps(table_descriptions, indent=2)}

User question:
{question}

Your task:
1. Identify which tables are needed to answer this question
2. Consider foreign key relationships (you may need junction tables)
3. Output ONLY a JSON array of table names

Rules:
- Include ALL tables needed for joins
- If asking about products AND orders, include order_products_* tables
- Don't include unnecessary tables
- Output ONLY valid JSON, no explanation

Example outputs:
["products"]
["orders", "order_products_prior", "products"]
["products", "aisles", "departments"]

JSON array of table names:
""".strip()


def build_optimized_prompt(question: str, schema: Dict[str, Any]) -> str:
    """Optimized SQL generation prompt"""
    return f"""
You are an expert PostgreSQL SQL generator.

CRITICAL RULES:
- Output ONLY one SQL SELECT query
- Do NOT include markdown, backticks, or explanations
- Use ONLY tables and columns from the schema
- Follow join templates strictly
- Never invent joins or columns
- Prefer correctness over brevity

Database schema with semantics:
{schema}

User question:
{question}

SQL:
""".strip()


def build_optimized_correction_prompt(
    question: str,
    schema: Dict[str, Any],
    previous_sql: str,
    error_reason: str
) -> str:
    """Optimized correction prompt with available columns list"""
    
    # Safety check
    if not isinstance(schema, dict):
        from src.utils.schema_utils import FULL_SCHEMA
        schema = FULL_SCHEMA
    
    # Extract actual available columns SAFELY
    available_columns = []
    tables = schema.get('tables', {})
    
    if isinstance(tables, dict):
        for table_name, table_info in tables.items():
            if isinstance(table_info, dict):
                columns = table_info.get('columns', [])
                if isinstance(columns, list):
                    for col in columns:
                        if isinstance(col, dict) and 'name' in col:
                            available_columns.append(f"{table_name}.{col['name']}")
    
    # Fallback if no columns found
    if not available_columns:
        available_columns = ["Unable to extract column list"]
    
    return f"""
You are an expert PostgreSQL SQL generator. The previous SQL query failed.

Failure reason:
{error_reason}

⚠️ CRITICAL: If the error mentions columns that DON'T EXIST, you must NOT use them.

AVAILABLE COLUMNS ONLY:
{', '.join(available_columns[:50])}

ABSOLUTE REQUIREMENTS:
1. Use ONLY columns listed above - do NOT invent columns
2. If the question asks for data we don't have (profit, margin, price), return a message:
   SELECT 'Data not available in database' as message
3. Output ONLY valid SELECT query with existing columns
4. No markdown, no backticks, no explanations

Original question:
{question}

Failed SQL:
{previous_sql}

Corrected SELECT query (using ONLY existing columns):
""".strip()


def build_validation_and_response_prompt(
    question: str,
    sql: str,
    results: list
) -> str:
    """
    Creates a prompt for LLM to:
    1. Validate if results answer the question
    2. Generate a natural language response
    """
    sample_results = results[:10]
    total_rows = len(results)
    
    return f"""
You are a SQL result validator and response generator.

Your tasks:
1. Validate if the SQL query results actually answer the user's question
2. Generate a natural, conversational answer for the user

CRITICAL RULES:
- Output ONLY valid JSON with three fields: "valid" (boolean), "reason" (string), "natural_language_response" (string)
- For validation: Check if query targeted RIGHT tables/columns and results are plausible
- For response: Be conversational, clear, and directly answer the question
- Include relevant numbers/data from results
- Don't mention SQL or technical details in the natural language response
- If results are empty or wrong, explain what went wrong in a user-friendly way

User Question:
{question}

SQL Query Executed:
{sql}

Results (showing {len(sample_results)} of {total_rows} total rows):
{sample_results}

Validation Checklist:
1. Does the SQL query the correct tables/columns for this question?
2. Do the returned values semantically match what was asked?
3. Are the results plausible? (no negative counts, reasonable magnitudes)

Response Guidelines:
- Be direct and conversational
- Use numbers from the results
- Format large numbers readably (e.g., "49,688" not "49688")
- If multiple rows, summarize or show top results
- Don't say "according to the query" - just answer

Output JSON format:
{{
    "valid": true/false,
    "reason": "brief explanation of validation decision",
    "natural_language_response": "conversational answer to user's question"
}}

JSON:
""".strip()


def build_simplified_prompt(
    question: str,
    schema: Dict[str, Any],
    previous_sql: str,
    error_reason: str
) -> str:
    """Generate a simpler query approach"""
    return f"""
You are an expert PostgreSQL SQL generator.

The previous complex query failed. Generate a SIMPLER query.

CRITICAL RULES:
- Use the SIMPLEST approach possible
- Avoid complex joins if possible
- Use single table if feasible
- Output ONLY SQL, no markdown

Database schema:
{schema}

User question:
{question}

Previous failed SQL (too complex):
{previous_sql}

Failure reason:
{error_reason}

Generate SIMPLER SQL:
""".strip()


def build_alternative_prompt(
    question: str,
    schema: Dict[str, Any],
    previous_sql: str,
    error_reason: str,
    attempted_strategies: List[str]
) -> str:
    """Generate a completely different approach"""
    return f"""
You are an expert PostgreSQL SQL generator.

Previous attempts failed. Think differently about this problem.

CRITICAL RULES:
- Approach this from a DIFFERENT angle
- Consider alternative tables or join patterns
- Use different aggregation methods if applicable
- Output ONLY SQL, no markdown

Database schema:
{schema}

User question:
{question}

Previous attempts that failed:
{attempted_strategies}

Previous SQL:
{previous_sql}

Failure reason:
{error_reason}

Generate ALTERNATIVE SQL approach:
""".strip()