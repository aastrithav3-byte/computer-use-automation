import json

from automation.llm_client import LLMClient


def main():
    client = LLMClient()

    goal = "Find the savings balance for member 12345."

    page_text = """
    Member Servicing System

    Member Search

    Enter a Member ID to search for a member.

    Member ID

    Search Member
    """

    action = client.decide_next_action(
        goal=goal,
        page_text=page_text,
    )

    print("\nLLM DECISION:")
    print(json.dumps(action, indent=2))


if __name__ == "__main__":
    main()