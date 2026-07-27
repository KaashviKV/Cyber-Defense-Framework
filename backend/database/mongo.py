"""
MongoDB Connection
"""

from pymongo import MongoClient


MONGO_URI = "mongodb://localhost:27017/"


client = MongoClient(MONGO_URI)


db = client["intelligent_cyber_defense"]


analysis_collection = db["analysis_history"]


print("MongoDB Connected Successfully!")