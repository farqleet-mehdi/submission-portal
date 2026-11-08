"""Local report receiver.

Start it with:   python receiver.py
It listens on http://127.0.0.1:5001 and saves every test report it receives
to testreport.json (a new report replaces the previous one).
"""
import json
import os

from flask import Flask, jsonify, request

app = Flask(__name__)

# testreport.json is saved in the same folder as this file.
REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testreport.json")


@app.route("/report", methods=["POST"])
def receive_report():
    report = request.get_json(silent=True)
    if not isinstance(report, dict):
        return jsonify({"error": "Send a JSON object."}), 400

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Report saved to {REPORT_FILE} "
          f"(status={report.get('overall_status')}, commit={report.get('commit_sha')})")
    return jsonify({"saved": "testreport.json"}), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)