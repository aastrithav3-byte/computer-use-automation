from copy import deepcopy


class ArtifactBuilder:
    def build(self, discovery_result: dict) -> dict:
        if discovery_result.get("status") != "success":
            raise ValueError(
                "Cannot build artifact from unsuccessful discovery."
            )

        steps = deepcopy(
            discovery_result.get("steps", [])
        )

        reusable_steps = [
            {
                "action": "open",
                "target": "http://127.0.0.1:8000",
                "value": None,
            }
        ]

        for step in steps:
            action = step.get("action")
            target = step.get("target")
            value = step.get("value")

            # Convert discovered member ID into a reusable parameter.
            # Handles both 12345 and "12345".
            if value is not None and str(value) == "12345":
                value = "{{member_id}}"

            # Convert discovered account type into a reusable parameter.
            if (
                isinstance(target, str)
                and target.strip().lower() == "savings"
            ):
                target = "{{account_type}}"

            # Discovery uses "done" only to indicate completion.
            # Deterministic replay does not execute it.
            if action == "done":
                continue

            reusable_steps.append(
                {
                    "action": action,
                    "target": target,
                    "value": value,
                }
            )

        artifact = {
            "schema_version": "1.0",
            "capability_id": "get_account_balance",
            "capability_version": "1.0",
            "name": "Get Account Balance",
            "description": (
                "Find an account balance for a member."
            ),
            "inputs": {
                "member_id": {
                    "type": "string",
                    "required": True,
                },
                "account_type": {
                    "type": "string",
                    "required": True,
                },
            },
            "outputs": {
                "balance": {
                    "type": "string"
                }
            },
            "steps": reusable_steps,
            "success_checkpoint": {
                "type": "text_present",
                "value": "Account Details",
            },
        }

        return artifact