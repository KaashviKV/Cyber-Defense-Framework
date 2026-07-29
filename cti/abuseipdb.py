import os
from typing import Any

import requests
from dotenv import load_dotenv

from cti.cache import get_cached_cti, set_cached_cti
from cti.http_client import request_with_retry

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(CURRENT_DIR, "..", "backend", ".env")
load_dotenv(ENV_PATH)

API_KEY = os.getenv("ABUSEIPDB_API_KEY", "").strip()
BASE_URL = "https://api.abuseipdb.com/api/v2/check"


def check_abuseip(ip_address: str) -> dict[str, Any]:
    cached = get_cached_cti("abuseipdb", ip_address)
    if cached is not None:
        return cached

    if not API_KEY or API_KEY.startswith("your_"):
        return {
            "error": "missing_api_key",
            "message": "ABUSEIPDB_API_KEY is not configured.",
        }

    headers = {
        "Key": API_KEY,
        "Accept": "application/json",
    }
    params = {
        "ipAddress": ip_address,
        "maxAgeInDays": 90,
    }

    try:
        response = request_with_retry(
            "GET",
            BASE_URL,
            headers=headers,
            params=params,
        )
    except requests.RequestException as exc:
        return {
            "error": "request_failed",
            "message": str(exc),
        }

    if response.status_code == 200:
        data = response.json()["data"]
        result: dict[str, Any] = {
            "ip": data["ipAddress"],
            "abuse_confidence": data["abuseConfidenceScore"],
            "country": data["countryCode"],
            "usage_type": data["usageType"],
            "total_reports": data["totalReports"],
            "is_whitelisted": data["isWhitelisted"],
            "cached": False,
        }
        set_cached_cti("abuseipdb", ip_address, result)
        return result

    return {
        "error": response.status_code,
        "message": response.text,
    }


if __name__ == "__main__":
    ip = input("Enter IP Address: ")
    print("\nAbuseIPDB Result\n")
    print(check_abuseip(ip))
