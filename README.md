# Assignment Submission Portal

A small assignment submission portal (Python / Flask) with automated testing on every push.
Every push to GitHub runs the tests, sends the results to a local receiver that saves
`testreport.json`, emails the report, and publishes a demo to GitHub Pages when all tests pass.

## Files

| File | Purpose |
|---|---|
| `app.py` | The portal: form, validation, saved submissions |
| `test_app.py` | Automated tests (pytest) |
| `requirements.txt` | Python dependencies |
| `receiver.py` | Local HTTP receiver that saves the test report as `testreport.json` |
| `send_report.py` | Builds the report from the test results and sends it to the receiver |
| `send_email.py` | Emails the report (bonus) |
| `docs/index.html` | Static demo published to GitHub Pages (bonus) |
| `.github/workflows/ci.yml` | The CI pipeline |

## Setup

Requires Python 3.10 or newer.

```
pip install -r requirements.txt
```

## Run the application

```
python app.py
```

Open http://127.0.0.1:5000. Enter name, registration number, assignment title and a submission URL.
Valid submissions are saved to `submissions.json` and shown in the list. Missing fields or an invalid
URL are rejected with a message and nothing is saved.

## Run the tests

```
python -m pytest -v
```

The tests cover:
1. Complete details and a valid URL: the submission is saved and listed.
2. Missing registration number: rejected with a validation message.
3. Invalid URL: rejected and not saved.

## Start the receiver

```
python receiver.py
```

It listens on http://127.0.0.1:5001 and saves each report it receives to `testreport.json`
in the project folder. A new report replaces the previous one.

## The CI pipeline

The workflow in `.github/workflows/ci.yml` runs on every push.

**Job `test`** runs on a self-hosted runner (my own computer), so `localhost` reaches the receiver:
1. Check out the pushed commit.
2. Install dependencies.
3. Run the tests (`pytest --junitxml=results.xml`). A failed test fails this step and the job.
4. `send_report.py` sends the report (repository, branch, commit SHA, run ID, timestamp, each test's
   result and failure message, totals and overall status) to the receiver. It runs even if the tests failed.
5. `send_email.py` emails the report. It also runs even if the tests failed.

**Job `deploy`** (bonus) publishes `docs/` to GitHub Pages. It runs only on `main` and only if the
`test` job succeeded, so a failing run leaves the previously published version unchanged.

## Self-hosted runner setup (Windows)

1. In the repo go to Settings > Actions > Runners > New self-hosted runner, and choose Windows, x64.
2. Download and extract the runner into a folder outside the project (for example `D:\action-runner`),
   using the commands shown on that page.
3. Register it with the `config.cmd --url ... --token ...` command shown on that page.
4. Start it with `./run.cmd` and leave that window open.

## Running the full workflow

1. Start the runner (`./run.cmd` in the runner folder).
2. Start the receiver (`python receiver.py` in the project folder).
3. Push a commit. Check the Actions tab, then open `testreport.json` to see the received report.

## Bonus: GitHub Pages

Settings > Pages > Source: GitHub Actions. Deployed demo:
https://farqleet-mehdi.github.io/submission-portal/

## Bonus: email report

The report is emailed after every run, passing or failing. Credentials are kept in GitHub Secrets
(Settings > Secrets and variables > Actions):

| Secret | Value |
|---|---|
| `SMTP_USER` | Sender's Gmail address |
| `SMTP_PASSWORD` | A Gmail app password (not the normal password) |
| `EMAIL_TO` | Address that receives the report (change this to change the recipient) |

The email contains the commit, overall result, test counts and each test's result,
with the full report attached as `testreport.json`.