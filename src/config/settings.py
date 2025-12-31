"""
Configuration settings for the SQL agent
"""

# Retry and attempt limits
MAX_RETRIES = 2  # Max retries per strategy before escalating
MAX_TOTAL_ATTEMPTS = 6  # Total attempts across all strategies

# LLM Configuration
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0