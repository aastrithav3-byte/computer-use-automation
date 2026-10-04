import json

from automation.artifact_builder import ArtifactBuilder

import asyncio

from playwright.async_api import async_playwright

from automation.discovery import DiscoveryEngine


async def main():
    goal = "Find the savings balance for member 12345."

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=False
        )

        page = await browser.new_page()

        await page.goto("http://127.0.0.1:8000")

        engine = DiscoveryEngine(page)

        result = await engine.run(
            goal=goal,
            max_steps=10,
        )

        if result["status"] == "success":
            builder = ArtifactBuilder()

            artifact = builder.build(result)
            with open(
                "artifacts/discovered_account_balance.json",
                "w",
                ) as file:
                    json.dump(
                         artifact,
                         file,
                         indent=2,
                    )

            print(
                 "\nArtifact saved to "
                 "artifacts/discovered_account_balance.json"
            )

        print("\nDISCOVERY RESULT:")
        print(result)

        input("\nPress Enter to close the browser...")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())