"""
Application configuration.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Project paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
LOG_DIR = PROJECT_ROOT / "logs"
ML_DIR = PROJECT_ROOT / "ml"
SAVED_MODELS_DIR = ML_DIR / "saved_models"

RF_MODEL_PATH = SAVED_MODELS_DIR / "random_forest_model.pkl"
DQN_MODEL_PATH = SAVED_MODELS_DIR / "dqn_model.pth"

FEATURE_COUNT = 78
ATTACK_CLASS_COUNT = 15
RL_ACTION_COUNT = 4
API_VERSION = "v1"
SCHEMA_VERSION = "1.0"
DATASET_NAME = "CICIDS2017"
APP_NAME = "Intelligent Cyber Defense Framework"

# Load environment from backend/.env
load_dotenv(BACKEND_DIR / ".env")

# External services
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "intelligent_cyber_defense")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "analysis_history")

VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "").strip()
ABUSEIPDB_API_KEY = os.getenv("ABUSEIPDB_API_KEY", "").strip()
VIRUSTOTAL_BASE_URL = "https://www.virustotal.com/api/v3/ip_addresses/"
ABUSEIPDB_BASE_URL = "https://api.abuseipdb.com/api/v2/check"

# CTI behaviour
CTI_CACHE_TTL_SECONDS = int(os.getenv("CTI_CACHE_TTL_SECONDS", "900"))
CTI_RETRY_ATTEMPTS = int(os.getenv("CTI_RETRY_ATTEMPTS", "2"))
CTI_REQUEST_TIMEOUT = int(os.getenv("CTI_REQUEST_TIMEOUT", "15"))

# Rate limiting
RATE_LIMIT_ANALYZE = os.getenv("RATE_LIMIT_ANALYZE", "10 per minute")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
BACKEND_LOG_FILE = LOG_DIR / "backend.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"
