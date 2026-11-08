"""Automated tests for the submission portal.

Each test gets a fresh, empty submissions file in a temporary folder, so tests
never affect each other or your real data.
"""
import json

import pytest

import app as portal


@pytest.fixture
def client(tmp_path):
    portal.app.config["DATA_FILE"] = str(tmp_path / "submissions.json")
    portal.app.config["TESTING"] = True
    return portal.app.test_client()


VALID_FORM = {
    "name": "Ali Khan",
    "reg_no": "FA22-BCS-001",
    "title": "Lab 3 - Docker",
    "url": "https://github.com/ali/lab3",
}


def test_valid_submission_is_saved_and_listed(client):
    """Complete details + valid URL -> saved and shown in the submission list."""
    response = client.post("/submit", data=VALID_FORM, follow_redirects=True)

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Ali Khan" in page
    assert "FA22-BCS-001" in page
    assert "https://github.com/ali/lab3" in page
    assert len(portal.load_submissions()) == 1


def test_missing_registration_number_is_rejected_with_message(client):
    """Missing registration number -> rejected with a validation message."""
    form = dict(VALID_FORM, reg_no="")
    response = client.post("/submit", data=form)

    assert response.status_code == 400
    assert "Registration number is required." in response.get_data(as_text=True)
    assert portal.load_submissions() == []


def test_invalid_url_is_rejected_and_not_saved(client):
    """Invalid URL -> rejected and nothing is written to the file."""
    form = dict(VALID_FORM, url="not-a-real-url")
    response = client.post("/submit", data=form)

    assert response.status_code == 400
    assert "not a valid" in response.get_data(as_text=True)
    assert portal.load_submissions() == []
