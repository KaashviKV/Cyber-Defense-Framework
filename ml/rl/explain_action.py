"""
State/action context for the RL recommendation.

This is not a claim that DQN produces human-readable reasoning.
It describes the observed state and how that state typically maps to actions
in the trained reward bands, for analyst/viva explanation.
"""

from __future__ import annotations

from typing import Any

from ml.rl.baselines import rule_based_action


def explain_rl_decision(
    *,
    action: str,
    attack: str,
    severity: float,
    confidence: float,
    risk_score: float,
    risk_level: str,
    virustotal_score: float,
    abuseipdb_score: float,
    q_values: list[float] | None = None,
    model_version: str = "v2_cti",
) -> dict[str, Any]:
    cti_heat = max(float(virustotal_score or 0), float(abuseipdb_score or 0))
    baseline = rule_based_action({
        "attack": attack,
        "risk_score": risk_score,
        "virustotal_score": virustotal_score,
        "abuseipdb_score": abuseipdb_score,
    })

    if action == "ISOLATE_HOST":
        summary = (
            "The policy selected ISOLATE_HOST given critical-range risk and/or "
            "strong CTI agreement. Isolation is the strongest simulated containment."
        )
    elif action == "BLOCK_IP":
        summary = (
            "The policy selected BLOCK_IP for high-risk traffic with elevated "
            "CTI or severity. Blocking is a simulated network control, not a live firewall change."
        )
    elif action == "ALERT_ADMIN":
        summary = (
            "The policy selected ALERT_ADMIN for medium-risk or uncertain cases "
            "where investigation is preferred over immediate blocking."
        )
    else:
        summary = (
            "The policy selected NO_ACTION because combined risk and CTI sit in a "
            "safe operating range. Traffic is allowed and the event is logged."
        )

    q_ranking = None
    if q_values:
        names = ["NO_ACTION", "ALERT_ADMIN", "BLOCK_IP", "ISOLATE_HOST"]
        paired = sorted(zip(names, q_values), key=lambda item: item[1], reverse=True)
        q_ranking = [{"action": name, "q_value": round(float(value), 4)} for name, value in paired]

    return {
        "action": action,
        "baseline_rule_action": baseline,
        "agrees_with_rule_baseline": action == baseline,
        "model_version": model_version,
        "caveat": (
            "Explanation is state/action context for analysts. Q-values indicate "
            "relative action preference of the learned policy, not causal proof."
        ),
        "state_context": {
            "attack": attack,
            "severity": round(float(severity or 0), 2),
            "confidence": round(float(confidence or 0), 2),
            "risk_score": round(float(risk_score or 0), 2),
            "risk_level": risk_level,
            "virustotal_score": round(float(virustotal_score or 0), 2),
            "abuseipdb_score": round(float(abuseipdb_score or 0), 2),
            "cti_heat": round(float(cti_heat), 2),
        },
        "summary": summary,
        "q_ranking": q_ranking,
    }
