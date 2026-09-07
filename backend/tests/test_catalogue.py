import pytest
from app.catalogue import CatalogueError, normalize_camera


def test_normalizes_gateway_camera_without_url_assumptions():
    camera = normalize_camera({"camera_id": "c-7", "location": {"lat": "23.03", "lon": "72.56"}, "live_status": "online", "streams": {"rtsp_url": "rtsp://example/live/variable"}})
    assert camera.id == "c-7"
    assert camera.status.value == "live"
    assert camera.streams.rtsp == "rtsp://example/live/variable"


def test_rejects_camera_without_coordinates():
    with pytest.raises(CatalogueError):
        normalize_camera({"id": "c-7", "streams": {}})

