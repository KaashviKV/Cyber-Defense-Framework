"""
Risk Engine Configuration

Primary weights (sum = 1.0) were chosen so that:
- attack class severity remains the largest term (prioritize known high-impact attacks)
- CTI (VirusTotal + AbuseIPDB) jointly match severity, so reputation can override a weak ML label
- model confidence is a stabilizer, not the dominant signal (CICIDS2017 confidence can be overconfident)

Reports and whitelist are modifiers, not extra weights, so historical 4-term scores stay
stable when those fields are missing (backward compatible).
"""

# -------------------------
# Weight Configuration
# -------------------------

ATTACK_WEIGHT = 0.40
CONFIDENCE_WEIGHT = 0.20
VIRUSTOTAL_WEIGHT = 0.20
ABUSEIPDB_WEIGHT = 0.20

# Report volume is folded into the AbuseIPDB channel (does not change the 4-weight sum).
REPORTS_BLEND = 0.30
WHITELIST_CTI_SCALE = 0.35

# -------------------------
# Attack Severity Scores
# -------------------------

ATTACK_SEVERITY = {

    "BENIGN": 0,

    "Bot": 55,

    "PortScan": 60,

    "FTP-Patator": 65,

    "SSH-Patator": 70,

    "Web Attack – Brute Force": 75,

    "Web Attack – Sql Injection": 95,

    "Web Attack – XSS": 85,

    "DoS Hulk": 85,

    "DoS GoldenEye": 82,

    "DoS Slowhttptest": 80,

    "DoS slowloris": 80,

    "DDoS": 95,

    "Heartbleed": 100,

    "Infiltration": 98

}

# -------------------------
# Risk Levels
# -------------------------

SAFE_THRESHOLD = 20
LOW_THRESHOLD = 40
MEDIUM_THRESHOLD = 60
HIGH_THRESHOLD = 80