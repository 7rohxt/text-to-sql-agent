from src.config.settings import MAX_TOTAL_ATTEMPTS


def print_result(result: dict):
    print("\n" + "=" * 70)

    if result["valid"] and result["executed"]:
        print("SUCCESS")
        print(f"\nQuestion: {result['question']}")
        print(f"\nAnswer: {result['nl_response']}")
        print(f"\nSQL: {result['sql']}")
        print(f"\nTotal Attempts: {result['total_attempts']}")
    else:
        print("❌ FAILED")
        print(f"\n🙋 Question: {result['question']}")
        print(f"\n💬 Response: {result['nl_response']}")
        print(f"\n📈 Total Attempts: {result['total_attempts']}/{MAX_TOTAL_ATTEMPTS}")
        print(f"\n🔄 Strategies Tried: {', '.join(result['attempted_strategies'])}")

    print("=" * 70)
