"""
RL state encoding for ICDF.

Legacy DQN (v1): [severity, risk]          -> state_size = 2
CTI-aware DQN (v2): [severity, confidence, risk, vt, abuse] -> state_size = 5
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

STATE_SIZE_V1 = 2
STATE_SIZE_V2 = 5
STATE_FEATURE_NAMES_V2 = [
    "severity",
    "confidence",
    "risk_score",
    "virustotal_score",
    "abuseipdb_score",
]


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def encode_state_v1(severity: float, risk_score: float) -> list[float]:
    return [_clamp01(severity / 100.0), _clamp01(risk_score / 100.0)]


def encode_state_v2(
    severity: float,
    risk_score: float,
    confidence: float = 0.0,
    virustotal_score: float = 0.0,
    abuseipdb_score: float = 0.0,
) -> list[float]:
    return [
        _clamp01(severity / 100.0),
        _clamp01(confidence / 100.0),
        _clamp01(risk_score / 100.0),
        _clamp01(virustotal_score / 100.0),
        _clamp01(abuseipdb_score / 100.0),
    ]


def encode_state(
    severity: float,
    risk_score: float,
    confidence: float = 0.0,
    virustotal_score: float = 0.0,
    abuseipdb_score: float = 0.0,
    state_size: int = STATE_SIZE_V2,
) -> list[float]:
    if state_size == STATE_SIZE_V1:
        return encode_state_v1(severity, risk_score)
    return encode_state_v2(
        severity,
        risk_score,
        confidence=confidence,
        virustotal_score=virustotal_score,
        abuseipdb_score=abuseipdb_score,
    )


def encode_from_mapping(state: Mapping[str, Any], state_size: int = STATE_SIZE_V2) -> list[float]:
    return encode_state(
        severity=float(state.get("severity", 0) or 0),
        risk_score=float(state.get("risk_score", 0) or 0),
        confidence=float(state.get("confidence", 0) or 0),
        virustotal_score=float(state.get("virustotal_score", 0) or 0),
        abuseipdb_score=float(state.get("abuseipdb_score", 0) or 0),
        state_size=state_size,
    )


def infer_state_size_from_checkpoint(state_dict: Mapping[str, Any]) -> int:
    """
    Infer DQN input dimension from first Linear weight shape (out, in).
    Falls back to legacy size 2 if shape cannot be read.
    """
    weight = state_dict.get("network.0.weight")
    if weight is None:
        return STATE_SIZE_V1
    try:
        in_features = int(weight.shape[1])
    except Exception:
        return STATE_SIZE_V1
    if in_features in (STATE_SIZE_V1, STATE_SIZE_V2):
        return in_features
    return STATE_SIZE_V1
