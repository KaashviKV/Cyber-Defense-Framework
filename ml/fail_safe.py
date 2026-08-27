"""Fail-safe policy when CTI or evidence is missing. Does not change DQN weights."""

from __future__ import annotations


def apply_fail_safe(action: str, attack_name: str, cti_status: str) -> tuple[str, bool, str | None]:
    if cti_status == "unknown" and attack_name and attack_name != "BENIGN" and action == "NO_ACTION":
        return (
            "ALERT_ADMIN",
            True,
            "CTI unavailable: treated as unknown (not clean). Fail-safe ALERT instead of allowing non-benign traffic.",
        )
    return action, False, None
