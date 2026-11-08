"""Assignment submission portal (Flask).

Routes:
    GET  /        show the form and the list of saved submissions
    POST /submit  validate the form; save it if valid, otherwise show errors
"""
import json
import os
from urllib.parse import urlparse

from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)
# Where submissions are stored. Tests point this at a temporary file.
app.config["DATA_FILE"] = os.environ.get("SUBMISSIONS_FILE", "submissions.json")


# ---------- validation ----------

def is_valid_url(url):
    """A URL is valid if it is http(s) and has a real-looking domain."""
    if not url or " " in url:
        return False
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    host = parsed.hostname
    # needs a host with at least one dot, e.g. github.com (rejects "http://x")
    return bool(host) and "." in host and not host.startswith(".") and not host.endswith(".")


def validate_submission(name, reg_no, title, url):
    """Return a list of problems. An empty list means the submission is valid."""
    errors = []
    if not name.strip():
        errors.append("Name is required.")
    if not reg_no.strip():
        errors.append("Registration number is required.")
    if not title.strip():
        errors.append("Assignment title is required.")
    if not url.strip():
        errors.append("Submission URL is required.")
    elif not is_valid_url(url.strip()):
        errors.append("Submission URL is not a valid http(s) URL.")
    return errors


# ---------- storage ----------

def load_submissions():
    path = app.config["DATA_FILE"]
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_submission(submission):
    submissions = load_submissions()
    submissions.append(submission)
    with open(app.config["DATA_FILE"], "w", encoding="utf-8") as f:
        json.dump(submissions, f, indent=2)


# ---------- page ----------

PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Assignment Submission Portal</title>
  <style>
    body { font-family: sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; }
    label { display: block; margin-top: .8rem; font-weight: bold; }
    input { width: 100%; padding: .4rem; box-sizing: border-box; }
    button { margin-top: 1rem; padding: .5rem 1.2rem; }
    .errors { background: #fde8e8; border: 1px solid #e0a0a0; padding: .5rem 1rem; }
    table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
    th, td { border: 1px solid #ccc; padding: .4rem; text-align: left; }
  </style>
</head>
<body>
  <h1>Assignment Submission Portal</h1>

  {% if errors %}
  <div class="errors" id="errors">
    <ul>{% for e in errors %}<li>{{ e }}</li>{% endfor %}</ul>
  </div>
  {% endif %}

  <form method="post" action="/submit">
    <label>Name <input name="name" value="{{ form.get('name', '') }}"></label>
    <label>Registration number <input name="reg_no" value="{{ form.get('reg_no', '') }}"></label>
    <label>Assignment title <input name="title" value="{{ form.get('title', '') }}"></label>
    <label>Submission URL <input name="url" value="{{ form.get('url', '') }}"></label>
    <button type="submit">Submit</button>
  </form>

  <h2>Saved submissions</h2>
  {% if submissions %}
  <table id="submission-list">
    <tr><th>Name</th><th>Reg. no.</th><th>Assignment</th><th>URL</th></tr>
    {% for s in submissions %}
    <tr>
      <td>{{ s.name }}</td><td>{{ s.reg_no }}</td><td>{{ s.title }}</td>
      <td><a href="{{ s.url }}">{{ s.url }}</a></td>
    </tr>
    {% endfor %}
  </table>
  {% else %}
  <p>No submissions yet.</p>
  {% endif %}
</body>
</html>
"""


def render(errors=None, form=None, status=200):
    html = render_template_string(
        PAGE,
        errors=errors or [],
        form=form or {},
        submissions=load_submissions(),
    )
    return html, status


@app.route("/", methods=["GET"])
def index():
    return render()


@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name", "")
    reg_no = request.form.get("reg_no", "")
    title = request.form.get("title", "")
    url = request.form.get("url", "")

    errors = validate_submission(name, reg_no, title, url)
    if errors:
        # Rejected: show the messages, keep what the student typed, save nothing.
        return render(errors=errors, form=request.form, status=400)

    save_submission(
        {"name": name.strip(), "reg_no": reg_no.strip(), "title": title.strip(), "url": url.strip()}
    )
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
