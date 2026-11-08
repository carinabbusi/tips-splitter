from fastapi.testclient import TestClient

from tips_splitter import __version__
from tips_splitter.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}


def test_split_endpoint():
    payload = {
        "entries": [
            {"date": "2026-09-01", "amount": "10.00", "workers": ["Alex", "Bia", "Caio"]},
            {"date": "2026-09-02", "amount": "4.00", "workers": ["Alex", "Bia"]},
        ]
    }
    response = client.post("/split", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["total"] == "14.00"
    assert body["per_person"] == {"Alex": "5.34", "Bia": "5.33", "Caio": "3.33"}
    assert body["days_worked"] == {"Alex": 2, "Bia": 2, "Caio": 1}
    assert len(body["days"]) == 2


def test_split_rejects_negative_amount():
    payload = {"entries": [{"date": "2026-09-01", "amount": "-5", "workers": ["Alex"]}]}
    assert client.post("/split", json=payload).status_code == 422


def test_split_rejects_empty_workers():
    payload = {"entries": [{"date": "2026-09-01", "amount": "5.00", "workers": []}]}
    assert client.post("/split", json=payload).status_code == 422


def test_split_rejects_blank_worker_name():
    payload = {"entries": [{"date": "2026-09-01", "amount": "5.00", "workers": ["  "]}]}
    response = client.post("/split", json=payload)
    assert response.status_code == 422
    assert "empty" in response.json()["detail"]


def test_split_rejects_empty_request():
    assert client.post("/split", json={"entries": []}).status_code == 422
