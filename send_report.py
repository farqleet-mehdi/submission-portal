"""Build the test report and send it to the local receiver.

The CI pipeline runs this after the tests:
    python -m pytest --junitxml=results.xml   (runs the tests, writes results.xml)
    python send_report.py                     (this file: reads results.xml, sends the report)
"""
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import requests

RESULTS_FILE = "results.xml"
RECEIVER_URL = os.environ.get("RECEIVER_URL", "http://127.0.0.1:5001/report")


def read_tests(path):
    """Return one entry per test: its name, result and failure message (if any)."""
    tests = []
    for case in ET.parse(path).getroot().iter("testcase"):
        problem = case.find("failure")
        if problem is None:
            problem = case.find("error")
        tests.append({
            "name": case.get("name"),
            "result": "failed" if problem is not None else "passed",
            "failure_message": (problem.get("message") or "").strip() if problem is not None else None,
        })
    return tests


def build_report(tests):
    """Combine the test results with the GitHub run details."""
    passed = sum(1 for t in tests if t["result"] == "passed")
    failed = len(tests) - passed
    return {
        # GitHub fills these in automatically while the pipeline runs.
        "repository": os.environ.get("GITHUB_REPOSITORY", "local"),
        "branch": os.environ.get("GITHUB_REF_NAME", "local"),
        "commit_sha": os.environ.get("GITHUB_SHA", "local"),
        "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tests": tests,
        "total": len(tests),
        "passed": passed,
        "failed": failed,
        "overall_status": "passed" if tests and failed == 0 else "failed",
    }


def main():
    if os.path.exists(RESULTS_FILE):
        tests, error = read_tests(RESULTS_FILE), None
    else:
        tests, error = [], f"{RESULTS_FILE} was not created, so the tests did not run."

    report = build_report(tests)
    if error:
        report["error"] = error

    try:
        response = requests.post(RECEIVER_URL, json=report, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Could not send the report to {RECEIVER_URL}: {exc}")
        sys.exit(1)

    print(f"Report sent: {report['overall_status']} "
          f"({report['passed']}/{report['total']} tests passed)")


if __name__ == "__main__":
    main()