from dataclasses import dataclass
from urllib.parse import urlparse


class PolicyViolation(Exception):
    """Raised when an automation action violates the safety policy."""


@dataclass
class SafetyPolicy:
    """
    Safety policy for discovery and deterministic replay.

    The policy restricts:
    - which hosts the automation may access
    - which action types it may perform
    - risky/irreversible actions
    """

    allowed_hosts: tuple[str, ...] = (
        "127.0.0.1",
        "localhost",
    )

    allowed_actions: tuple[str, ...] = (
        "open",
        "fill",
        "click",
        "read",
    )

    # Actions containing these terms require human approval.
    risky_terms: tuple[str, ...] = (
        "delete",
        "transfer",
        "submit payment",
        "send payment",
        "close account",
        "confirm transaction",
    )

    def validate_action(
        self,
        action: str,
        target: str | None,
    ) -> None:
        """Validate an action before execution."""

        action = action.lower()

        if action not in self.allowed_actions:
            raise PolicyViolation(
                f"Action '{action}' is not permitted."
            )

        if action == "open":
            self.validate_url(target)

        if action == "click" and target:
            self.validate_risky_action(target)

    def validate_url(self, url: str | None) -> None:
        """Prevent navigation outside approved applications."""

        if not url:
            raise PolicyViolation(
                "Navigation target is missing."
            )

        parsed = urlparse(url)

        if parsed.hostname not in self.allowed_hosts:
            raise PolicyViolation(
                f"Navigation to host "
                f"'{parsed.hostname}' is not permitted."
            )

    def validate_risky_action(self, target: str) -> None:
        """
        Risky or irreversible actions must not be
        executed automatically.
        """

        normalized = target.lower()

        for risky_term in self.risky_terms:
            if risky_term in normalized:
                raise PolicyViolation(
                    f"Risky action requires human approval: "
                    f"'{target}'"
                )


def redact(value: str | None) -> str | None:
    """
    Redact values before they are written to logs.

    We intentionally avoid logging raw invocation values,
    because production inputs may contain financial or
    personally identifiable information.
    """

    if value is None:
        return None

    return "[REDACTED]"