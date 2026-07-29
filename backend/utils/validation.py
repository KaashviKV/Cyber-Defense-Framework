"""
Input validation helpers for the analyze endpoint.
"""

import ipaddress
import math
from typing import Any

from backend.config.config import FEATURE_COUNT
from backend.utils.errors import APIError


def validate_ip_address(ip_address: Any) -> str:
    if ip_address is None:
        raise APIError(
            message="ip_address is required.",
            code="MISSING_IP_ADDRESS",
            status_code=400,
        )

    if not isinstance(ip_address, str):
        raise APIError(
            message="ip_address must be a string.",
            code="INVALID_IP_ADDRESS",
            status_code=400,
        )

    ip_value = ip_address.strip()
    if not ip_value:
        raise APIError(
            message="ip_address cannot be empty.",
            code="INVALID_IP_ADDRESS",
            status_code=400,
        )

    try:
        ipaddress.ip_address(ip_value)
    except ValueError as exc:
        raise APIError(
            message=f"Invalid IP address format: {ip_value}",
            code="INVALID_IP_ADDRESS",
            status_code=400,
        ) from exc

    return ip_value


def validate_features(features: Any) -> list[float]:
    if features is None:
        raise APIError(
            message="features are required.",
            code="MISSING_FEATURES",
            status_code=400,
        )

    if not isinstance(features, list):
        raise APIError(
            message="features must be a JSON array of numbers.",
            code="INVALID_FEATURE_VECTOR",
            status_code=400,
        )

    if len(features) != FEATURE_COUNT:
        raise APIError(
            message=f"Exactly {FEATURE_COUNT} feature values are required.",
            code="INVALID_FEATURE_COUNT",
            status_code=400,
            details={"received": len(features), "expected": FEATURE_COUNT},
        )

    validated: list[float] = []
    for index, value in enumerate(features):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise APIError(
                message=f"Invalid feature at index {index}. Expected float.",
                code="INVALID_FEATURE_TYPE",
                status_code=400,
                details={"index": index, "value": value},
            )

        number = float(value)
        if math.isnan(number):
            raise APIError(
                message=f"Invalid feature at index {index}. NaN is not allowed.",
                code="INVALID_FEATURE_NAN",
                status_code=400,
                details={"index": index},
            )

        if math.isinf(number):
            raise APIError(
                message=f"Invalid feature at index {index}. Infinity is not allowed.",
                code="INVALID_FEATURE_INFINITY",
                status_code=400,
                details={"index": index},
            )

        validated.append(number)

    return validated
