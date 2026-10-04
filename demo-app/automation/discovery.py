import asyncio

from playwright.async_api import Page

from automation.llm_client import LLMClient
from automation.surface import BrowserSurface


class DiscoveryEngine:
    def __init__(self, page: Page):
        self.page = page
        self.surface = BrowserSurface(page)
        self.llm = LLMClient()

    async def run(self, goal: str, max_steps: int = 10):
        history = []

        for step_number in range(1, max_steps + 1):
            page_text = await self.surface.read_page()

            action = self.llm.decide_next_action(
                goal=goal,
                page_text=page_text,
                history=history,
            )
            
            action_type = action.get("action", "").lower()
            target = action.get("target")
            value = action.get("value")
            reason = action.get("reason", "")

            print(f"\n[DISCOVERY] Step {step_number}")
            print(f"Action: {action_type}")
            print(f"Target: {target}")
            print(f"Value: {value}")
            print(f"Reason: {reason}")

            history.append(
                {
                    "step": step_number,
                    "action": action_type,
                    "target": target,
                    "value": value,
                    "reason": reason,
                }
            )

            if action_type == "fill":
                await self.surface.fill_label(
                    target,
                    value,
                )

            elif action_type == "click":
                await self.surface.click_text(target)

            elif action_type == "read":
                page_text = await self.surface.read_page()

                print("\n[READ RESULT]")
                print(page_text)

            elif action_type == "done":
                print("\n[DISCOVERY COMPLETE]")

                return {
                    "status": "success",
                    "steps": history,
                    "page_text": page_text,
                }

            else:
                return {
                    "status": "failure",
                    "reason": f"Unsupported action: {action_type}",
                    "steps": history,
                }

            await asyncio.sleep(1)

        return {
            "status": "failure",
            "reason": "Maximum discovery steps reached",
            "steps": history,
        }