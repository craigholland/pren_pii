import json

from flask import Flask, jsonify, request
from services.kafka.kafka_main import get_producer
from services.config import config
# Flask App for REST API
app = Flask(__name__)

# REST API Route Example
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "OK", "service": config.service_name})

@app.route("/publish", methods=["POST"])
def publish_event():
    data = request.json
    producer = get_producer(config)
    producer.send(config.kafka_topic, json.dumps(data).encode("utf-8"))
    return jsonify({"status": "Message Published"})