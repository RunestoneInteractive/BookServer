# ********************************
# |docname| - test the logging API
# ********************************
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
import datetime

# Third-party imports
# -------------------
from pydantic import ValidationError
import pytest

# Local application imports
# -------------------------
from bookserver.models import UseinfoValidation
from bookserver.applogger import rslogger


# Tests
# =====
def test_main(test_client_app):
    with test_client_app as client:
        response = client.get("/")
        assert response.status_code == 200


def test_add_log(test_client_app):
    item = dict(
        event="page",
        act="view",
        div_id="/runestone/fopp/index.html",
        sid="testuser",
        course_name="fopp",
        timestamp=datetime.datetime.utcnow().isoformat(),
    )
    with test_client_app as client:
        response = client.post(
            "/logger/bookevent",
            headers={"Content-type": "application/json; charset=utf-8"},
            json=item,
        )
        assert response.status_code == 401
        # assert response.json()["result"] == "success"
        rslogger.debug(response.json())


def test_add_mchoice(test_client_app):
    item = dict(
        event="mChoice",
        act="answer:2:correct",
        correct="T",
        div_id="test_mchoice_1",
        sid="testuser",
        course_name="fopp",
        percent="1",
        timestamp=datetime.datetime.utcnow().isoformat(),
    )
    # Create JWT security token
    # add to headers
    with test_client_app as client:
        response = client.post(
            "/logger/bookevent",
            headers={"Content-type": "application/json; charset=utf-8"},
            json=item,
        )
        assert response.status_code == 401
        # assert response.json()["result"] == "success"

    req = dict(
        course="fopp",
        div_id="test_mchoice_1",
        event="mChoice",
        sid="testuser",
    )

    with test_client_app as client:
        response = client.post(
            "/assessment/results",
            headers={"Content-type": "application/json; charset=utf-8"},
            json=req,
        )
    # TODO: get login working and add a test for a logged in user
    assert response.status_code == 401
    # res = response.json()
    # assert res["correct"] is True
    # assert res["div_id"] == "test_mchoice_1"


def test_schema_generator():
    with pytest.raises(ValidationError):
        # The sid Column has a max length of 512. This should fail validation.
        UseinfoValidation(sid="x" * 600, id="5")


def test_secondary_validation_error(test_client_app):
    item = dict(
        event="mChoice",
        act="answer:2:correct",
        correct="T",
        div_id="test_mchoice_1",
        sid="testuser",
        course_name="fopp" * 500,
        percent="1",
        timestamp=datetime.datetime.utcnow().isoformat(),
    )
    # Create JWT security token
    # add to headers
    with test_client_app as client:
        response = client.post(
            "/logger/bookevent",
            headers={"Content-type": "application/json; charset=utf-8"},
            json=item,
        )
        assert response.status_code == 401
