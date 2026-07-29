# Intelligent Cyber Defense Framework

AI-powered adaptive network security system using Random Forest detection,
Cyber Threat Intelligence (VirusTotal + AbuseIPDB), risk scoring, and a
Deep Q-Network for automated defensive response.

## Architecture

```
Network Features → Random Forest → VirusTotal + AbuseIPDB
       → Risk Engine → DQN Decision Engine → Flask API → MongoDB
```

## Requirements

- Python 3.10+
- MongoDB running locally (`mongodb://localhost:27017/`)
- VirusTotal and AbuseIPDB API keys in `backend/.env`

```env
VIRUSTOTAL_API_KEY=your_key
ABUSEIPDB_API_KEY=your_key
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the API

From the project root:

```bash
python -m backend.app
```

API endpoints:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check with service status |
| GET | `/model-info` | Random Forest and DQN metadata |
| GET | `/api/v1/model-info` | Versioned model metadata |
| GET | `/metrics` | Aggregated analysis metrics |
| GET | `/api/v1/metrics` | Versioned metrics endpoint |
| GET | `/model-performance` | Random Forest accuracy, precision, recall, F1 |
| GET | `/api/v1/model-performance` | Versioned model evaluation metrics |
| POST | `/analyze` | Run full analysis pipeline |
| POST | `/api/v1/analyze` | Versioned analyze endpoint |
| GET | `/history` | List saved analyses (`limit`, `skip`) |
| GET | `/api/v1/history` | Versioned history list |
| GET | `/history/<id>` | Fetch one analysis by id |
| GET | `/api/v1/history/<id>` | Versioned analysis detail |

Logs are written to `logs/backend.log` and `logs/error.log`.

### Example `POST /analyze`

```json
{
  "ip_address": "8.8.8.8",
  "features": []
}
```

`features` must be a JSON array of exactly **78** numeric CICIDS2017 feature values.

## Project layout

- `ml/` — preprocessing, Random Forest, risk engine, DQN, decision engine
- `cti/` — VirusTotal and AbuseIPDB clients
- `backend/` — Flask API, pipeline, MongoDB integration
- `frontend/` — React dashboard (in progress)
- `ml/saved_models/` — trained RF and DQN artifacts

## Notes

- Defensive actions (allow / alert / block / isolate) are simulated via log files under `logs/`.
- Dataset files under `dataset/` are gitignored; regenerate with the scripts in `ml/`.
