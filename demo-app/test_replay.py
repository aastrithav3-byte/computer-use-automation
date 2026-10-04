import pytest
from playwright.async_api import async_playwright

from automation.replay import ReplayEngine, load_artifact


ARTIFACT_PATH = "artifacts/discovered_account_balance.json"


async def run_replay(inputs):
    artifact = load_artifact(ARTIFACT_PATH)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()

        engine = ReplayEngine(page)
        result = await engine.run(
            artifact=artifact,
            inputs=inputs,
        )

        await browser.close()

        return result


@pytest.mark.asyncio
async def test_successful_checking_account():
    result = await run_replay(
        {
            "member_id": "12345",
            "account_type": "Checking",
        }
    )

    assert result["status"] == "success"
    assert result["outputs"]["balance"] == "3120.25"


@pytest.mark.asyncio
async def test_account_not_found():
    result = await run_replay(
        {
            "member_id": "12345",
            "account_type": "Credit Card",
        }
    )

    assert result["status"] == "business_outcome"
    assert result["code"] == "ACCOUNT_NOT_FOUND"


@pytest.mark.asyncio
async def test_member_not_found():
    result = await run_replay(
        {
            "member_id": "99999",
            "account_type": "Checking",
        }
    )

    assert result["status"] == "business_outcome"
    assert result["code"] == "MEMBER_NOT_FOUND"