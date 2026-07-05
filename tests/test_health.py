"""HANDOFF-01 §5: health & DB connectivity."""


def test_health_returns_healthy(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}


def test_test_db_reports_connected(client):
    resp = client.get("/test-db")
    assert resp.status_code == 200
    assert resp.json() == {"db_connected": True}
