import os
import requests
from dotenv import load_dotenv

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

ENV_PATH = os.path.join(
    CURRENT_DIR,
    "..",
    "backend",
    ".env"
)

load_dotenv(ENV_PATH)

API_KEY = os.getenv("VIRUSTOTAL_API_KEY")

BASE_URL = "https://www.virustotal.com/api/v3/ip_addresses/"


def check_virustotal(ip_address):
    headers = {
        "x-apikey": API_KEY
    }

    response = requests.get(BASE_URL + ip_address, headers=headers)

    if response.status_code == 200:
        data = response.json()

        stats = data["data"]["attributes"]["last_analysis_stats"]

        return {
            "ip": ip_address,
            "malicious": stats["malicious"],
            "suspicious": stats["suspicious"],
            "harmless": stats["harmless"],
            "undetected": stats["undetected"]
        }

    else:
        return {
            "error": response.status_code,
            "message": response.text
        }


if __name__ == "__main__":

    ip = input("Enter IP Address: ")

    result = check_virustotal(ip)

    print("\nVirusTotal Result\n")
    print(result)