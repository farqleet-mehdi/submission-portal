"""Email the test report.

The CI pipeline runs this after the tests, using the same results.xml as
send_report.py. Settings come from environment variables, which the workflow
fills in from GitHub Secrets:

    SMTP_USER      the sender's email address (Gmail)
    SMTP_PASSWORD  the sender's app password
    EMAIL_TO       who receives the report
    SMTP_HOST      optional, default smtp.gmail.com
    SMTP_PORT      optional, default 587
"""
import json
import os
import smtplib
import sys
from email.message import EmailMessage

from send_report import RESULTS_FILE, build_report, read_tests


def build_body(report):
    """The readable text of the email."""
    lines = [
        f"Overall result: {report['overall_status'].upper()}",
        f"Tests: {report['total']} total, {report['passed']} passed, {report['failed']} failed",
        "",
        f"Repository: {report['repository']}",
        f"Branch:     {report['branch']}",
        f"Commit:     {report['commit_sha']}",
        f"Run ID:     {report['run_id']}",
        f"Time (UTC): {report['timestamp']}",
        "",
        "Individual results:",
    ]
    for test in report["tests"]:
        mark = "PASS" if test["result"] == "passed" else "FAIL"
        lines.append(f"  [{mark}] {test['name']}")
        if test["failure_message"]:
            lines.append(f"         {test['failure_message'].splitlines()[0]}")
    if report.get("error"):
        lines += ["", f"Problem: {report['error']}"]
    lines += ["", "The full report is attached as testreport.json."]
    return "\n".join(lines)


def build_message(report, sender, recipient):
    """Subject + body + the report attached as testreport.json."""
    status = report["overall_status"].upper()
    message = EmailMessage()
    message["Subject"] = (
        f"[{status}] {report['repository']} - {report['branch']} @ {report['commit_sha'][:7]}"
        f" - {report['passed']}/{report['total']} tests passed"
    )
    message["From"] = sender
    message["To"] = recipient
    message.set_content(build_body(report))
    message.add_attachment(
        json.dumps(report, indent=2).encode("utf-8"),
        maintype="application",
        subtype="json",
        filename="testreport.json",
    )
    return message


def main():
    sender = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "").replace(" ", "")
    recipient = os.environ.get("EMAIL_TO", "")
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))

    if not (sender and password and recipient):
        print("Missing SMTP_USER, SMTP_PASSWORD or EMAIL_TO. Add them as GitHub Secrets.")
        sys.exit(1)

    if os.path.exists(RESULTS_FILE):
        report = build_report(read_tests(RESULTS_FILE))
    else:
        report = build_report([])
        report["error"] = f"{RESULTS_FILE} was not created, so the tests did not run."

    message = build_message(report, sender, recipient)
    try:
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        print(f"Could not send the email: {exc}")
        sys.exit(1)

    print(f"Email sent: {report['overall_status']} "
          f"({report['passed']}/{report['total']} tests passed)")


if __name__ == "__main__":
    main()