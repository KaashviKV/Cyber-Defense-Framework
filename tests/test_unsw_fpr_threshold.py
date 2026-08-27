"""Unit tests for UNSW FPR threshold helpers (no full dataset required)."""

from __future__ import annotations

import numpy as np

from scripts.analyze_unsw_fpr_threshold import binary_rates, choose_recommended, evaluate_threshold


def test_binary_rates_perfect():
    y = np.array([0, 0, 1, 1])
    p = np.array([0, 0, 1, 1])
    m = binary_rates(y, p)
    assert m["false_positive_rate"] == 0.0
    assert m["attack_recall"] == 1.0
    assert m["false_negative_rate"] == 0.0


def test_binary_rates_all_benign_pred():
    y = np.array([0, 0, 1, 1])
    p = np.array([0, 0, 0, 0])
    m = binary_rates(y, p)
    assert m["false_positive_rate"] == 0.0
    assert m["attack_recall"] == 0.0
    assert m["false_negative_rate"] == 1.0


def test_evaluate_threshold():
    y = np.array([0, 0, 1, 1])
    scores = np.array([0.1, 0.6, 0.7, 0.9])
    low = evaluate_threshold(y, scores, 0.5)
    high = evaluate_threshold(y, scores, 0.8)
    assert low["false_positive_rate"] == 0.5  # one of two benign above 0.5
    assert high["false_positive_rate"] == 0.0
    assert high["attack_recall"] == 0.5


def test_choose_recommended_respects_min_recall():
    rows = [
        {"threshold": 0.5, "attack_recall": 0.99, "false_positive_rate": 0.30, "false_negative_rate": 0.01, "f1_attack": 0.8, "precision_attack": 0.7},
        {"threshold": 0.7, "attack_recall": 0.96, "false_positive_rate": 0.12, "false_negative_rate": 0.04, "f1_attack": 0.85, "precision_attack": 0.8},
        {"threshold": 0.9, "attack_recall": 0.80, "false_positive_rate": 0.02, "false_negative_rate": 0.20, "f1_attack": 0.7, "precision_attack": 0.9},
    ]
    rec = choose_recommended(rows, baseline_fpr=0.30, min_recall=0.95)
    assert rec["threshold"] == 0.7
    assert rec["fpr_reduction_vs_baseline"] == round((0.30 - 0.12) / 0.30, 4)
