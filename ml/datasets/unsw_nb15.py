"""
UNSW-NB15 dataset adapter for standalone IDS experiments.

This module is intentionally separate from the production CICIDS2017
78-feature Random Forest pipeline. Do not feed these features into /analyze.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from ml.datasets.common import (
    class_distribution,
    drop_identifier_columns,
    project_root,
    replace_non_finite,
)

# Official multiclass target for this experiment.
TARGET_COLUMN = "attack_cat"
UNSW_BENIGN_LABEL = "Normal"

# Curated train/test CSVs include these categorical fields.
KNOWN_CATEGORICAL = ("proto", "service", "state")


@dataclass(frozen=True)
class UnswSplits:
    x_train: pd.DataFrame
    x_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series
    numeric_features: list[str]
    categorical_features: list[str]
    train_class_counts: dict[str, int]
    test_class_counts: dict[str, int]
    dataset_dir: Path


def resolve_unsw_dir(root: Path | None = None) -> Path:
    """Locate UNSW-NB15 directory (supports a common mistyped folder name)."""
    base = root or project_root()
    candidates = [
        base / "dataset" / "UNSW-NB15",
        base / "dataset" / "UNSW _NB15",
        base / "dataset" / "UNSW_NB15",
    ]
    for path in candidates:
        if path.is_dir():
            return path
    raise FileNotFoundError(
        "UNSW-NB15 dataset directory not found under dataset/. "
        "Expected dataset/UNSW-NB15/ with training and testing CSVs."
    )


def _resolve_csv(dataset_dir: Path, names: tuple[str, ...]) -> Path:
    for name in names:
        path = dataset_dir / name
        if path.is_file():
            return path
    raise FileNotFoundError(
        f"None of {names} found in {dataset_dir}. "
        "Place the official UNSW-NB15 train/test CSVs there."
    )


def load_feature_catalog(dataset_dir: Path | None = None) -> pd.DataFrame | None:
    """Load UNSW feature descriptions when available (optional metadata)."""
    directory = dataset_dir or resolve_unsw_dir()
    for name in ("UNSW-NB15_features.csv", "NUSW-NB15_features.csv"):
        path = directory / name
        if path.is_file():
            frame = pd.read_csv(path, encoding="latin-1")
            frame.columns = [str(c).strip() for c in frame.columns]
            return frame
    return None


def _strip_target_leakage(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Separate attack_cat labels and drop label/attack_cat from features.

    Critical: binary `label` and multiclass `attack_cat` must never be used
    as model inputs — that would leak the prediction target.
    """
    if TARGET_COLUMN not in df.columns:
        raise KeyError(
            f"Required target column '{TARGET_COLUMN}' missing. "
            f"Columns present: {list(df.columns)}"
        )

    y = df[TARGET_COLUMN].astype(str).str.strip()
    # Normalize benign spelling only; preserve original attack category names.
    y = y.replace({"normal": UNSW_BENIGN_LABEL, "NORMAL": UNSW_BENIGN_LABEL})

    drop = [c for c in df.columns if str(c).strip().lower() in {"label", "attack_cat"}]
    features = df.drop(columns=drop)
    features = drop_identifier_columns(features)
    return features, y


def _split_feature_types(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    categorical: list[str] = []
    for col in df.columns:
        if col in KNOWN_CATEGORICAL:
            categorical.append(col)
            continue
        dtype = df[col].dtype
        if pd.api.types.is_object_dtype(dtype) or pd.api.types.is_string_dtype(dtype):
            categorical.append(col)
        elif str(dtype) == "category":
            categorical.append(col)

    numeric = [c for c in df.columns if c not in categorical]
    return numeric, categorical


def load_unsw_nb15_splits(root: Path | None = None) -> UnswSplits:
    """
    Load the official UNSW-NB15 train/test CSVs without reshuffling.

    Uses attack_cat as the multiclass target. Does not map labels onto
    the CICIDS2017 taxonomy.
    """
    dataset_dir = resolve_unsw_dir(root)
    train_path = _resolve_csv(
        dataset_dir,
        ("UNSW_NB15_training-set.csv", "UNSW-NB15_training-set.csv"),
    )
    test_path = _resolve_csv(
        dataset_dir,
        ("UNSW_NB15_testing-set.csv", "UNSW-NB15_testing-set.csv"),
    )

    train_df = pd.read_csv(train_path, low_memory=False)
    test_df = pd.read_csv(test_path, low_memory=False)

    x_train, y_train = _strip_target_leakage(train_df)
    x_test, y_test = _strip_target_leakage(test_df)

    # Align columns (test must match train feature schema).
    missing = [c for c in x_train.columns if c not in x_test.columns]
    extra = [c for c in x_test.columns if c not in x_train.columns]
    if missing or extra:
        raise ValueError(
            f"Train/test feature mismatch. Missing in test={missing}, extra in test={extra}"
        )
    x_test = x_test[x_train.columns]

    numeric, categorical = _split_feature_types(x_train)
    x_train = replace_non_finite(x_train, numeric)
    x_test = replace_non_finite(x_test, numeric)

    # Ensure categoricals are strings for the imputer/encoder.
    for col in categorical:
        x_train[col] = x_train[col].astype(str)
        x_test[col] = x_test[col].astype(str)

    return UnswSplits(
        x_train=x_train,
        x_test=x_test,
        y_train=y_train,
        y_test=y_test,
        numeric_features=numeric,
        categorical_features=categorical,
        train_class_counts=class_distribution(y_train),
        test_class_counts=class_distribution(y_test),
        dataset_dir=dataset_dir,
    )


def build_preprocess_pipeline(
    numeric_features: list[str],
    categorical_features: list[str],
) -> ColumnTransformer:
    """Median/most-frequent imputation + OneHot for categoricals."""
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_features),
            ("cat", categorical_pipeline, categorical_features),
        ],
        remainder="drop",
    )


def prepare_unsw_features(
    splits: UnswSplits | None = None,
) -> tuple[UnswSplits, ColumnTransformer]:
    """Convenience: load splits and return a fitted-ready preprocessor."""
    data = splits or load_unsw_nb15_splits()
    preprocessor = build_preprocess_pipeline(
        data.numeric_features,
        data.categorical_features,
    )
    return data, preprocessor


def describe_splits(splits: UnswSplits) -> dict[str, Any]:
    return {
        "dataset_dir": str(splits.dataset_dir),
        "train_rows": int(len(splits.y_train)),
        "test_rows": int(len(splits.y_test)),
        "feature_count": int(splits.x_train.shape[1]),
        "numeric_feature_count": len(splits.numeric_features),
        "categorical_feature_count": len(splits.categorical_features),
        "numeric_features": list(splits.numeric_features),
        "categorical_features": list(splits.categorical_features),
        "train_class_distribution": splits.train_class_counts,
        "test_class_distribution": splits.test_class_counts,
        "benign_label": UNSW_BENIGN_LABEL,
        "target": TARGET_COLUMN,
        "note": (
            "Standalone UNSW-NB15 evaluation. Not cross-dataset generalization. "
            "Binary label and attack_cat are excluded from features."
        ),
    }
