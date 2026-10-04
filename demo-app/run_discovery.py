import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

from automation.artifact_builder import ArtifactBuilder
from automation.discovery import DiscoveryEngine


ARTIFACT_PATH = Path(
    "artifacts/discovered_account_balance.json"
)

EVIDENCE_DIR = Path("evidence")

DISCOVERY_LOG_PATH = EVIDENCE_DIR / "discovery_run.json"

DISCOVERY_SCREENSHOT_PATH = (
    EVIDENCE_DIR / "discovery_success.png"
)


async def main():
    """
    Run a genuine LLM-driven discovery against the
    live Member Servicing System and save evidence
    from the discovery run.
    """

    goal = "Find the savings balance for member 12345."

    # Make sure output directories exist.
    ARTIFACT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    EVIDENCE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=False
        )

        page = await browser.new_page()

        await page.goto(
            "http://127.0.0.1:8000"
        )

        engine = DiscoveryEngine(page)

        result = await engine.run(
            goal=goal,
            max_steps=10,
        )

        # ------------------------------------------
        # SAVE DISCOVERY EVIDENCE
        # ------------------------------------------

        evidence = {
            "goal": goal,
            "discovery_type": "llm_driven",
            "status": result.get("status"),
            "steps": result.get("steps", []),
            "final_page_text": result.get(
                "page_text"
            ),
        }

        with open(
            DISCOVERY_LOG_PATH,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                evidence,
                file,
                indent=2,
            )

        await page.screenshot(
            path=str(DISCOVERY_SCREENSHOT_PATH),
            full_page=True,
        )

        print(
            "\nDiscovery evidence saved:"
        )

        print(
            f"- {DISCOVERY_LOG_PATH}"
        )

        print(
            f"- {DISCOVERY_SCREENSHOT_PATH}"
        )

        # ------------------------------------------
        # BUILD REUSABLE ARTIFACT
        # ------------------------------------------

        if result["status"] == "success":
            builder = ArtifactBuilder()

            artifact = builder.build(result)

            with open(
                ARTIFACT_PATH,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    artifact,
                    file,
                    indent=2,
                )

            print(
                "\nArtifact saved to "
                f"{ARTIFACT_PATH}"
            )

        # ------------------------------------------
        # DISPLAY RESULT
        # ------------------------------------------

        print("\nDISCOVERY RESULT:")
        print(result)

        input(
            "\nPress Enter to close the browser..."
        )

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())