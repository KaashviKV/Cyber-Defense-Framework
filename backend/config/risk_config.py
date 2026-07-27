"""
Risk Engine Configuration
"""

# -------------------------
# Weight Configuration
# -------------------------

ATTACK_WEIGHT = 0.40
CONFIDENCE_WEIGHT = 0.20
VIRUSTOTAL_WEIGHT = 0.20
ABUSEIPDB_WEIGHT = 0.20

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