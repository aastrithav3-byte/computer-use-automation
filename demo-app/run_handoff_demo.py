import asyncio

from playwright.async_api import async_playwright

from automation.replay import ReplayEngine


async def main():
    """
    Demonstrate human-in-the-loop handoff.

    The flow intentionally contains a risky action:
    "Transfer Funds".

    The safety policy blocks automatic execution and
    transfers control of the SAME browser session to
    a human operator.
    """

    artifact = {
        "schema_version": "1.0",
        "capability_id": "human_handoff_demo",
        "capability_version": "1.0",
        "name": "Human Handoff Demo",
        "description": (
            "Demonstrate escalation of a risky action "
            "to a human operator."
        ),
        "inputs": {},
        "outputs": {},
        "steps": [
            {
                "action": "open",
                "target": "http://127.0.0.1:8000",
                "value": None,
            },
            {
                "action": "click",
                "target": "Transfer Funds",
                "value": None,
            },
        ],
    }

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=False
        )

        page = await browser.new_page()

        engine = ReplayEngine(page)

        result = await engine.run(
            artifact=artifact,
            inputs={},
        )

        print("\nHANDOFF DEMO RESULT:")
        print(result)

        input(
            "\nPress Enter to close the browser..."
        )

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())