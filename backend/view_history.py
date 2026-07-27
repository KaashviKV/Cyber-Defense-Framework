from backend.database.mongo import analysis_collection

print("\nAnalysis History\n")

for doc in analysis_collection.find():

    print(doc)