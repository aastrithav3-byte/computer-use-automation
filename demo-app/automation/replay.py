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
from automation.handoff import HumanHandoff


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
    - verifies success checkpoints
    - extracts outputs
    - escalates risky actions to a human
    """

    def __init__(
        self,
        page: Page,
        policy: SafetyPolicy | None = None,
        handoff: HumanHandoff | None = None,
    ):
        self.page = page
        self.surface = BrowserSurface(page)
        self.policy = policy or SafetyPolicy()
        self.handoff = handoff or HumanHandoff()

    async def run(
        self,
        artifact: dict[str, Any],
        inputs: dict[str, str],
    ) -> dict[str, Any]:

        outputs: dict[str, Any] = {}

        capability = artifact.get(
            "capability_id",
            "unknown_capability",
        )

        goal = artifact.get(
            "description",
            "Execute saved capability",
        )

        for step_number, step in enumerate(
            artifact["steps"],
            start=1,
        ):
            action = step["action"].lower()

            target = None
            value = None

            try:
                target = substitute(
                    step.get("target"),
                    inputs,
                )

                value = substitute(
                    step.get("value"),
                    inputs,
                )

                # -----------------------------------
                # SAFE LOGGING
                # -----------------------------------

                if action == "fill":
                    print(
                        f"[REPLAY] Step {step_number}: "
                        f"{action} -> {target} "
                        f"value={redact(value)}"
                    )
                else:
                    print(
                        f"[REPLAY] Step {step_number}: "
                        f"{action} -> {target}"
                    )

                # -----------------------------------
                # SAFETY POLICY
                # -----------------------------------

                try:
                    self.policy.validate_action(
                        action=action,
                        target=target,
                    )

                except PolicyViolation as policy_error:

                    # Risky actions are escalated to a
                    # human instead of being executed
                    # automatically.
                    if (
                        action == "click"
                        and target
                        and any(
                            risky_term
                            in target.lower()
                            for risky_term
                            in self.policy.risky_terms
                        )
                    ):
                        handoff_result = (
                            await self.handoff.request_intervention(
                                page=self.page,
                                capability=capability,
                                goal=goal,
                                step=step_number,
                                reason=str(policy_error),
                            )
                        )

                        if (
                            handoff_result.get("status")
                            != "resumed"
                        ):
                            return {
                                "status": "failure",
                                "reason": "human_handoff_failed",
                                "step": step_number,
                                "outputs": outputs,
                            }

                        # Human performed this risky step
                        # manually in the same session.
                        # Do NOT execute it automatically.
                        print(
                            f"[REPLAY] Step {step_number}: "
                            "human completed risky action; "
                            "automation resumed"
                        )

                        continue

                    # Non-risk policy violations such as
                    # navigating to an unapproved host
                    # remain blocked.
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
                        "error": str(policy_error),
                        "outputs": outputs,
                    }

                # -----------------------------------
                # EXECUTE SAFE ACTION
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
                # CHECK BUSINESS OUTCOMES
                # -----------------------------------

                page_text = await self.surface.read_page()

                if "Member Not Found" in page_text:
                    return {
                        "status": "business_outcome",
                        "code": "MEMBER_NOT_FOUND",
                        "step": step_number,
                        "outputs": outputs,
                    }

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
                    "target": (
                        redact(target)
                        if action == "fill"
                        else target
                    ),
                    "error": str(error),
                    "outputs": outputs,
                }

        # -------------------------------------------
        # FINAL CHECKPOINT
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