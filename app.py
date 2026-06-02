"""Flask API for grade calculation and Prometheus monitoring."""

import os
import time

from flask import Flask, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from calculator import calculate_grade, calculate_stats

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "app_request_count_total",
    "Total request count",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "app_request_latency_seconds",
    "Request latency in seconds",
    ["endpoint"],
)
GRADE_REQUESTS = Counter(
    "grade_calculation_total",
    "Total grade calculations performed",
)


@app.route("/health", methods=["GET"])
def health():
    """Return service health for Docker and Jenkins smoke checks."""
    REQUEST_COUNT.labels("GET", "/health", "200").inc()
    return jsonify({"status": "healthy", "service": "grade-api"}), 200


@app.route("/metrics", methods=["GET"])
def metrics():
    """Expose Prometheus metrics."""
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.route("/grade", methods=["POST"])
def grade():
    """Calculate grade information for a submitted list of marks."""
    start = time.time()
    try:
        data = request.get_json()
        if not data or "marks" not in data:
            REQUEST_COUNT.labels("POST", "/grade", "400").inc()
            return jsonify({"error": "marks field is required"}), 400

        marks = data["marks"]
        if not isinstance(marks, list) or len(marks) == 0:
            REQUEST_COUNT.labels("POST", "/grade", "400").inc()
            return jsonify({"error": "marks must be a non-empty list"}), 400

        results = [calculate_grade(m) for m in marks]
        stats = calculate_stats(marks)

        GRADE_REQUESTS.inc()
        REQUEST_COUNT.labels("POST", "/grade", "200").inc()
        REQUEST_LATENCY.labels("/grade").observe(time.time() - start)

        return jsonify({"results": results, "stats": stats}), 200

    except (ValueError, TypeError) as e:
        REQUEST_COUNT.labels("POST", "/grade", "500").inc()
        return jsonify({"error": str(e)}), 500


@app.route("/grades/batch", methods=["POST"])
def batch_grades():
    """Calculate grade information for multiple students."""
    start = time.time()
    try:
        data = request.get_json()
        if not data or "students" not in data:
            REQUEST_COUNT.labels("POST", "/grades/batch", "400").inc()
            return jsonify({"error": "students field is required"}), 400

        students = data["students"]
        output = []
        for student in students:
            name = student.get("name", "Unknown")
            marks = student.get("marks", [])
            grades = [calculate_grade(m) for m in marks]
            stats = calculate_stats(marks) if marks else {}
            output.append({"name": name, "grades": grades, "stats": stats})

        REQUEST_COUNT.labels("POST", "/grades/batch", "200").inc()
        REQUEST_LATENCY.labels("/grades/batch").observe(time.time() - start)
        return jsonify({"students": output}), 200

    except (ValueError, TypeError) as e:
        REQUEST_COUNT.labels("POST", "/grades/batch", "500").inc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=5000, debug=False)
