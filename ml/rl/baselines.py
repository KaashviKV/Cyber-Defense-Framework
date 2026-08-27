"""Shared response-policy baselines used by experiments and the live pipeline."""

from __future__ import annotations

from typing import Any

ACTIONS = ["NO_ACTION", "ALERT_ADMIN", "BLOCK_IP", "ISOLATE_HOST"]


def rule_based_action(state: dict[str, Any]) -> str:
    """
    Deterministic threshold policy used as the academic baseline.

    Bands are aligned with the risk engine (SAFE <20, LOW <40, MEDIUM <60,
    HIGH <80, CRITICAL >=80) plus CTI heat.
    """
    risk = float(state.get("risk_score", 0) or 0)
    cti = max(
        float(state.get("virustotal_score", 0) or 0),
        float(state.get("abuseipdb_score", 0) or 0),
    )
    attack = state.get("attack", "BENIGN")

    if attack == "BENIGN" and risk < 25 and cti < 20:
        return "NO_ACTION"
    if risk >= 90 or (risk >= 80 and cti >= 70):
        return "ISOLATE_HOST"
    if risk >= 70 or cti >= 60:
        return "BLOCK_IP"
    if risk >= 40:
        return "ALERT_ADMIN"
    return "NO_ACTION"


def ideal_action(state: dict[str, Any]) -> str:
    """Same bands as the environment's reward shaping (ground-truth for metrics)."""
    return rule_based_action(state)


def ml_only_action(state: dict[str, Any]) -> str:
    """Respond from attack severity only (no CTI, no fused risk)."""
    severity = float(state.get("severity", 0) or 0)
    attack = state.get("attack", "BENIGN")
    if attack == "BENIGN" or severity < 20:
        return "NO_ACTION"
    if severity >= 90:
        return "ISOLATE_HOST"
    if severity >= 70:
        return "BLOCK_IP"
    if severity >= 40:
        return "ALERT_ADMIN"
    return "NO_ACTION"


def ml_cti_action(state: dict[str, Any]) -> str:
    """Respond from max(severity, CTI) without the weighted risk fusion."""
    severity = float(state.get("severity", 0) or 0)
    cti = max(
        float(state.get("virustotal_score", 0) or 0),
        float(state.get("abuseipdb_score", 0) or 0),
    )
    heat = max(severity, cti)
    attack = state.get("attack", "BENIGN")
    if attack == "BENIGN" and cti < 20:
        return "NO_ACTION" if heat < 25 else "ALERT_ADMIN"
    if heat >= 90:
        return "ISOLATE_HOST"
    if heat >= 70:
        return "BLOCK_IP"
    if heat >= 40:
        return "ALERT_ADMIN"
    return "NO_ACTION"


def ml_cti_risk_action(state: dict[str, Any]) -> str:
    """Rule-based policy on the fused risk score (no RL)."""
    return rule_based_action(state)
