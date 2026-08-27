"""Defensible CICIDS2017 → MITRE ATT&CK mappings (static, with confidence)."""

from __future__ import annotations

from typing import Any

# Only map where the CICIDS class clearly aligns with a public ATT&CK technique.
_MAP = {
    "BENIGN": {
        "technique_id": None,
        "technique": None,
        "tactic": None,
        "kill_chain": None,
        "confidence": "n/a",
    },
    "PortScan": {
        "technique_id": "T1046",
        "technique": "Network Service Discovery",
        "tactic": "Discovery",
        "kill_chain": "SCANNING",
        "confidence": "HIGH",
    },
    "FTP-Patator": {
        "technique_id": "T1110",
        "technique": "Brute Force",
        "tactic": "Credential Access",
        "kill_chain": "EXPLOITATION",
        "confidence": "HIGH",
    },
    "SSH-Patator": {
        "technique_id": "T1110",
        "technique": "Brute Force",
        "tactic": "Credential Access",
        "kill_chain": "EXPLOITATION",
        "confidence": "HIGH",
    },
    "Web Attack – Brute Force": {
        "technique_id": "T1110",
        "technique": "Brute Force",
        "tactic": "Credential Access",
        "kill_chain": "EXPLOITATION",
        "confidence": "MEDIUM",
    },
    "Web Attack – Sql Injection": {
        "technique_id": "T1190",
        "technique": "Exploit Public-Facing Application",
        "tactic": "Initial Access",
        "kill_chain": "EXPLOITATION",
        "confidence": "MEDIUM",
    },
    "Web Attack – XSS": {
        "technique_id": "T1059",
        "technique": "Command and Scripting Interpreter",
        "tactic": "Execution",
        "kill_chain": "EXPLOITATION",
        "confidence": "LOW",
    },
    "DoS Hulk": {
        "technique_id": "T1498",
        "technique": "Network Denial of Service",
        "tactic": "Impact",
        "kill_chain": "IMPACT",
        "confidence": "HIGH",
    },
    "DoS GoldenEye": {
        "technique_id": "T1499",
        "technique": "Endpoint Denial of Service",
        "tactic": "Impact",
        "kill_chain": "IMPACT",
        "confidence": "HIGH",
    },
    "DoS Slowhttptest": {
        "technique_id": "T1499",
        "technique": "Endpoint Denial of Service",
        "tactic": "Impact",
        "kill_chain": "IMPACT",
        "confidence": "HIGH",
    },
    "DoS slowloris": {
        "technique_id": "T1499",
        "technique": "Endpoint Denial of Service",
        "tactic": "Impact",
        "kill_chain": "IMPACT",
        "confidence": "HIGH",
    },
    "DDoS": {
        "technique_id": "T1498",
        "technique": "Network Denial of Service",
        "tactic": "Impact",
        "kill_chain": "IMPACT",
        "confidence": "HIGH",
    },
    "Bot": {
        "technique_id": "T1071",
        "technique": "Application Layer Protocol",
        "tactic": "Command and Control",
        "kill_chain": "COMMAND_AND_CONTROL",
        "confidence": "MEDIUM",
    },
    "Infiltration": {
        "technique_id": "T1190",
        "technique": "Exploit Public-Facing Application",
        "tactic": "Initial Access",
        "kill_chain": "EXPLOITATION",
        "confidence": "LOW",
    },
    "Heartbleed": {
        "technique_id": "T1190",
        "technique": "Exploit Public-Facing Application",
        "tactic": "Initial Access",
        "kill_chain": "EXPLOITATION",
        "confidence": "MEDIUM",
    },
}

KILL_CHAIN_ORDER = ["RECON", "SCANNING", "EXPLOITATION", "COMMAND_AND_CONTROL", "IMPACT"]


def map_attack(attack_name: str) -> dict[str, Any]:
    entry = _MAP.get(attack_name) or {
        "technique_id": None,
        "technique": None,
        "tactic": None,
        "kill_chain": None,
        "confidence": "LOW",
        "note": "No defensible mapping; left unmapped.",
    }
    return {"attack": attack_name, **entry}
