from datetime import datetime

from backend.database.mongo import analysis_collection


def save_analysis(report):

    report["timestamp"] = datetime.utcnow()

    result = analysis_collection.insert_one(report)

    return str(result.inserted_id)