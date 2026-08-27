"""
Persistent simulated SOC state (blocklist, isolation, alerts).

Actions are never applied to a real firewall. State is stored as JSON under logs/.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "..", "logs", "simulated_soc_state.json")
)
MAX_EVENTS = 500


def _empty_state() -> dict[str, Any]:
    return {
        "blocklist": [],
        "isolated_hosts": [],
        "alerts": [],
        "allowed": [],
        "updated_at": None,
    }


def load_state() -> dict[str, Any]:
    if not os.path.exists(STATE_PATH):
        return _empty_state()
    try:
        with open(STATE_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
        for key in ("blocklist", "isolated_hosts", "alerts", "allowed"):
            data.setdefault(key, [])
        return data
    except (OSError, json.JSONDecodeError):
        return _empty_state()


def _write_state(state: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(STATE_PATH, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)


def record_event(action: str, ip_address: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    state = load_state()
    event = {
        "ip": ip_address,
        "action": action,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **(extra or {}),
    }

    bucket = {
        "BLOCK_IP": "blocklist",
        "ISOLATE_HOST": "isolated_hosts",
        "ALERT_ADMIN": "alerts",
        "NO_ACTION": "allowed",
    }.get(action, "allowed")

    entries = state[bucket]
    entries.insert(0, event)
    state[bucket] = entries[:MAX_EVENTS]
    _write_state(state)

    effects = {
        "NO_ACTION": ["Traffic allowed (simulated)", "Event logged"],
        "ALERT_ADMIN": ["Security alert generated (simulated)", "Event logged"],
        "BLOCK_IP": ["IP added to simulated blocklist", "Event logged"],
        "ISOLATE_HOST": ["Host marked isolated (simulated)", "Event logged"],
    }
    return {
        "mode": "simulated",
        "action": action,
        "ip": ip_address,
        "effects": effects.get(action, ["Event logged"]),
        "state_file": STATE_PATH,
    }


def get_simulation_summary() -> dict[str, Any]:
    state = load_state()
    return {
        "status": "success",
        "mode": "simulated",
        "counts": {
            "blocklist": len(state.get("blocklist") or []),
            "isolated_hosts": len(state.get("isolated_hosts") or []),
            "alerts": len(state.get("alerts") or []),
            "allowed": len(state.get("allowed") or []),
        },
        "blocklist": (state.get("blocklist") or [])[:50],
        "isolated_hosts": (state.get("isolated_hosts") or [])[:50],
        "alerts": (state.get("alerts") or [])[:50],
        "updated_at": state.get("updated_at"),
    }
