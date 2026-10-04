import json
from openai import OpenAI


class LLMClient:
    def __init__(self):
        self.client = OpenAI()

    def decide_next_action(
        self,
        goal: str,
        page_text: str,
        history: list,
    ) -> dict:

        history_text = json.dumps(
            history,
            indent=2,
        )

        prompt = f"""
You are controlling a web browser to complete a task.

GOAL:
{goal}

CURRENT PAGE:
{page_text}

PREVIOUS ACTIONS:
{history_text}

Choose exactly ONE next action.

Allowed actions:
- fill
- click
- read
- done

Important rules:

1. Do not repeat an action that has already succeeded unless the page clearly requires it.
2. Use the CURRENT PAGE to decide what is available now.
3. If the requested information is already visible, use "done".
4. For a fill action, include the value.
5. For a click action, use the exact visible text of the target.
6. Return ONLY valid JSON.

Examples:

{{
    "action": "fill",
    "target": "Member ID",
    "value": "12345",
    "reason": "The member must be searched first."
}}

{{
    "action": "click",
    "target": "Search Member",
    "reason": "The member ID has already been entered."
}}

{{
    "action": "click",
    "target": "Open Member",
    "reason": "The correct member is visible."
}}

{{
    "action": "click",
    "target": "Savings",
    "reason": "The goal asks for the savings balance."
}}

{{
    "action": "done",
    "reason": "The savings account balance is visible on the page."
}}
"""

        response = self.client.responses.create(
            model="gpt-6-luna",
            input=prompt,
        )

        text = response.output_text.strip()

        return json.loads(text)