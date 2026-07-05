"""HANDOFF-01 §5: health & DB connectivity."""


async def test_health_returns_healthy(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}


async def test_test_db_reports_connected(client):
    resp = await client.get("/test-db")
    assert resp.status_code == 200
    assert resp.json() == {"db_connected": True}
