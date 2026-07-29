"""Quick sample IP test against running backend."""
import random
import sys

import requests

BASE = "http://localhost:5000"

SAMPLES = [
    ("8.8.8.8", "Google DNS (benign baseline)"),
    ("1.1.1.1", "Cloudflare DNS (benign)"),
    ("45.146.164.110", "Often flagged in threat feeds"),
    ("185.220.101.1", "Tor exit / frequently reported"),
    ("23.129.64.190", "Historical scanner/abuse reports"),
]


def main():
    try:
        health = requests.get(f"{BASE}/health", timeout=5)
        print("Health:", health.status_code, health.json().get("status"))
    except Exception as exc:
        print("Backend not reachable at", BASE, "-", exc)
        sys.exit(1)

    features = [round(random.uniform(0, 100), 4) for _ in range(78)]
    print("\n--- Same random features, different IPs (CTI + risk will differ) ---\n")

    for ip, label in SAMPLES:
        try:
            resp = requests.post(
                f"{BASE}/analyze",
                json={"ip_address": ip, "features": features},
                timeout=120,
            )
            if resp.status_code != 200:
                body = resp.json()
                print(f"{ip} ({label}) -> HTTP {resp.status_code}: {body.get('message')}\n")
                continue

            analysis = resp.json().get("analysis", {})
            pred = analysis.get("prediction", {})
            vt = analysis.get("virustotal", {})
            abuse = analysis.get("abuseipdb", {})
            risk = analysis.get("risk", {})
            decision = analysis.get("decision", {})

            print(f"{ip} ({label})")
            print(f"  RF attack: {pred.get('attack')} | confidence: {pred.get('confidence')}%")
            if "error" not in vt:
                print(
                    f"  VirusTotal: malicious={vt.get('malicious')} "
                    f"suspicious={vt.get('suspicious')} cached={vt.get('cached', False)}"
                )
            else:
                print(f"  VirusTotal: {vt.get('error')} - {str(vt.get('message', ''))[:70]}")

            if "error" not in abuse:
                print(
                    f"  AbuseIPDB: {abuse.get('abuse_confidence')}% | "
                    f"reports={abuse.get('total_reports')} | country={abuse.get('country')}"
                )
            else:
                print(f"  AbuseIPDB: {abuse.get('error')}")

            print(f"  Risk: {risk.get('risk_level')} ({risk.get('risk_score')})")
            print(f"  Action: {decision.get('action')}")
            print(f"  Latency: {analysis.get('performance', {}).get('total_ms')}ms\n")

        except Exception as exc:
            print(f"{ip} -> error: {exc}\n")


if __name__ == "__main__":
    main()
