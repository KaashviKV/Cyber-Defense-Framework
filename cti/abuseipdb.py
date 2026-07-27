import requests
import os
from dotenv import load_dotenv

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

ENV_PATH = os.path.join(
    CURRENT_DIR,
    "..",
    "backend",
    ".env"
)

load_dotenv(ENV_PATH)

API_KEY = os.getenv("ABUSEIPDB_API_KEY")

BASE_URL = "https://api.abuseipdb.com/api/v2/check"


def check_abuseip(ip_address):

    headers = {
        "Key": API_KEY,
        "Accept": "application/json"
    }

    params = {
        "ipAddress": ip_address,
        "maxAgeInDays": 90
    }

    response = requests.get(
        BASE_URL,
        headers=headers,
        params=params
    )

    if response.status_code == 200:

        data = response.json()["data"]

        return {
            "ip": data["ipAddress"],
            "abuse_confidence": data["abuseConfidenceScore"],
            "country": data["countryCode"],
            "usage_type": data["usageType"],
            "total_reports": data["totalReports"],
            "is_whitelisted": data["isWhitelisted"]
        }

    else:
        return {
            "error": response.status_code,
            "message": response.text
        }


if __name__ == "__main__":

    ip = input("Enter IP Address: ")

    result = check_abuseip(ip)

    print("\nAbuseIPDB Result\n")

    print(result)