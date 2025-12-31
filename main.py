"""
Main entry point for the SQL Agent
"""
from dotenv import load_dotenv
from src.agent.agent import SQLAgent
from src.config.settings import MAX_TOTAL_ATTEMPTS

# Load environment variables
load_dotenv()


def print_result(result: dict):
    """Pretty print agent result"""
    print("\n" + "="*70)
    if result["valid"] and result["executed"]:
        print("✅ SUCCESS")
        print(f"\n🙋 Question: {result['question']}")
        print(f"\n💬 Answer: {result['nl_response']}")
        print(f"\n🔧 SQL: {result['sql']}")
        print(f"\n📈 Total Attempts: {result['total_attempts']}")
    else:
        print("❌ FAILED")
        print(f"\n🙋 Question: {result['question']}")
        print(f"\n💬 Response: {result['nl_response']}")
        print(f"\n📈 Total Attempts: {result['total_attempts']}/{MAX_TOTAL_ATTEMPTS}")
        print(f"\n🔄 Strategies Tried: {', '.join(result['attempted_strategies'])}")
    print("="*70)


def main():
    """Main function to run the SQL agent"""
    # Initialize agent
    agent = SQLAgent()
    
    # Test questions
    test_questions = [
        "Show me the top 5 most ordered products",
        "What's the average profit margin per product category last month?",  # Impossible
        "Which department has the most products?"
    ]
    
    # Run tests
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: {question}")
        print(f"{'='*70}")
        
        result = agent.query(question)
        print_result(result)
    
    # Close connection
    agent.close()


if __name__ == "__main__":
    main()