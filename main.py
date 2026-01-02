"""
Main entry point for the SQL Agent
"""
from dotenv import load_dotenv
from src.agent.agent import SQLAgent

load_dotenv()


def main(query: str) -> dict:
    """
    Execute the SQL agent for a single query.
    Returns the result dict only.
    """
    agent = SQLAgent()
    try:
        return agent.query(query)
    finally:
        agent.close()

if __name__ == "__main__":
    from src.utils.print_result import print_result

    q = "Show me the top 5 most ordered products"
    result = main(q)
    print_result(result)