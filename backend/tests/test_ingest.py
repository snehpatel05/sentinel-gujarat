from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def test_ingest_rejects_missing_token(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("SENTINEL_INGEST_TOKEN", "test-token")
    with TestClient(app) as client:
        response = client.post(
            "/api/events/ingest",
            json={
                "camera_id": "cam04",
                "entity_id": "cam04:1",
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "source_pts_ms": 1000,
                "confidence": 0.9,
                "location": {"latitude": 23.03, "longitude": 72.56},
            },
        )
    assert response.status_code == 401


def test_ingest_registers_direct_camera_and_saves_event(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("SENTINEL_INGEST_TOKEN", "test-token")
    with TestClient(app) as client:
        response = client.post(
            "/api/events/ingest",
            headers={"X-Sentinel-Ingest-Token": "test-token"},
            json={
                "camera_id": "cam04",
                "entity_id": "cam04:1",
                "entity_type": "car",
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "source_pts_ms": 1000,
                "confidence": 0.9,
                "location": {"latitude": 23.03, "longitude": 72.56},
            },
        )
        cameras = client.get("/api/cameras").json()
    assert response.status_code == 201
    assert response.json()["camera_id"] == "cam04"
    camera = next(camera for camera in cameras if camera["id"] == "cam04")
    assert camera["streams"]["rtsp"] is None