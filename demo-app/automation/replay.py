import json
import re
from typing import Any

from playwright.async_api import Page

from automation.surface import BrowserSurface
from automation.policy import (
    SafetyPolicy,
    PolicyViolation,
    redact,
)


def load_artifact(path: str) -> dict[str, Any]:
    """
    Load a saved capability artifact from JSON.
    """
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
    """
    Deterministically executes a saved capability artifact.

    The replay engine:
    - substitutes runtime inputs
    - enforces the safety policy
    - executes browser actions
    - detects business outcomes
    - verifies the success checkpoint
    - extracts declared outputs
    """

    def __init__(
        self,
        page: Page,
        policy: SafetyPolicy | None = None,
    ):
        self.page = page
        self.surface = BrowserSurface(page)

        # Use the supplied policy or the default
        # local-demo safety policy.
        self.policy = policy or SafetyPolicy()

    async def run(
        self,
        artifact: dict[str, Any],
        inputs: dict[str, str],
    ) -> dict[str, Any]:

        outputs: dict[str, Any] = {}

        for step_number, step in enumerate(
            artifact["steps"],
            start=1,
        ):
            action = step["action"].lower()

            try:
                # Resolve runtime parameters such as
                # {{member_id}} and {{account_type}}.
                target = substitute(
                    step.get("target"),
                    inputs,
                )

                value = substitute(
                    step.get("value"),
                    inputs,
                )

                # Do not expose filled values in logs.
                # A fill value may contain PII or other
                # sensitive financial information.
                if action == "fill":
                    log_target = target
                    log_value = redact(value)

                    print(
                        f"[REPLAY] Step {step_number}: "
                        f"{action} -> {log_target} "
                        f"value={log_value}"
                    )

                else:
                    print(
                        f"[REPLAY] Step {step_number}: "
                        f"{action} -> {target}"
                    )

                # -----------------------------------
                # SAFETY POLICY
                # -----------------------------------
                # Validate the action before touching
                # the live application.
                self.policy.validate_action(
                    action=action,
                    target=target,
                )

                # -----------------------------------
                # EXECUTE ACTION
                # -----------------------------------

                if action == "open":
                    await self.surface.open(target)

                elif action == "fill":
                    await self.surface.fill_label(
                        target,
                        value,
                    )

                elif action == "click":
                    clicked = await self.surface.click_text(
                        target
                    )

                    # If the requested account type
                    # does not exist for this member,
                    # this is a legitimate business
                    # outcome rather than a crash.
                    if not clicked:
                        if target == inputs.get(
                            "account_type"
                        ):
                            return {
                                "status": "business_outcome",
                                "code": "ACCOUNT_NOT_FOUND",
                                "step": step_number,
                                "outputs": outputs,
                            }

                        # A different missing target
                        # means the deterministic flow
                        # could not continue.
                        return {
                            "status": "failure",
                            "reason": "target_not_found",
                            "step": step_number,
                            "action": action,
                            "target": target,
                            "outputs": outputs,
                        }

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

                # -----------------------------------
                # CHECK PAGE STATE
                # -----------------------------------

                page_text = await self.surface.read_page()

                # Expected business outcome:
                # requested member does not exist.
                if "Member Not Found" in page_text:
                    return {
                        "status": "business_outcome",
                        "code": "MEMBER_NOT_FOUND",
                        "step": step_number,
                        "outputs": outputs,
                    }

                # Expected business outcome:
                # member exists but requested
                # account does not.
                if "Account Not Found" in page_text:
                    return {
                        "status": "business_outcome",
                        "code": "ACCOUNT_NOT_FOUND",
                        "step": step_number,
                        "outputs": outputs,
                    }

            # ---------------------------------------
            # SAFETY FAILURE
            # ---------------------------------------

            except PolicyViolation as error:
                return {
                    "status": "failure",
                    "reason": "policy_violation",
                    "step": step_number,
                    "action": action,
                    "target": (
                        redact(target)
                        if action == "fill"
                        else target
                    ),
                    "error": str(error),
                    "outputs": outputs,
                }

            # ---------------------------------------
            # TECHNICAL FAILURE
            # ---------------------------------------

            except Exception as error:
                return {
                    "status": "failure",
                    "reason": "step_failed",
                    "step": step_number,
                    "action": action,
                    "target": (
                        redact(target)
                        if action == "fill"
                        else target
                    ),
                    "error": str(error),
                    "outputs": outputs,
                }

        # -------------------------------------------
        # FINAL PAGE VALIDATION
        # -------------------------------------------

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

        # -------------------------------------------
        # OUTPUT EXTRACTION
        # -------------------------------------------

        balance = extract_balance(page_text)

        if balance is not None:
            outputs["balance"] = balance

        return {
            "status": "success",
            "outputs": outputs,
        }