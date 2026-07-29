"""
MongoDB Connection
"""

from typing import Literal

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from backend.config.config import MONGO_COLLECTION, MONGO_DB_NAME, MONGO_URI


client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

db = client[MONGO_DB_NAME]

analysis_collection = db[MONGO_COLLECTION]


def get_mongo_status() -> Literal["connected", "disconnected"]:
    """Ping MongoDB and return connection status."""
    try:
        client.admin.command("ping")
        return "connected"
    except PyMongoError:
        return "disconnected"
