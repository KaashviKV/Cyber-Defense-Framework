from backend.models.analysis_model import get_analysis_history, count_analyses

print("\nAnalysis History\n")
print(f"Total documents: {count_analyses()}\n")

for doc in get_analysis_history(limit=20):
    prediction = doc.get("prediction", {})
    risk = doc.get("risk", {})
    decision = doc.get("decision", {})

    print("-" * 40)
    print("ID       :", doc.get("_id"))
    print("IP       :", doc.get("ip_address"))
    print("Attack   :", prediction.get("attack"))
    print("Risk     :", risk.get("risk_level"), risk.get("risk_score"))
    print("Action   :", decision.get("action"))
    print("Time     :", doc.get("timestamp"))
