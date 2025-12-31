"""
SQL utility functions
"""
from typing import Tuple, Optional
import re

def preprocess_sql(sql: str) -> str:
    if not sql:
        return ""

    # Remove triple backtick code fences (```sql ... ``` or ``` ... ```)
    sql = re.sub(r"```(?:sql)?", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"```", "", sql)

    # Remove triple-quoted strings (""" ... """)
    sql = re.sub(r'^"""|"""$', "", sql.strip(), flags=re.DOTALL)

    return sql.strip()

def normalize_sql(sql: str) -> str:
    """
    Normalize SQL for safety checks:
    - Remove SQL comments
    - Collapse whitespace
    - Lowercase everything
    """
    if not sql:
        return ""

    # Remove single-line comments (-- ...)
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)

    # Remove multi-line comments (/* ... */)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)

    # Normalize whitespace
    sql = re.sub(r"\s+", " ", sql)

    return sql.strip().lower()

def clean_sql(raw_sql):
    preprocessed_sql = preprocess_sql(raw_sql)
    clean_sql = normalize_sql(preprocessed_sql)

    return clean_sql

def is_single_statement(sql: str) -> bool:
    """
    Ensure only one SQL statement is present.
    """
    return sql.count(";") <= 1

FORBIDDEN_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "truncate",
    "grant",
    "revoke",
    "replace",
    "merge",
    "call",
    "execute",
    "commit",
    "rollback",
    "savepoint"
}

def contains_forbidden_sql(sql: str) -> bool:
    """
    Check whether normalized SQL contains forbidden operations.
    Assumes input SQL is already normalized.
    """
    tokens = set(sql.split())
    return not FORBIDDEN_KEYWORDS.isdisjoint(tokens)


def is_read_only_query(sql: str) -> bool:
    """
    Allow only SELECT or WITH ... SELECT queries.
    """
    return sql.startswith("select") or sql.startswith("with")


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Validate SQL against guardrails.
    Returns (is_valid, reason).
    """
    sql = clean_sql(sql)

    if not sql:
        return False, "Empty SQL query"

    if not is_single_statement(sql):
        return False, "Multiple SQL statements detected"

    if contains_forbidden_sql(sql):
        return False, "Forbidden SQL operation detected"

    if not is_read_only_query(sql):
        return False, "Only SELECT queries are allowed"

    return True, "SQL is safe to execute"