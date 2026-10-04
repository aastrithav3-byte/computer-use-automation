import json
import re
from typing import Any

from playwright.async_api import Page

from automation.surface import BrowserSurface


def load_artifact(path: str) -> dict[str, Any]:
    """Load a saved capability artifact from JSON."""
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def substitute(
    value: str | None,
    inputs: dict[str, str],
) -> str | None:
    """
    Replace parameters such as {{member_id}}
    with values supplied at replay time.
    """
    if value is None:
        return None

    pattern = r"\{\{([a-zA-Z0-9_]+)\}\}"

    def replace(match):
        parameter_name = match.group(1)

        if parameter_name not in inputs:
            raise ValueError(
                f"Missing required input: {parameter_name}"
            )

        return str(inputs[parameter_name])

    return re.sub(pattern, replace, value)


def extract_balance(page_text: str) -> str | None:
    """
    Extract a balance such as:
    Current Balance: $5,240.00

    Returns:
    5240.00
    """
    match = re.search(
        r"Current Balance:\s*\$([\d,]+\.\d{2})",
        page_text,
        re.IGNORECASE,
    )

    if not match:
        return None

    return match.group(1).replace(",", "")


class ReplayEngine:
    def __init__(self, page: Page):
        self.page = page
        self.surface = BrowserSurface(page)

    async def run(
        self,
        artifact: dict[str, Any],
        inputs: dict[str, str],
    ) -> dict[str, Any]:

        outputs = {}

        for step_number, step in enumerate(
            artifact["steps"],
            start=1,
        ):
            action = step["action"].lower()

            target = substitute(
                step.get("target"),
                inputs,
            )

            value = substitute(
                step.get("value"),
                inputs,
            )

            print(
                f"[REPLAY] Step {step_number}: "
                f"{action} -> {target}"
            )

            try:
                if action == "open":
                    await self.surface.open(target)

                elif action == "fill":
                    await self.surface.fill_label(
                        target,
                        value,
                    )

                elif action == "click":
                    await self.surface.click_text(target)

                elif action == "read":
                    page_text = (
                        await self.surface.read_page()
                    )

                    save_as = step.get("save_as")

                    if save_as:
                        outputs[save_as] = page_text

                else:
                    return {
                        "status": "failure",
                        "reason": "unsupported_action",
                        "step": step_number,
                        "action": action,
                        "outputs": outputs,
                    }

                # Check the page after every successful action.
                page_text = await self.surface.read_page()

                # Expected business outcome:
                # the requested member does not exist.
                if "Member Not Found" in page_text:
                    return {
                        "status": "business_outcome",
                        "code": "MEMBER_NOT_FOUND",
                        "step": step_number,
                        "outputs": outputs,
                    }

                # Expected business outcome:
                # member exists but requested account does not.
                if "Account Not Found" in page_text:
                    return {
                        "status": "business_outcome",
                        "code": "ACCOUNT_NOT_FOUND",
                        "step": step_number,
                        "outputs": outputs,
                    }

            except Exception as error:
                return {
                    "status": "failure",
                    "reason": "step_failed",
                    "step": step_number,
                    "action": action,
                    "target": target,
                    "error": str(error),
                    "outputs": outputs,
                }

        page_text = await self.surface.read_page()

        checkpoint = artifact.get(
            "success_checkpoint"
        )

        if checkpoint:
            expected_text = checkpoint.get("value")

            if (
                expected_text
                and expected_text not in page_text
            ):
                return {
                    "status": "failure",
                    "reason": "checkpoint_failed",
                    "expected": expected_text,
                    "outputs": outputs,
                }

        balance = extract_balance(page_text)

        if balance is not None:
            outputs["balance"] = balance

        return {
            "status": "success",
            "outputs": outputs,
        }