import math

import pytest

from backend.utils.errors import APIError
from backend.utils.validation import validate_features, validate_ip_address


def test_validate_ip_address_accepts_ipv4():
    assert validate_ip_address("8.8.8.8") == "8.8.8.8"


def test_validate_ip_address_rejects_invalid():
    with pytest.raises(APIError) as exc:
        validate_ip_address("not-an-ip")
    assert exc.value.code == "INVALID_IP_ADDRESS"


def test_validate_features_requires_exact_count():
    with pytest.raises(APIError) as exc:
        validate_features([1.0] * 10)
    assert exc.value.code == "INVALID_FEATURE_COUNT"


def test_validate_features_rejects_nan():
    values = [1.0] * 78
    values[5] = float("nan")
    with pytest.raises(APIError) as exc:
        validate_features(values)
    assert exc.value.code == "INVALID_FEATURE_NAN"
    assert exc.value.details["index"] == 5


def test_validate_features_rejects_infinity():
    values = [1.0] * 78
    values[2] = math.inf
    with pytest.raises(APIError) as exc:
        validate_features(values)
    assert exc.value.code == "INVALID_FEATURE_INFINITY"


def test_validate_features_accepts_valid_vector():
    values = [float(i) for i in range(78)]
    assert len(validate_features(values)) == 78
