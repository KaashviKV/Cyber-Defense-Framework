from backend.models.analysis_model import save_analysis

dummy = {

    "ip_address": "8.8.8.8",

    "prediction": {

        "attack": "BENIGN",

        "confidence": 80

    }

}

_id = save_analysis(dummy)

print("Inserted ID :", _id)