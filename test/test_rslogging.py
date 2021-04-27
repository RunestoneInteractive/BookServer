# ********************************
# |docname| - test the logging API
# ********************************

from fastapi.testclient import TestClient
from bookserver.schemas import LogItemIncoming
from bookserver.main import app
from bookserver.schemas import AssessmentRequest


def test_main():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200


def test_add_log():
    item = LogItemIncoming(
        event="page",
        act="view",
        div_id="/runestone/fopp/index.html",
        sid="testuser",
        course_name="fopp",
    )
    with TestClient(app) as client:
        response = client.post(
            "/logger/bookevent",
            headers={"Content-type": "application/json; charset=utf-8"},
            json=item.dict(),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "OK"


def test_add_mchoice():
    item = LogItemIncoming(
        event="mChoice",
        act="answer:2:correct",
        correct="T",
        div_id="test_mchoice_1",
        sid="testuser",
        course_name="fopp",
        percent=1,
    )
    # Create JWT security token
    # add to headers
    with TestClient(app) as client:
        response = client.post(
            "/logger/bookevent",
            headers={"Content-type": "application/json; charset=utf-8"},
            json=item.dict(),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "OK"

    req = AssessmentRequest(
        course="fopp", div_id="test_mchoice_1", event="mChoice", sid="current_user"
    )

    with TestClient(app) as client:
        response = client.post(
            "/assessment/results",
            headers={"Content-type": "application/json; charset=utf-8"},
            json=req.dict(),
        )
    assert response.status_code == 200
    res = response.json()
    assert res["correct"] == True
    assert res["div_id"] == "test_mchoice_1"
