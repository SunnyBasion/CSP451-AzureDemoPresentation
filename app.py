from flask import Flask, request, jsonify, send_from_directory
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.cosmos import CosmosClient, PartitionKey
from datetime import datetime
import os

app = Flask(__name__)

# -----------------------------
# Azure Language Service Config
# -----------------------------
key = "your-key"
endpoint = "your-endpoint"

client = TextAnalyticsClient(endpoint=endpoint, credential=AzureKeyCredential(key))

# -----------------------------
# Cosmos DB Config
# -----------------------------
cosmos_endpoint = "your-endpoint"       # Replace with your Cosmos DB URI
cosmos_key = "your-key   # Replace with your Cosmos DB PRIMARY KEY
database_name = "SentimentDB"
container_name = "AnalysisResults"

cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
database = cosmos_client.create_database_if_not_exists(id=database_name)
container = database.create_container_if_not_exists(
    id=container_name,
    partition_key=PartitionKey(path="/id"),
)

# -----------------------------
# Serve the Dashboard
# -----------------------------
@app.route("/")
def index():
    return send_from_directory(os.getcwd(), "index.html")

# -----------------------------
# Analyze Text
# -----------------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    text = request.json.get("text", "")
    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Analyze sentiment
    sentiment_result = client.analyze_sentiment([text])[0]

    # Extract key phrases
    key_phrases_result = client.extract_key_phrases([text])[0]

    # Build result JSON
    result_data = {
        "id": str(datetime.utcnow().timestamp()),  # unique ID
        "text": text,
        "sentiment": sentiment_result.sentiment,
        "confidence_scores": {
            "positive": sentiment_result.confidence_scores.positive,
            "neutral": sentiment_result.confidence_scores.neutral,
            "negative": sentiment_result.confidence_scores.negative
        },
        "key_phrases": key_phrases_result.key_phrases,
        "timestamp": datetime.utcnow().isoformat()
    }

    # Save result to Cosmos DB
    container.create_item(body=result_data)

    return jsonify(result_data)

# -----------------------------
# Run the App
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
