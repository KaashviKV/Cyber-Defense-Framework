import os
from typing import Any

import requests
from dotenv import load_dotenv

from cti.cache import get_cached_cti, set_cached_cti
from cti.http_client import request_with_retry

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(CURRENT_DIR, "..", "backend", ".env")
load_dotenv(ENV_PATH)

API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "").strip()
BASE_URL = "https://www.virustotal.com/api/v3/ip_addresses/"


def check_virustotal(ip_address: str) -> dict[str, Any]:
    cached = get_cached_cti("virustotal", ip_address)
    if cached is not None:
        return cached

    if not API_KEY or API_KEY.startswith("your_"):
        return {
            "error": "missing_api_key",
            "message": "VIRUSTOTAL_API_KEY is not configured.",
        }

    headers = {"x-apikey": API_KEY}

    try:
        response = request_with_retry(
            "GET",
            BASE_URL + ip_address,
            headers=headers,
        )
    except requests.RequestException as exc:
        return {
            "error": "request_failed",
            "message": str(exc),
        }

    if response.status_code == 200:
        data = response.json()
        stats = data["data"]["attributes"]["last_analysis_stats"]
        result: dict[str, Any] = {
            "ip": ip_address,
            "malicious": stats["malicious"],
            "suspicious": stats["suspicious"],
            "harmless": stats["harmless"],
            "undetected": stats["undetected"],
            "cached": False,
        }
        set_cached_cti("virustotal", ip_address, result)
        return result

    return {
        "error": response.status_code,
        "message": response.text,
    }


if __name__ == "__main__":
    ip = input("Enter IP Address: ")
    print("\nVirusTotal Result\n")
    print(check_virustotal(ip))
