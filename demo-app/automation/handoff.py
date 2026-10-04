import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class HumanHandoff:
    """
    Minimal human-in-the-loop handoff mechanism.

    The same browser session remains alive while automation
    pauses. A human can manually operate that browser and
    then signal the automation to resume.

    Intervention events are recorded for observability.
    """

    def __init__(
        self,
        evidence_dir: str = "evidence",
    ):
        self.evidence_dir = Path(evidence_dir)

        self.evidence_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.control_owner = "automation"

    def _timestamp(self) -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()

    def _write_event(
        self,
        event: dict[str, Any],
    ) -> None:
        """
        Append an intervention event to a JSONL evidence log.
        """

        log_path = (
            self.evidence_dir
            / "human_handoff.jsonl"
        )

        with log_path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(event) + "\n"
            )

    async def request_intervention(
        self,
        *,
        page,
        capability: str,
        goal: str,
        step: int,
        reason: str,
    ) -> dict[str, Any]:
        """
        Pause automation and transfer control of the
        existing live browser session to a human.
        """

        self.control_owner = "human"

        screenshot_path = (
            self.evidence_dir
            / f"handoff_step_{step}.png"
        )

        await page.screenshot(
            path=str(screenshot_path),
            full_page=True,
        )

        event = {
            "event": "human_intervention_requested",
            "timestamp": self._timestamp(),
            "capability": capability,
            "goal": goal,
            "step": step,
            "reason": reason,
            "control_owner": self.control_owner,
            "screenshot": str(screenshot_path),
        }

        self._write_event(event)

        print("\n" + "=" * 60)
        print("HUMAN INTERVENTION REQUIRED")
        print("=" * 60)
        print(f"Capability: {capability}")
        print(f"Goal: {goal}")
        print(f"Step: {step}")
        print(f"Reason: {reason}")
        print()
        print(
            "Automation is paused. "
            "The existing browser session remains open."
        )
        print(
            "Please complete the required manual action "
            "in that SAME browser window."
        )
        print()

        input(
            "When finished, press Enter here "
            "to return control to automation..."
        )

        self.control_owner = "automation"

        resume_event = {
            "event": "human_control_returned",
            "timestamp": self._timestamp(),
            "capability": capability,
            "goal": goal,
            "step": step,
            "control_owner": self.control_owner,
        }

        self._write_event(resume_event)

        print(
            "\nControl returned to automation."
        )

        return {
            "status": "resumed",
            "control_owner": self.control_owner,
            "step": step,
        }