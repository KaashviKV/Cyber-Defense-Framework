"""
Response Actions Module

This module performs the defensive action
recommended by the Decision Engine.
"""

import os
from datetime import datetime

from ml.response_engine.simulation_state import record_event


# Log folder (project-root/logs)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FOLDER = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "..", "logs")
)

os.makedirs(LOG_FOLDER, exist_ok=True)


def write_log(filename, message):
    """
    Write message to a log file.
    """

    path = os.path.join(LOG_FOLDER, filename)

    with open(path, "a") as file:
        file.write(
            f"[{datetime.now()}] {message}\n"
        )


# ---------------------------------------------------
# Action 1
# ---------------------------------------------------

def allow_traffic(ip):
    print(f"\nTraffic Allowed : {ip}")

    write_log(
        "predictions.log",
        f"Allowed Traffic -> {ip}"
    )
    return record_event("NO_ACTION", ip)


# ---------------------------------------------------
# Action 2
# ---------------------------------------------------

def monitor_ip(ip):
    print(f"\nMonitoring IP : {ip}")

    write_log(
        "predictions.log",
        f"Monitoring -> {ip}"
    )


# ---------------------------------------------------
# Action 3
# ---------------------------------------------------

def alert_admin(ip, risk_score):
    print(f"\nALERT! High Risk IP : {ip}")
    print(f"Risk Score : {risk_score}")

    write_log(
        "alerts.log",
        f"ALERT -> {ip} | Risk Score : {risk_score}"
    )
    return record_event("ALERT_ADMIN", ip, {"risk_score": risk_score})


# ---------------------------------------------------
# Action 4
# ---------------------------------------------------

def block_ip(ip):
    print(f"\nIP Blocked : {ip}")

    write_log(
        "blocked_ips.log",
        f"Blocked -> {ip}"
    )
    return record_event("BLOCK_IP", ip)

# ---------------------------------------------------
# Action 5
# ---------------------------------------------------

def isolate_host(ip):
    """
    Simulates isolating an infected host
    from the enterprise network.
    """

    print("\n==============================")
    print("HOST ISOLATION")
    print("==============================")

    print(f"Target Host : {ip}")

    print("Disconnecting host from network...")

    print("Firewall Rules Updated")

    print("Switch Port Disabled")

    print("Host Successfully Isolated")

    write_log(
        "isolated_hosts.log",
        f"Host Isolated -> {ip}"
    )
    return record_event("ISOLATE_HOST", ip)