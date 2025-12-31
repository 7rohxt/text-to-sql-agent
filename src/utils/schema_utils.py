"""
Schema utilities and filters
"""
from typing import Dict, Any, List
import yaml
from pathlib import Path


# Load schema once at module level
SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "schema_summary.yaml"

with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    FULL_SCHEMA: Dict[str, Any] = yaml.safe_load(f)


def ensure_schema_dict(schema: Any) -> Dict[str, Any]:
    """Ensure schema is a dict, fallback to FULL_SCHEMA if not"""
    if isinstance(schema, dict):
        return schema
    print(f"⚠️ Warning: Invalid schema type {type(schema)}, using FULL_SCHEMA")
    return FULL_SCHEMA


def schema_filter_tool(table_names: List[str]) -> Dict[str, Any]:
    """
    Extract only specified tables and their related info from full schema.
    This is the 'tool' the agent uses to get relevant schema.
    """
    filtered_schema = {
        'tables': {},
        'hints': FULL_SCHEMA.get('hints', []),
        'common_joins': []
    }
    
    # Extract requested tables
    for table_name in table_names:
        if table_name in FULL_SCHEMA['tables']:
            filtered_schema['tables'][table_name] = FULL_SCHEMA['tables'][table_name]
    
    # Extract relevant joins (any join involving requested tables)
    for join_info in FULL_SCHEMA.get('common_joins', []):
        join_tables = set(join_info.get('tables', []))
        if join_tables.intersection(set(table_names)):
            filtered_schema['common_joins'].append(join_info)
    
    return filtered_schema