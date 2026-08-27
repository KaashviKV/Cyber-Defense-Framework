"""
Documented feature alignment for CICIDS2017 <-> UNSW-NB15 cross-dataset experiments.

IMPORTANT
---------
This is a *research* alignment layer only. It does NOT feed the production
78-feature /analyze pipeline and does NOT claim the two datasets share an
identical measurement process.

Design choices (explicit):
- Binary labels only: Normal/BENIGN vs Attack.
- Use a small set of semantically overlapping *numeric* flow features.
- Drop UNSW categoricals (proto/service/state) because the production CICIDS
  processed vectors are numeric-only (78 dims).
- Convert CICIDS Flow Duration from microseconds to seconds to match UNSW `dur`.
- Approximate UNSW byte rate as sload + dload vs CICIDS Flow Bytes/s.
- Fit scalers on the *source* training domain only (no target leakage).

This alignment enables a transfer experiment; poor transfer is a valid result.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

# Exact column order from dataset/CICIDS2017/processed/balanced_dataset.csv
# (Label dropped) — matches train_test_data.pkl (78 dims). Do NOT use
# ml.feature_names.FEATURE_NAMES here; that list is longer/mismatched.
CICIDS_PROCESSED_FEATURE_NAMES: tuple[str, ...] = (
    "Destination Port",
    "Flow Duration",
    "Total Fwd Packets",
    "Total Backward Packets",
    "Total Length of Fwd Packets",
    "Total Length of Bwd Packets",
    "Fwd Packet Length Max",
    "Fwd Packet Length Min",
    "Fwd Packet Length Mean",
    "Fwd Packet Length Std",
    "Bwd Packet Length Max",
    "Bwd Packet Length Min",
    "Bwd Packet Length Mean",
    "Bwd Packet Length Std",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Flow IAT Mean",
    "Flow IAT Std",
    "Flow IAT Max",
    "Flow IAT Min",
    "Fwd IAT Total",
    "Fwd IAT Mean",
    "Fwd IAT Std",
    "Fwd IAT Max",
    "Fwd IAT Min",
    "Bwd IAT Total",
    "Bwd IAT Mean",
    "Bwd IAT Std",
    "Bwd IAT Max",
    "Bwd IAT Min",
    "Fwd PSH Flags",
    "Bwd PSH Flags",
    "Fwd URG Flags",
    "Bwd URG Flags",
    "Fwd Header Length",
    "Bwd Header Length",
    "Fwd Packets/s",
    "Bwd Packets/s",
    "Min Packet Length",
    "Max Packet Length",
    "Packet Length Mean",
    "Packet Length Std",
    "Packet Length Variance",
    "FIN Flag Count",
    "SYN Flag Count",
    "RST Flag Count",
    "PSH Flag Count",
    "ACK Flag Count",
    "URG Flag Count",
    "CWE Flag Count",
    "ECE Flag Count",
    "Down/Up Ratio",
    "Average Packet Size",
    "Avg Fwd Segment Size",
    "Avg Bwd Segment Size",
    "Fwd Header Length.1",
    "Fwd Avg Bytes/Bulk",
    "Fwd Avg Packets/Bulk",
    "Fwd Avg Bulk Rate",
    "Bwd Avg Bytes/Bulk",
    "Bwd Avg Packets/Bulk",
    "Bwd Avg Bulk Rate",
    "Subflow Fwd Packets",
    "Subflow Fwd Bytes",
    "Subflow Bwd Packets",
    "Subflow Bwd Bytes",
    "Init_Win_bytes_forward",
    "Init_Win_bytes_backward",
    "act_data_pkt_fwd",
    "min_seg_size_forward",
    "Active Mean",
    "Active Std",
    "Active Max",
    "Active Min",
    "Idle Mean",
    "Idle Std",
    "Idle Max",
    "Idle Min",
)

# CICIDS processed label encoder: index 0 == BENIGN
CICIDS_BENIGN_INDEX = 0
UNSW_BENIGN_LABEL = "Normal"


@dataclass(frozen=True)
class AlignedFeature:
    shared_name: str
    cicids_name: str
    unsw_name: str | None
    """If None, UNSW value is derived (see unsw_derive)."""
    notes: str
    cicids_transform: Callable[[np.ndarray], np.ndarray] | None = None
    unsw_derive: Callable[[pd.DataFrame], np.ndarray] | None = None


def _identity(x: np.ndarray) -> np.ndarray:
    return x.astype(float)


def _cicids_duration_to_seconds(x: np.ndarray) -> np.ndarray:
    # CICIDS2017 Flow Duration is commonly recorded in microseconds.
    return x.astype(float) / 1_000_000.0


def _unsw_flow_bytes_per_s(df: pd.DataFrame) -> np.ndarray:
    # Approximate total byte rate; not identical to CICIDS Flow Bytes/s.
    return df["sload"].to_numpy(dtype=float) + df["dload"].to_numpy(dtype=float)


ALIGNED_FEATURES: tuple[AlignedFeature, ...] = (
    AlignedFeature(
        "duration_sec",
        "Flow Duration",
        "dur",
        "CICIDS Flow Duration (us) / 1e6 -> seconds; UNSW dur already seconds.",
        cicids_transform=_cicids_duration_to_seconds,
    ),
    AlignedFeature(
        "fwd_packets",
        "Total Fwd Packets",
        "spkts",
        "Forward/source packet counts.",
    ),
    AlignedFeature(
        "bwd_packets",
        "Total Backward Packets",
        "dpkts",
        "Backward/destination packet counts.",
    ),
    AlignedFeature(
        "fwd_bytes",
        "Total Length of Fwd Packets",
        "sbytes",
        "Forward/source bytes.",
    ),
    AlignedFeature(
        "bwd_bytes",
        "Total Length of Bwd Packets",
        "dbytes",
        "Backward/destination bytes.",
    ),
    AlignedFeature(
        "fwd_pkt_len_mean",
        "Fwd Packet Length Mean",
        "smean",
        "Mean forward/source packet size.",
    ),
    AlignedFeature(
        "bwd_pkt_len_mean",
        "Bwd Packet Length Mean",
        "dmean",
        "Mean backward/destination packet size.",
    ),
    AlignedFeature(
        "flow_bytes_per_s",
        "Flow Bytes/s",
        None,
        "UNSW approximated as sload + dload (not identical instrumentation).",
        unsw_derive=_unsw_flow_bytes_per_s,
    ),
    AlignedFeature(
        "flow_packets_per_s",
        "Flow Packets/s",
        "rate",
        "Packet rate; definitions may differ slightly across collectors.",
    ),
    AlignedFeature(
        "fwd_iat_mean",
        "Fwd IAT Mean",
        "sinpkt",
        "Mean forward inter-arrival / source inter-packet time.",
    ),
    AlignedFeature(
        "bwd_iat_mean",
        "Bwd IAT Mean",
        "dinpkt",
        "Mean backward inter-arrival / destination inter-packet time.",
    ),
    AlignedFeature(
        "init_win_fwd",
        "Init_Win_bytes_forward",
        "swin",
        "Initial / source TCP window (related but not guaranteed identical).",
    ),
    AlignedFeature(
        "init_win_bwd",
        "Init_Win_bytes_backward",
        "dwin",
        "Initial / destination TCP window (related but not guaranteed identical).",
    ),
)


def shared_feature_names() -> list[str]:
    return [f.shared_name for f in ALIGNED_FEATURES]


def alignment_documentation() -> list[dict]:
    rows = []
    for feat in ALIGNED_FEATURES:
        rows.append(
            {
                "shared_name": feat.shared_name,
                "cicids_source": feat.cicids_name,
                "unsw_source": feat.unsw_name
                if feat.unsw_name is not None
                else "derived: sload + dload",
                "notes": feat.notes,
            }
        )
    return rows


def _cicids_index(name: str) -> int:
    try:
        return CICIDS_PROCESSED_FEATURE_NAMES.index(name)
    except ValueError as exc:
        raise KeyError(
            f"CICIDS feature '{name}' not in CICIDS_PROCESSED_FEATURE_NAMES"
        ) from exc


def cicids_matrix_to_aligned(x: np.ndarray) -> np.ndarray:
    """Map CICIDS 78-dim numeric matrix -> aligned shared feature matrix."""
    x = np.asarray(x, dtype=float)
    expected = len(CICIDS_PROCESSED_FEATURE_NAMES)
    if x.ndim != 2 or x.shape[1] != expected:
        raise ValueError(
            f"Expected CICIDS matrix with {expected} columns, got {x.shape}"
        )
    cols = []
    for feat in ALIGNED_FEATURES:
        idx = _cicids_index(feat.cicids_name)
        values = x[:, idx]
        transform = feat.cicids_transform or _identity
        cols.append(transform(values))
    mat = np.column_stack(cols)
    mat[~np.isfinite(mat)] = np.nan
    return mat


def unsw_frame_to_aligned(df: pd.DataFrame) -> np.ndarray:
    """Map UNSW feature frame -> aligned shared feature matrix."""
    cols = []
    for feat in ALIGNED_FEATURES:
        if feat.unsw_derive is not None:
            values = feat.unsw_derive(df)
        elif feat.unsw_name is not None:
            if feat.unsw_name not in df.columns:
                raise KeyError(f"UNSW column missing: {feat.unsw_name}")
            values = df[feat.unsw_name].to_numpy(dtype=float)
        else:
            raise ValueError(f"Feature {feat.shared_name} has no UNSW source")
        cols.append(values.astype(float))
    mat = np.column_stack(cols)
    mat[~np.isfinite(mat)] = np.nan
    return mat


def cicids_labels_to_binary(y) -> np.ndarray:
    """0 = BENIGN, 1 = attack (CICIDS encoded labels; 0 is BENIGN)."""
    y = np.asarray(y)
    return (y != CICIDS_BENIGN_INDEX).astype(int)


def unsw_labels_to_binary(y) -> np.ndarray:
    """0 = Normal, 1 = attack."""
    y = np.asarray(y).astype(str)
    return (y != UNSW_BENIGN_LABEL).astype(int)
