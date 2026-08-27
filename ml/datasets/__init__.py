"""Dataset adapters for research experiments (separate from production CICIDS2017)."""

from ml.datasets.unsw_nb15 import (
    UNSW_BENIGN_LABEL,
    load_unsw_nb15_splits,
    prepare_unsw_features,
)

__all__ = [
    "UNSW_BENIGN_LABEL",
    "load_unsw_nb15_splits",
    "prepare_unsw_features",
]
