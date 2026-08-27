# Intelligent Cyber Defense Framework

AI-powered adaptive network security system: Random Forest IDS, Cyber Threat Intelligence (VirusTotal + AbuseIPDB), a documented risk model, Deep Q-Network response selection, simulated incident response, MongoDB persistence, and a React SOC dashboard.

**Research claim the experiments support:** CTI improves threat assessment, fused risk improves prioritization, and RL is evaluated against a rule-based baseline (and Double DQN) rather than presented as an untested add-on.

## Architecture

```
Network Traffic → Preprocessing → ML IDS (+ XAI)
        → CTI (VirusTotal, AbuseIPDB)
        → Risk Engine
        → RL Decision Engine (DQN / Double DQN)
        → Simulated Response (allow / alert / block / isolate)
        → MongoDB + Dashboard
        → Analyst feedback → optional model fine-tuning
```

## Features

- 15-class CICIDS2017 attack classification (Random Forest in production)
- Per-prediction explainability (leave-one-feature-out) plus global feature importance
- VirusTotal and AbuseIPDB enrichment with caching
- Weighted risk score (SAFE → CRITICAL) with report-volume blend and whitelist scaling
- DQN policy compared with a rule-based baseline and Double DQN
- Simulated SOC state (blocklist / isolation / alerts) — no live firewall changes
- Analyst feedback on stored analyses for later RL fine-tuning
- Experiments page that reads saved JSON artifacts for the report/viva

## Technologies

Python 3.10+, scikit-learn, PyTorch, Flask, MongoDB, React, VirusTotal API, AbuseIPDB API.

## Dataset

[CICIDS2017](https://www.unb.ca/cic/datasets/ids-2017.html) flow features (78 numeric inputs). Dataset files under `dataset/` are gitignored; regenerate with the scripts in `ml/`.

## System workflow

1. Client posts an IP and 78 features to `POST /analyze`.
2. Random Forest predicts attack class, severity, and confidence.
3. CTI lookups enrich the IP.
4. Risk engine fuses severity, confidence, VirusTotal, AbuseIPDB, and report volume.
5. DQN selects `NO_ACTION`, `ALERT_ADMIN`, `BLOCK_IP`, or `ISOLATE_HOST`.
6. The action is simulated (logs + JSON SOC state) and stored in MongoDB.

## Installation

```bash
pip install -r requirements.txt
cd frontend && npm install
```

## Configuration

MongoDB: `mongodb://localhost:27017/`

`backend/.env`:

```env
VIRUSTOTAL_API_KEY=your_key
ABUSEIPDB_API_KEY=your_key
```

## Run

API (project root):

```bash
python -m backend.app
```

Dashboard: `cd frontend && npm start`

Swagger UI: [http://localhost:5000/docs](http://localhost:5000/docs)

## API documentation

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check with service status |
| GET | `/model-info` | Random Forest and DQN metadata |
| GET | `/model-performance` | Accuracy, precision, recall, F1, macro-F1, FPR/FNR |
| GET | `/metrics` | Aggregated analysis metrics |
| GET | `/feature-importance` | Global Random Forest importances |
| GET | `/experiments` | Saved research experiment JSON |
| GET | `/simulation` | Simulated blocklist / isolation / alerts |
| POST | `/analyze` | Full ML + CTI + risk + RL pipeline |
| GET | `/history` | List saved analyses (`limit`, `skip`) |
| GET | `/history/<id>` | One analysis |
| POST | `/history/<id>/feedback` | Analyst verdict for the feedback loop |

Versioned aliases exist under `/api/v1/...`. `features` on `/analyze` must be a JSON array of exactly **78** numeric values.

Additional platform routes: `GET /incidents`, `GET /model-health`, `GET /stream/latest`, `POST /history/<id>/feedback` (optional `override_action`).

## Platform additions

Temporal incidents (15-minute IP windows), dynamic risk (event score kept; `dynamic_risk_score` added), CTI freshness/unknown vs clean, optional RF calibration, MITRE mappings with confidence, fail-safe ALERT when CTI is down on non-benign traffic, HITL overrides, live event poll, Docker Compose, and `python -m experiments.run_all --quick`. Production DQN remains 5-dimensional.

```bash
docker compose up --build
python -m experiments.run_all --quick
```

## Machine learning model

Production detector: Random Forest (`ml/saved_models/random_forest_model.pkl`).

Compare baselines (macro-F1 and per-class recall, not accuracy alone):

```bash
python scripts/compare_ml_models.py
python scripts/compare_ml_models.py --synthetic --quick
```

Unseen-class and distribution-shift tests:

```bash
python scripts/evaluate_evolving_threats.py
```

## CTI integration

`cti/virustotal.py` and `cti/abuseipdb.py` with cache and retries. Missing keys degrade gracefully (errors recorded; scores treated as 0).

## Risk engine

```
risk = 0.40 * attack_severity + 0.20 * confidence + 0.20 * VirusTotal + 0.20 * abuse_effective
```

- `abuse_effective` blends AbuseIPDB confidence with log-scaled report counts.
- Whitelisted IPs scale CTI down.
- BENIGN + hot reputation uses a CTI floor so malicious IPs are not scored SAFE.

Levels: SAFE &lt;20, LOW &lt;40, MEDIUM &lt;60, HIGH &lt;80, CRITICAL ≥80.

Weight justification artifact: `python scripts/evaluate_risk_weights.py`

## Reinforcement learning

- **State (v2):** severity, confidence, risk, VirusTotal, AbuseIPDB
- **Actions:** `NO_ACTION`, `ALERT_ADMIN`, `BLOCK_IP`, `ISOLATE_HOST`
- **Train:** `python -m ml.rl.train_dqn`
- **DQN vs Double DQN:** `python -m ml.rl.train_compare_agents` (does not overwrite production unless `--promote-best`)
- **Rule-based vs DQN vs Double DQN + component policies:** `python scripts/evaluate_rl_ablation.py`
- **Pipeline ablation (ML / +CTI / +Risk / +DQN):** `python scripts/evaluate_pipeline_ablation.py`
- **Case studies:** `python scripts/evaluate_case_studies.py`
- **Fine-tune from history:** `python scripts/finetune_dqn_from_mongo.py` (needs enough stored analyses; `--promote` replaces production weights)

Legacy 2-feature checkpoints still load. Dashboard explanations are **state/action context**, not a claim that DQN is intrinsically interpretable.

## Experiments

Results are written under `ml/saved_models/` and shown on the Experiments page:

| Experiment | Script | Artifact |
|------------|--------|----------|
| IDS comparison | `scripts/compare_ml_models.py` | `ml_model_comparison.json` |
| Response strategy | `scripts/evaluate_rl_ablation.py` | `ablation_results.json` |
| Pipeline ablation | `scripts/evaluate_pipeline_ablation.py` | `pipeline_ablation.json` |
| Evolving/unseen threats | `scripts/evaluate_evolving_threats.py` | `evolving_threat_results.json` |
| Risk differentiation | `scripts/evaluate_risk_weights.py` | `risk_engine_evaluation.json` |
| Case studies | `scripts/evaluate_case_studies.py` | `case_study_results.json` |
| DQN vs Double DQN | `python -m ml.rl.train_compare_agents` | `dqn_vs_double_dqn.json` |
| UNSW-NB15 standalone | `scripts/evaluate_unsw_nb15.py` | `unsw_nb15_evaluation.json` |
| UNSW-NB15 Phase 1 analysis | `scripts/analyze_unsw_nb15_phase1.py` | `unsw_nb15_phase1_analysis.json` |
| UNSW-NB15 Phase 2 imbalance | `scripts/analyze_unsw_nb15_phase2.py` | `unsw_nb15_phase2_imbalance.json` |
| UNSW-NB15 Phase 3 feature ablation | `scripts/analyze_unsw_nb15_phase3.py` | `unsw_nb15_phase3_feature_ablation.json` |
| Cross-dataset Phase 4 | `scripts/analyze_cross_dataset_phase4.py` | `cross_dataset_phase4.json` |
| UNSW FPR threshold tuning | `scripts/analyze_unsw_fpr_threshold.py` | `unsw_nb15_fpr_threshold.json` |

Security-oriented IDS metrics: detection rate (recall on attacks), false positive rate (benign flagged as attack), false negative rate, macro-F1.

### UNSW-NB15 Evaluation

UNSW-NB15 is used as an **additional IDS evaluation dataset**, not as a replacement for production CICIDS2017.

- It uses its **own feature representation** (numeric + categorical fields after dropping `id`).
- It is evaluated **separately** from the production 78-feature CICIDS2017 Random Forest.
- The official UNSW train/test split is preserved (no reshuffle).
- Target is multiclass `attack_cat` (Normal = benign). Binary `label` and `attack_cat` are excluded from inputs to prevent leakage.
- Metrics include macro-F1, per-class recall, attack detection rate, FPR, and FNR.
- The UNSW model is saved only as `ml/saved_models/random_forest_unsw_nb15.pkl` and **does not replace** `random_forest_model.pkl`.

```bash
python scripts/evaluate_unsw_nb15.py
python scripts/analyze_unsw_nb15_phase1.py
python scripts/analyze_unsw_nb15_phase2.py
python scripts/analyze_unsw_nb15_phase3.py
python scripts/analyze_cross_dataset_phase4.py
# optional: python -m experiments.run_all --unsw
```

Phase 1 adds confusion-matrix analysis, per-class metrics, a dedicated binary Normal-vs-Attack RF, ROC-AUC / PR-AUC, and feature importance. A key SOC finding is high attack recall with a non-trivial false-positive rate — which motivates CTI enrichment, risk fusion, and DQN prioritization rather than chasing recall alone.

Phase 2 compares **unweighted RF**, **class-weighted RF** (`balanced_subsample`), and **train-only random oversampling**, reporting attack recall and FPR for both multiclass (collapsed) and binary Normal-vs-Attack settings.

Phase 3 ablates to the top **42 / 30 / 20 / 10** original features (ranked by Phase 1 importance) and reports the recall–FPR trade-off.

Phase 4 is the **cross-dataset** experiment (binary only) with a documented 13-feature numeric alignment in `ml/datasets/cross_dataset_alignment.py`: CICIDS2017→UNSW-NB15 and UNSW-NB15→CICIDS2017, plus in-domain controls on the same aligned space. Alignment is approximate (duration unit conversion, `sload+dload`≈Flow Bytes/s); poor transfer is a valid research outcome. This does **not** change the production 78-feature model.

**Classifier FPR tuning (efficient):** `python scripts/analyze_unsw_fpr_threshold.py` sweeps `P(attack)` decision thresholds on the saved UNSW RF. Raising the threshold can reduce **classifier FPR** while keeping high attack recall. This is separate from CTI/risk/DQN (those address operational responses, not RF FPR).

## Project layout

- `ml/` — preprocessing, Random Forest, risk engine, DQN, decision engine
- `cti/` — VirusTotal and AbuseIPDB clients
- `backend/` — Flask API, pipeline, MongoDB
- `frontend/` — React SOC dashboard
- `scripts/` — comparison, ablation, case studies, fine-tune
- `ml/saved_models/` — trained artifacts and experiment JSON

## Limitations

- **Responses are simulated** — BLOCK/ISOLATE update logs and SOC state only; nothing is pushed to a real firewall.
- **CTI is optional** — without VirusTotal/AbuseIPDB keys the pipeline still runs; risk leans on ML severity/confidence. Missing CTI is treated as unknown, not “clean.”
- **Production vs research** — live `/analyze` uses CICIDS2017 (78 features). UNSW-NB15 results are standalone research artifacts and do not replace the production RF.
- **Classifier FPR** on UNSW can be reduced by probability thresholding; that does not claim CTI/DQN change the RF’s mathematical FPR.
- **Cross-dataset transfer** (CICIDS↔UNSW) is weak after documented alignment — reported honestly as a negative result.
- CICIDS2017 is dated and class-imbalanced; high accuracy on a held-out split is not proof of live enterprise robustness.
- The rule-based response baseline encodes the same reward bands as the RL environment, so it is a strong baseline, not a weak straw man.
- CTI APIs can fail or rate-limit; fail-safe may ALERT on non-benign labels when CTI is unavailable.

## Future work

Online RL from analyst feedback, temporal CICIDS/CSE-CIC-IDS2018 splits, optional SHAP for XAI, and optional XGBoost if added to the environment.

## Team

Final-year CSE (Cybersecurity + AI) project — Intelligent Cyber Defense Framework.
